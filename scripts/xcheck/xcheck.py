#!/usr/bin/env python3
"""Cross-check belt balancer blueprint books with a THIRD-PARTY verifier.

Engine: tzwaan/factorio_balancers (https://github.com/tzwaan/factorio_balancers), cloned unmodified in
./factorio_balancers; deps in ./venv (py_factorio_blueprints, progress). Run with any python3: the script
re-executes itself under ./venv.

usage: python3 xcheck.py <blueprint-book-file.txt> [regex-filter-on-label] [options]

One line per blueprint: STATUS, label, detected inputs x outputs, then
  out_bal / in_bal / tp_full : the tool's test protocol (each single input and all inputs fed -> outputs equal;
                               each single output and all outputs open -> inputs drawn equally; all in/all out
                               -> full throughput), simulated by the tool's engine, compared with a tolerance.
  native=out/in/tp           : the tool's own verdict as-is. It compares exact Fractions after stopping at a
                               1e-6 convergence, so balancers with feedback loops get false 'NO's. Informational.
  tu_1-2 (--sweep)           : tool's native throughput-unlimited candidate sweep (any 1 or 2 inputs -> any 1 or 2
                               outputs).
  partial (--partial K)      : extra partial-use balance checks through the tool's simulation primitives: every
                               subset of <=K inputs fed / every subset of <=K outputs open (rest blocked), plus
                               the n-1 subsets. K >= max(n, m) is exhaustive.
STATUS: PASS / FAIL / ERROR (tool rejected or crashed) / UNSUPPORTED (non-belt entities, no splitter, or
sideloading, where the tool switches to a per-lane model). Label dimensions 'N to M' / 'N-M' must match.

What this wrapper adds around the unmodified third-party engine:
  * Factorio 2.0 -> 1.1 blueprint conversion (16-way directions -> 8-way, unknown keys dropped, turbo->express).
  * Splitter outputs that are blocked in the real game are treated as blocked (flag B) instead of being
    rejected / mis-parsed by the tool: splitter with a 'filter' set (Raynquist's deconstruction-planner
    trick; the output_priority side passes nothing), output facing the side of another splitter, output
    facing the back of an underground exit.
  * Splitters that no input can reach are reported (flag D, warning) instead of crashing the tool.
  * O(1) tile lookup (the library scans all entities per lookup; 7000-entity blueprints took forever).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENV_PY = os.path.join(HERE, 'venv', 'bin', 'python')
if os.path.exists(VENV_PY) and os.path.realpath(sys.prefix) != os.path.realpath(os.path.join(HERE, 'venv')):
    os.execv(VENV_PY, [VENV_PY, os.path.abspath(__file__)] + sys.argv[1:])

import argparse
import base64
import json
import logging
import math
import multiprocessing
import re
import signal
import time
import traceback
import zlib
from itertools import combinations

sys.path.insert(0, os.path.join(HERE, 'factorio_balancers'))
sys.setrecursionlimit(1000000)

from py_factorio_blueprints import Blueprint  # noqa: E402
from py_factorio_blueprints.util import Vector  # noqa: E402
from factorio_balancers import Balancer  # noqa: E402
from factorio_balancers import entity_mixins as em  # noqa: E402
from factorio_balancers.exceptions import IllegalConfiguration  # noqa: E402

logging.getLogger('factorio_balancers').setLevel(logging.CRITICAL)

BELT_RE = re.compile(r'^(|fast-|express-|turbo-)(transport-belt|underground-belt|splitter)$')
KEEP = ('entity_number', 'name', 'position', 'type', 'input_priority', 'output_priority')
TOL = 1e-6


# ----------------------------------------------------------------------------- blueprint helpers
def decode(s):
    s = s.strip()
    return json.loads(zlib.decompress(base64.b64decode(s[1:])))


def walk(o, path=()):
    for k in ('blueprint_book', 'blueprint'):
        if k in o:
            b = o[k]
            if k == 'blueprint':
                yield path + (b.get('label') or '',), b
            else:
                for c in b.get('blueprints', []):
                    yield from walk(c, path + (b.get('label') or '',))


def convert(b):
    """Factorio 2.0 blueprint dict -> 1.1-style dict understood by py_factorio_blueprints."""
    ents, blocked = [], 0
    for e in b.get('entities', []):
        n = {k: e[k] for k in KEEP if k in e}
        d = e.get('direction', 0)
        if d % 4:
            raise ValueError('diagonal direction %r on %s' % (d, e['name']))
        n['direction'] = d // 2
        if n['name'].startswith('turbo-'):
            n['name'] = 'express-' + n['name'][len('turbo-'):]
        if 'filter' in e and e['name'].endswith('splitter'):
            # filtered item never shows up on a balancer -> the priority side outputs nothing
            n['xcheck_blocked'] = e.get('output_priority', 'left')
            n.pop('output_priority', None)
            blocked += 1
        ents.append(n)
    return {'blueprint': {'item': 'blueprint', 'label': b.get('label'), 'entities': ents, 'version': 0}}, blocked


# ----------------------------------------------------------------------------- engine patches
class XSplitter(em.Splitter):
    """Same as the tool's Splitter, but in-game-blocked outputs are dead ends, not errors."""

    def __init__(self, *args, xcheck_blocked=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.xcheck_blocked = xcheck_blocked
        self.xcheck_dead = set()

    def setup_transport_lines(self):
        positions = [c + self.direction.vector for c in self.coordinates]
        live = 0
        for side, position in zip(('left', 'right'), positions):
            if side == self.xcheck_blocked:
                self.xcheck_dead.add(side)
                continue
            other = self.blueprint.entities[position]
            if not other:
                live += 1  # open end = balancer output
                continue
            if len(other) > 1:
                raise IllegalConfiguration(self, other, message="More than one entity occupying the same space")
            other = other[0]
            if isinstance(other, em.Splitter) and other.direction != self.direction:
                self.xcheck_dead.add(side)  # facing the side/front of a splitter: blocked in game
                continue
            if isinstance(other, em.Underground) and other.type == 'output' and other.direction == self.direction:
                self.xcheck_dead.add(side)  # facing the back (tunnel half) of an underground exit: blocked
                continue
            if other.direction == self.direction.rotate(2):
                if isinstance(other, em.Underground) and other.type == 'input':
                    self.xcheck_dead.add(side)
                    continue
                raise IllegalConfiguration(self, other, message="Entities facing each other")
            live += 1
            self.get_connection_for(position, em.Connection.Type.OUTPUT).connect(
                other.get_connection_for(position, em.Connection.Type.INPUT))
        if not live:
            raise IllegalConfiguration(self, message="Splitter is unable to output")

    def pad_connection(self, inp=False, out=False):
        if inp or not self.xcheck_dead:
            return super().pad_connection(inp=inp, out=out)
        name = {1: 'transport-belt', 2: 'fast-transport-belt', 3: 'express-transport-belt'}[
            self.name.data['belt_speed']]
        for side, coord in zip(('left', 'right'), self.coordinates):
            if side in self.xcheck_dead:
                continue
            new = self.blueprint.entities.make(
                name=name, position=coord + self.direction.vector, direction=self.direction)
            getattr(self, 'forward_' + side).connect(new.backward)


_belt_setup = em.Belt.setup_transport_lines


def _belt_setup_checked(self):
    other = self.blueprint.entities[self.position + self.direction.vector]
    if len(other) == 1 and isinstance(other[0], em.Underground) and other[0].type == 'output' \
            and other[0].direction == self.direction and not isinstance(self, em.Underground):
        raise IllegalConfiguration(self, other[0], message="Belt dead-ends into the back of an underground exit")
    return _belt_setup(self)


em.Belt.setup_transport_lines = _belt_setup_checked


em.entity_prototypes['splitter']['mixins'] = [XSplitter]


# O(1) tile lookup instead of the library's O(n) scan (same results: candidates are re-checked with collides())
_BL = type(Blueprint().entities)
_orig_getitem, _orig_add, _orig_remove = _BL.__getitem__, _BL.add, _BL.remove


def _fast_getitem(self, vector):
    if type(vector) is tuple:
        vector = Vector(vector)
    idx = self.__dict__.get('_xcheck_idx')
    if idx is None or self.__dict__.get('_xcheck_n') != len(self.objs):
        idx = {}
        for obj in self.objs:
            if not hasattr(obj, 'coordinates'):
                return _orig_getitem(self, vector)
            for c in obj.coordinates:
                idx.setdefault((math.floor(c.x), math.floor(c.y)), []).append(obj)
        self._xcheck_idx, self._xcheck_n = idx, len(self.objs)
    return [o for o in idx.get((math.floor(vector.x), math.floor(vector.y)), ()) if o.collides(vector.copy())]


def _add(self, obj):
    self.__dict__.pop('_xcheck_idx', None)
    return _orig_add(self, obj)


def _remove(self, obj):
    self.__dict__.pop('_xcheck_idx', None)
    return _orig_remove(self, obj)


_BL.__getitem__, _BL.add, _BL.remove = _fast_getitem, _add, _remove


class XBalancer(Balancer):
    """Tool's Balancer, but splitters unreachable from every input are recorded instead of crashing the
    parser with AttributeError('_traversed') (the tool's own 'not fully connected' check is buggy)."""

    def generate_simulation(self):
        self.xcheck_unreachable = []
        try:
            super().generate_simulation()
        except AttributeError as ex:
            if '_traversed' not in str(ex):
                raise
        if not self.has_sideloads:
            self.xcheck_unreachable = [e for e in self._get_nodes() if not getattr(e, '_traversed', False)]


def patch_speed(uniform):
    if not uniform:
        return
    orig = Blueprint.import_prototype_data.__func__

    def patched(cls, filename, **kw):
        orig(cls, filename, **kw)
        for v in cls.entity_prototypes.values():
            if 'belt_speed' in v:
                v['belt_speed'] = 3
    Blueprint.import_prototype_data = classmethod(patched)


# ----------------------------------------------------------------------------- extended checks
def _run(bal, ins, outs, fill, max_cycles=200000):
    """Drive the tool's simulation to steady state. Feed only `ins`, drain only `outs`."""
    if fill:
        bal.fill()
    else:
        bal.clear()
    prev, stable = None, 0
    for _ in range(max_cycles):
        drained = [float(b.clear()) for b in outs]
        bal.cycle()
        supplied = [float(b.supply()) for b in ins]
        cur = drained + supplied
        if prev is not None and max(abs(a - b) for a, b in zip(cur, prev)) < 1e-10 \
                and abs(sum(drained) - sum(supplied)) <= 1e-7 * max(1.0, sum(supplied)):
            stable += 1
            if stable >= 3:
                return drained, supplied
        else:
            stable = 0
        prev = cur
    raise RuntimeError('no steady state after %d cycles' % max_cycles)


def _spread(v):
    return (max(v) - min(v)) if v else 0.0


def subsets(items, k):
    n = len(items)
    sizes = sorted(set(range(1, min(k, n) + 1)) | ({n - 1} if n > 1 else set()) | {n})
    for s in sizes:
        yield from combinations(range(n), s)


def std_checks(bal):
    """The tool's own test protocol (each single input / all inputs; each single output / all outputs;
    full-load throughput) but compared with a tolerance. The native code compares exact Fractions after
    stopping at a 1e-6 convergence, which reports every balancer containing a feedback loop as unbalanced."""
    ins, outs = bal._input_belts, bal._output_belts
    notes = []
    out_ok = in_ok = True
    for sub in [(i,) for i in range(len(ins))] + [tuple(range(len(ins)))]:
        drained, supplied = _run(bal, [ins[i] for i in sub], outs, fill=False)
        if _spread(drained) > TOL * 3:
            out_ok = False
            notes.append('out-unbalanced feeding inputs %s: %s' % (list(sub), ['%.4f' % d for d in drained]))
    full_d, full_s = drained, supplied
    cap = min(sum(float(b.capacity) for b in ins), sum(float(b.capacity) for b in outs))
    tp = sum(full_d) / cap
    for sub in [(i,) for i in range(len(outs))] + [tuple(range(len(outs)))]:
        _, supplied = _run(bal, ins, [outs[i] for i in sub], fill=True)
        if _spread(supplied) > TOL * 3:
            in_ok = False
            notes.append('in-unbalanced with only outputs %s open: %s' % (list(sub), ['%.4f' % d for d in supplied]))
    return out_ok, in_ok, tp, notes


def partial_checks(bal, k):
    """Returns list of failure strings (empty = ok)."""
    fails = []
    ins, outs = bal._input_belts, bal._output_belts
    for sub in subsets(ins, k):
        drained, _ = _run(bal, [ins[i] for i in sub], outs, fill=False)
        if _spread(drained) > TOL * 3:
            fails.append('out-unbalanced feeding inputs %s: %s' % (list(sub), ['%.4f' % d for d in drained]))
    for sub in subsets(outs, k):
        _, supplied = _run(bal, ins, [outs[i] for i in sub], fill=True)
        if _spread(supplied) > TOL * 3:
            fails.append('in-unbalanced with only outputs %s open: %s' % (list(sub), ['%.4f' % d for d in supplied]))
    return fails


# ----------------------------------------------------------------------------- per-blueprint job
class Timeout(Exception):
    pass


def _alarm(*_):
    raise Timeout()


def fmt_exc(ex):
    msg = getattr(ex, 'message', '') or ''
    parts = []
    for a in getattr(ex, 'args', ()):
        if isinstance(a, Exception):
            parts.append(fmt_exc(a))
        elif isinstance(a, (list, tuple)):
            parts.append('[' + ', '.join('%s@%s' % (getattr(x, 'name', x), getattr(x, 'position', '')) for x in a) + ']')
        elif hasattr(a, 'position'):
            parts.append('%s@%s' % (a.name, a.position))
        else:
            parts.append(str(a))
    return ('%s: %s %s' % (type(ex).__name__, msg, '; '.join(parts))).strip()


def check(job):
    idx, path, b, opt = job
    label = path[-1]
    r = {'idx': idx, 'path': path, 'label': label, 'n_ent': len(b.get('entities', [])), 'status': 'ERROR',
         'flags': '', 'detail': '', 'dims': None, 'time': 0.0}
    t0 = time.time()
    patch_speed(opt['uniform_speed'])
    names = {e['name'] for e in b.get('entities', [])}
    other = sorted(n for n in names if not BELT_RE.match(n))
    if other:
        r.update(status='UNSUPPORTED', detail='non-belt entities: %s' % ', '.join(other))
        return r
    if not any(n.endswith('splitter') for n in names):
        r.update(status='UNSUPPORTED', detail='no splitter in blueprint (tool needs at least one node)')
        return r
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(opt['timeout'])
    try:
        data, nfilter = convert(b)
        bal = XBalancer(data=data)
        dead = sum(len(getattr(e, 'xcheck_dead', ())) for e in bal.entities)
        r['dims'] = (bal.nr_inputs, bal.nr_outputs)
        if bal.has_sideloads:
            r['flags'] += 'L'
        if dead:
            r['flags'] += 'B'
        if len({BELT_RE.match(n).group(1) for n in names}) > 1:
            r['flags'] += 'M'
        if any('input_priority' in e or ('output_priority' in e and 'filter' not in e) for e in b['entities']):
            r['flags'] += 'P'
        props = ['balance.output', 'balance.input', 'throughput.full']
        if opt['sweep']:
            props.append('throughput.unlimited.candidate')
        res = bal.test(properties=props)
        r['native'] = (res['balance.output']['result'], res['balance.input']['result'],
                       res['throughput.full']['result'])
        if opt['sweep']:
            r['tu'] = res['throughput.unlimited.candidate']['result']
            r['tu_msg'] = res['throughput.unlimited.candidate'].get('message')
        r['out'], r['in'], r['tp'], r['notes'] = std_checks(bal)
        r['partial'] = partial_checks(bal, opt['partial']) if opt['partial'] else None
        ok = r['out'] and r['in'] and r['tp'] > 1 - 1e-5 and not r['partial']
        m = re.search(r'(\d+)\s*(?:to|-|x)\s*(\d+)', label)
        if m and (int(m.group(1)), int(m.group(2))) != r['dims']:
            ok = False
            r['detail'] = 'label says %sx%s' % m.groups()
        if bal.xcheck_unreachable:
            r['flags'] += 'D'
            r['detail'] += ' %d splitter(s) can never receive items (no path from any input), at %s' % (
                len(bal.xcheck_unreachable),
                ' '.join('(%g,%g)' % (e.position.x, e.position.y) for e in bal.xcheck_unreachable[:8]))
        r['status'] = 'PASS' if ok else 'FAIL'
        if bal.has_sideloads:
            r['status'] = 'UNSUPPORTED'
            r['detail'] = ('sideloading -> tool switches to per-lane mode (%d lane inputs x %d lane outputs); '
                           'verdict shown is per lane, informational only. ' % (
                               bal.nr_inputs_sim, bal.nr_outputs_sim)) + r['detail']
    except Timeout:
        r.update(status='ERROR', detail='timeout after %ds' % opt['timeout'])
    except Exception as ex:  # tool rejected / crashed on the blueprint
        tb = traceback.extract_tb(ex.__traceback__)[-1]
        r.update(status='ERROR', detail=('%s [at %s:%d `%s`]' % (
            fmt_exc(ex), os.path.basename(tb.filename), tb.lineno, tb.line))[:400])
    finally:
        signal.alarm(0)
    r['time'] = time.time() - t0
    return r


def yn(v):
    return {True: 'yes', False: 'NO', None: '-'}[v]


def line(r, full_path):
    name = ' / '.join(r['path'][1:]) if full_path else r['label']
    dims = '%dx%d' % r['dims'] if r['dims'] else '?x?'
    s = '%-11s %-34s %-7s' % (r['status'], name[:60], dims)
    if 'out' in r:
        s += ' out_bal=%-3s in_bal=%-3s tp_full=%-3s' % (yn(r['out']), yn(r['in']), yn(r['tp'] > 1 - 1e-5))
        if r['tp'] <= 1 - 1e-5:
            s += ' (%.2f%% of max)' % (100 * r['tp'])
        s += ' native=%s/%s/%s' % tuple(yn(v) for v in r['native'])
        if 'tu' in r:
            s += ' tu_1-2=%-3s' % yn(r['tu'])
            if not r['tu'] and r.get('tu_msg') is not None:
                s += ' (%.1f%%)' % float(r['tu_msg'])
        if r.get('partial') is not None:
            s += ' partial=%s' % ('ok' if not r['partial'] else 'FAIL(%d)' % len(r['partial']))
    s += ' ent=%d %.1fs' % (r['n_ent'], r['time'])
    if r['flags']:
        s += ' [%s]' % r['flags']
    if r['detail']:
        s += ' ' + r['detail']
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('book')
    ap.add_argument('regex', nargs='?', default=None, help='regex filter applied to the blueprint label')
    ap.add_argument('--partial', type=int, default=0, metavar='K',
                    help='extra partial-use balance checks over all subsets of size <=K (and size n-1)')
    ap.add_argument('--sweep', action='store_true', help="tool's native TU candidate sweep (1 or 2 belts in/out)")
    ap.add_argument('--timeout', type=int, default=600, help='seconds per blueprint (default 600)')
    ap.add_argument('--uniform-speed', action='store_true', help='treat every belt tier as the same speed')
    ap.add_argument('--skip', default=r'^FAQ$', help="regex on parent book labels to skip (default '^FAQ$')")
    ap.add_argument('-j', '--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument('-v', '--verbose', action='store_true', help='print partial-check failure details')
    a = ap.parse_args()

    book = decode(open(a.book).read())
    rx = re.compile(a.regex) if a.regex else None
    skip = re.compile(a.skip) if a.skip else None
    opt = {'partial': a.partial, 'sweep': a.sweep, 'timeout': a.timeout, 'uniform_speed': a.uniform_speed}
    jobs, skipped = [], 0
    for i, (path, b) in enumerate(walk(book)):
        if rx and not rx.search(path[-1]):
            continue
        if skip and any(skip.search(p) for p in path[:-1]):
            skipped += 1
            continue
        jobs.append((i, path, b, opt))
    full_path = len({j[1][-1] for j in jobs}) != len(jobs) or any(len(j[1]) > 2 for j in jobs)

    counts = {}
    t0 = time.time()
    print('columns: out_bal/in_bal/tp_full = tool engine + tolerance compare; native = tool verdict as-is (out/in/tp, exact Fraction compare)')
    print('legend: L=lane/sideload mode  B=blocked splitter output emulated  M=mixed belt tiers  P=priority splitters  D=dead splitters (warning only)')
    with multiprocessing.Pool(a.jobs) as pool:
        for r in pool.imap(check, jobs):
            counts[r['status']] = counts.get(r['status'], 0) + 1
            if r['status'] == 'PASS' and 'D' in r['flags']:
                counts['warn'] = counts.get('warn', 0) + 1
            print(line(r, full_path), flush=True)
            notes = (r.get('notes') or []) + (r.get('partial') or [])
            if a.verbose and notes:
                for f in notes[:12]:
                    print('      ' + f)
                if len(notes) > 12:
                    print('      ... %d more' % (len(notes) - 12))
    print('-' * 100)
    print('SUMMARY: %d checked: pass=%d (of which %d with dead-splitter warning) fail=%d error=%d unsupported=%d (skipped by --skip: %d) in %.1fs' % (
        len(jobs), counts.get('PASS', 0), counts.get('warn', 0), counts.get('FAIL', 0), counts.get('ERROR', 0),
        counts.get('UNSUPPORTED', 0), skipped, time.time() - t0))
    return 1 if counts.get('FAIL') or counts.get('ERROR') else 0


if __name__ == '__main__':
    sys.exit(main())
