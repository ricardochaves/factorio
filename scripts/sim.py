"""Belt-balancer analysis: blueprint -> splitter graph -> fluid simulation with back-pressure.

Graph model
-----------
nodes: ('src', i) | ('snk', j) | ('spl', k) | ('mrg', k)
edges: dict with 'u' (node, out-slot), 'v' (node, in-slot), 'cap'
Splitter slots: 0 = left, 1 = right (relative to travel direction).
"""
import random

DIRS = {0: (0, -1), 4: (1, 0), 8: (0, 1), 12: (-1, 0)}
UG_DIST = {'underground-belt': 5, 'fast-underground-belt': 7,
           'express-underground-belt': 9, 'turbo-underground-belt': 11}


def opposite(d):
    return (d + 8) % 16


class Graph:
    def __init__(self):
        self.n_src = 0
        self.n_snk = 0
        self.splitters = []   # dict(in_prio=None|0|1, out_prio=None|0|1)
        self.merges = []      # dict(n_in=k)
        self.edges = []       # dict(u=(node,slot), v=(node,slot), cap=float)
        self.warnings = []
        self.src_pos = []
        self.snk_pos = []

    def add_src(self, pos=None):
        self.n_src += 1; self.src_pos.append(pos); return ('src', self.n_src - 1)

    def add_snk(self, pos=None):
        self.n_snk += 1; self.snk_pos.append(pos); return ('snk', self.n_snk - 1)

    def add_spl(self, in_prio=None, out_prio=None):
        self.splitters.append(dict(in_prio=in_prio, out_prio=out_prio))
        return ('spl', len(self.splitters) - 1)

    def add_edge(self, u, us, v, vs, cap=1.0, tiles=None):
        self.edges.append(dict(u=(u, us), v=(v, vs), cap=cap, tiles=tiles or []))


# ----------------------------------------------------------------------------
# Blueprint -> graph
# ----------------------------------------------------------------------------

def parse_blueprint(b):
    """Return Graph for a blueprint dict (the value under 'blueprint')."""
    tiles = {}  # (x,y) -> dict(kind, dir, name, ent, half)
    splitters = []
    for e in b.get('entities', []):
        name = e['name']
        d = e.get('direction', 0)
        x, y = e['position']['x'], e['position']['y']
        if name.endswith('transport-belt'):
            tiles[(int(x - 0.5), int(y - 0.5))] = dict(kind='belt', dir=d, name=name, ent=e)
        elif name.endswith('underground-belt'):
            k = 'ug_in' if e.get('type', 'input') == 'input' else 'ug_out'
            tiles[(int(x - 0.5), int(y - 0.5))] = dict(kind=k, dir=d, name=name, ent=e)
        elif name.endswith('splitter'):
            # two tiles; left/right relative to direction
            if d in (0, 8):
                t1 = (int(round(x - 1)), int(y - 0.5)); t2 = (int(round(x)), int(y - 0.5))
                left, right = (t1, t2) if d == 0 else (t2, t1)
            else:
                t1 = (int(x - 0.5), int(round(y - 1))); t2 = (int(x - 0.5), int(round(y)))
                left, right = (t1, t2) if d == 4 else (t2, t1)
            idx = len(splitters)
            splitters.append(e)
            tiles[left] = dict(kind='spl', dir=d, name=name, ent=e, spl=idx, half=0)
            tiles[right] = dict(kind='spl', dir=d, name=name, ent=e, spl=idx, half=1)
        else:
            raise ValueError('unexpected entity ' + name)

    g = Graph()
    # underground pairing
    ug_pair = {}
    for t, r in tiles.items():
        if r['kind'] != 'ug_in':
            continue
        dx, dy = DIRS[r['dir']]
        for k in range(1, UG_DIST[r['name']] + 1):
            o = tiles.get((t[0] + dx * k, t[1] + dy * k))
            if o and o['name'] == r['name'] and o['kind'] in ('ug_in', 'ug_out'):
                if o['dir'] == r['dir']:
                    if o['kind'] == 'ug_out':
                        ug_pair[t] = (t[0] + dx * k, t[1] + dy * k)
                    break
                if o['dir'] == opposite(r['dir']) and o['kind'] == 'ug_out':
                    # an output facing us: it belongs to an opposite tunnel; does not block
                    continue
        if t not in ug_pair:
            g.warnings.append('unpaired underground input at %s' % (t,))

    paired_outs = set(ug_pair.values())
    for t, r in tiles.items():
        if r['kind'] == 'ug_out' and t not in paired_outs:
            g.warnings.append('unpaired underground output at %s' % (t,))

    def next_tile(t):
        """Tile that the entity on tile t pushes items into (or None)."""
        r = tiles[t]
        if r['kind'] == 'ug_in':
            return ug_pair.get(t)
        dx, dy = DIRS[r['dir']]
        return (t[0] + dx, t[1] + dy)

    def accepts(src, dst):
        """How dst tile accepts items from src tile: 'full' | 'side' | None."""
        s, d = tiles[src], tiles.get(dst)
        if d is None:
            return None
        if s['kind'] == 'ug_in':
            return 'full' if ug_pair.get(src) == dst else None
        sd, dd = s['dir'], d['dir']
        if d['kind'] == 'belt':
            if sd == opposite(dd):
                return None
            return 'back' if sd == dd else 'perp'
        if d['kind'] == 'ug_in':
            if sd == dd:
                return 'back'
            if sd == opposite(dd):
                return None
            return 'side'
        if d['kind'] == 'ug_out':
            if sd == dd or sd == opposite(dd):
                return None
            return 'side'
        if d['kind'] == 'spl':
            return 'back' if sd == dd else None
        return None

    def blocked(t):
        """Splitter half whose output is disabled with the filter trick."""
        r = tiles[t]
        if r['kind'] != 'spl' or not r['ent'].get('filter'):
            return False
        return {'left': 0, 'right': 1}.get(r['ent'].get('output_priority')) == r['half']

    # NOTE (verified in game): the shape of a belt is purely geometric. An entity facing into the back of
    # a belt keeps it straight even if it never delivers an item (filter-blocked splitter half), and then
    # anything entering from the side is a sideload limited to one lane. So blocked halves stay in the
    # feeder list; they simply carry no flow.
    feeders = {t: [] for t in tiles}
    for t in tiles:
        n = next_tile(t)
        if n is None or n not in tiles:
            continue
        a = accepts(t, n)
        if a:
            feeders[n].append((t, a))
    # resolve perp -> curve or sideload, using the full geometry (blocked halves included) ...
    feed_mode = {}
    for t, fl in feeders.items():
        has_back = any(a in ('back', 'full') for _, a in fl)
        perps = [s for s, a in fl if a == 'perp']
        for s, a in fl:
            if a == 'perp':
                a = 'side' if (has_back or len(perps) > 1) else 'back'
            feed_mode[(s, t)] = a
    # ... then forget the feeders that never deliver anything
    for t in feeders:
        feeders[t] = [(s, a) for s, a in feeders[t] if not blocked(s)]

    # nodes
    g.spl_ents = splitters
    spl_nodes = []
    for e in splitters:
        pr = {'left': 0, 'right': 1}
        ip = pr.get(e.get('input_priority'))
        op = pr.get(e.get('output_priority'))
        node = g.add_spl(ip, op)
        g.splitters[-1]['filter'] = e.get('filter')
        spl_nodes.append(node)
    merge_nodes = {}
    for t, fl in feeders.items():
        if tiles[t]['kind'] != 'spl' and len(fl) > 1:
            g.merges.append(dict(n_in=len(fl), tile=t))
            merge_nodes[t] = ('mrg', len(g.merges) - 1)
            g.warnings.append('sideload/merge at %s' % (t,))
        elif tiles[t]['kind'] != 'spl' and len(fl) == 1 and feed_mode[(fl[0][0], t)] == 'side':
            g.warnings.append('single sideload at %s' % (t,))

    def trace(start_tile, u, us, cap=1.0):
        """Follow the path starting at start_tile (already known to accept), create edge."""
        t = start_tile
        prev = None
        seen = set()
        path = []
        while True:
            if t in seen:
                g.warnings.append('belt cycle without splitter at %s' % (t,)); return
            seen.add(t)
            r = tiles[t]
            if r['kind'] == 'spl':
                g.add_edge(u, us, spl_nodes[r['spl']], r['half'], cap, path); return
            if t in merge_nodes and prev is not None:
                slot = [s for s, _ in feeders[t]].index(prev)
                mode = feed_mode[(prev, t)]
                g.add_edge(u, us, merge_nodes[t], slot, 0.5 if mode == 'side' else cap, path); return
            path.append(t)
            n = next_tile(t)
            if n is None or n not in tiles or not accepts(t, n):
                if r['kind'] == 'ug_in':
                    return  # dead underground
                snk = g.add_snk(t)
                g.add_edge(u, us, snk, 0, cap, path); return
            if feed_mode.get((t, n)) == 'side' and n not in merge_nodes:
                cap = min(cap, 0.5)
            prev, t = t, n

    # sources: tiles with no feeders that are belts / ug_in
    for t in sorted(tiles, key=lambda p: (p[0], p[1])):
        r = tiles[t]
        if r['kind'] in ('belt', 'ug_in') and not feeders[t]:
            src = g.add_src(t)
            trace(t, src, 0)
    # splitter outputs
    for t, r in tiles.items():
        if r['kind'] != 'spl':
            continue
        e = r['ent']
        flt = e.get('filter')
        if flt:
            # filtered side only passes the filter item: treat as blocked when the
            # filter is the deconstruction planner trick
            side = {'left': 0, 'right': 1}.get(e.get('output_priority'))
            if side == r['half']:
                continue
        n = next_tile(t)
        if n in tiles and accepts(t, n):
            trace_from_spl(g, tiles, t, n, spl_nodes[r['spl']], r['half'], trace, merge_nodes, feeders, feed_mode)
    # merge outputs
    for t, node in merge_nodes.items():
        n = next_tile(t)
        if n is not None and n in tiles and accepts(t, n):
            _start(g, t, n, node, 0, tiles, merge_nodes, feeders, feed_mode, trace)
        else:
            snk = g.add_snk(t)
            g.add_edge(node, 0, snk, 0, 1.0)
    return g


def _start(g, t, n, node, slot, tiles, merge_nodes, feeders, feed_mode, trace):
    if n in merge_nodes:
        s = [x for x, _ in feeders[n]].index(t)
        mode = feed_mode[(t, n)]
        g.add_edge(node, slot, merge_nodes[n], s, 0.5 if mode == 'side' else 1.0)
    else:
        trace(n, node, slot, 0.5 if feed_mode.get((t, n)) == 'side' else 1.0)


def trace_from_spl(g, tiles, t, n, node, slot, trace, merge_nodes, feeders, feed_mode):
    _start(g, t, n, node, slot, tiles, merge_nodes, feeders, feed_mode, trace)


# ----------------------------------------------------------------------------
# Fluid simulation
# ----------------------------------------------------------------------------

class Sim:
    def __init__(self, g):
        self.g = g
        E = g.edges
        self.ne = len(E)
        self.cap = [e['cap'] for e in E]
        ns = len(g.splitters)
        self.spl_in = [[None, None] for _ in range(ns)]
        self.spl_out = [[None, None] for _ in range(ns)]
        self.mrg_in = [[] for _ in g.merges]
        self.mrg_out = [None for _ in g.merges]
        self.src_e = [None] * g.n_src
        self.snk_e = [None] * g.n_snk
        for i, e in enumerate(E):
            (u, us), (v, vs) = e['u'], e['v']
            if u[0] == 'spl': self.spl_out[u[1]][us] = i
            elif u[0] == 'mrg': self.mrg_out[u[1]] = i
            else: self.src_e[u[1]] = i
            if v[0] == 'spl': self.spl_in[v[1]][vs] = i
            elif v[0] == 'mrg': self.mrg_in[v[1]].append(i)
            else: self.snk_e[v[1]] = i

    def _c_setup(self):
        import ctypes, os
        lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csim.so'))
        lib.run.restype = ctypes.c_int
        g = self.g
        IA = lambda v: (ctypes.c_int * max(1, len(v)))(*v)
        n1 = lambda v: -1 if v is None else v
        self._lib = lib
        self._cap = (ctypes.c_double * max(1, self.ne))(*self.cap)
        self._sin = IA([n1(x) for p in self.spl_in for x in p])
        self._sout = IA([n1(x) for p in self.spl_out for x in p])
        self._ip = IA([n1(sp['in_prio']) for sp in g.splitters])
        self._op = IA([n1(sp['out_prio']) for sp in g.splitters])
        ms = [0]; mi = []
        for ins in self.mrg_in:
            mi += ins; ms.append(len(mi))
        self._ms = IA(ms); self._mi = IA(mi); self._mo = IA([n1(x) for x in self.mrg_out])
        self._ct = ctypes

    def run(self, supply, demand, tol=1e-11, max_iter=200000):
        if not hasattr(self, '_lib'):
            self._c_setup()
        ct = self._ct; cap = self.cap
        s = [0.0] * self.ne; d = list(cap)
        for i, e in enumerate(self.src_e):
            if e is not None: s[e] = min(cap[e], supply[i])
        for j, e in enumerate(self.snk_e):
            if e is not None: d[e] = min(cap[e], demand[j])
        S = (ct.c_double * max(1, self.ne))(*s); D = (ct.c_double * max(1, self.ne))(*d)
        it = self._lib.run(self.ne, self._cap, len(self.g.splitters), self._sin, self._sout, self._ip, self._op,
                           len(self.g.merges), self._ms, self._mi, self._mo, S, D, ct.c_double(tol), max_iter)
        f = [min(S[i], D[i]) for i in range(self.ne)]
        fin = [f[e] if e is not None else 0.0 for e in self.src_e]
        fout = [f[e] if e is not None else 0.0 for e in self.snk_e]
        self.last_flows = f
        return fin, fout, it

    # ---- dynamic (time-stepped) model -----------------------------------------------------
    def dyn_setup(self):
        import ctypes, os
        self._dlib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csim_dyn.so'))
        self._dlib.run_dyn.restype = None
        if not hasattr(self, '_lib'):
            self._c_setup()
        ct = self._ct
        caps = []
        for e in self.g.edges:
            ts = e.get('tiles') or []
            length = len(ts)
            for a, b in zip(ts, ts[1:]):
                length += max(0, abs(a[0] - b[0]) + abs(a[1] - b[1]) - 1)
            caps.append(8.0 * length * e['cap'] + 4.0)
        self._dcap = (ct.c_double * max(1, self.ne))(*caps)
        self._drf = (ct.c_double * max(1, self.ne))(*[e['cap'] for e in self.g.edges])
        n1 = lambda v: -1 if v is None else v
        self._srce = (ct.c_int * max(1, len(self.src_e)))(*[n1(x) for x in self.src_e])
        self._snke = (ct.c_int * max(1, len(self.snk_e)))(*[n1(x) for x in self.snk_e])
        self.q = (ct.c_double * max(1, self.ne))()

    def dyn_reset(self):
        for i in range(self.ne): self.q[i] = 0.0

    def dyn(self, supply, demand, ticks):
        """Advance `ticks` game ticks; returns (input rates, output rates) in belts, averaged over the window."""
        if not hasattr(self, '_dlib'):
            self.dyn_setup()
        ct = self._ct; rate = 0.75
        S = (ct.c_double * max(1, len(supply)))(*supply); D = (ct.c_double * max(1, len(demand)))(*demand)
        ai = (ct.c_double * max(1, len(supply)))(); ao = (ct.c_double * max(1, len(demand)))()
        self._dlib.run_dyn(self.ne, self._dcap, self._drf, len(self.g.splitters), self._sin, self._sout, self._ip, self._op,
                           len(supply), self._srce, S, len(demand), self._snke, D, self.q, int(ticks), ct.c_double(rate), ai, ao)
        k = rate * ticks
        return [ai[i] / k for i in range(len(supply))], [ao[j] / k for j in range(len(demand))]

    def run_py(self, supply, demand, tol=1e-11, max_iter=200000):
        """supply[i] for sources, demand[j] for sinks. Returns (in_flows, out_flows, iters)."""
        g = self.g; cap = self.cap
        s = [0.0] * self.ne
        d = list(cap)
        for i, e in enumerate(self.src_e):
            if e is not None: s[e] = min(cap[e], supply[i])
        for j, e in enumerate(self.snk_e):
            if e is not None: d[e] = min(cap[e], demand[j])
        spl = [(self.spl_in[k], self.spl_out[k], g.splitters[k]['in_prio'], g.splitters[k]['out_prio'])
               for k in range(len(g.splitters))]
        it = 0
        while it < max_iter:
            it += 1
            delta = 0.0
            for (ia, ib), (oc, od), ip, op in spl:
                sa = s[ia] if ia is not None else 0.0
                sb = s[ib] if ib is not None else 0.0
                dc = d[oc] if oc is not None else 0.0
                dd = d[od] if od is not None else 0.0
                I = sa + sb; O = dc + dd
                # offered supply downstream
                if op == 0:
                    nsc = I; nsd = I - min(I, dc)
                elif op == 1:
                    nsd = I; nsc = I - min(I, dd)
                else:
                    nsc = max(I / 2, I - dd); nsd = max(I / 2, I - dc)
                if ip == 0:
                    nda = O; ndb = O - min(O, sa)
                elif ip == 1:
                    ndb = O; nda = O - min(O, sb)
                else:
                    nda = max(O / 2, O - sb); ndb = max(O / 2, O - sa)
                if oc is not None:
                    v = min(cap[oc], nsc); delta = max(delta, abs(v - s[oc])); s[oc] = v
                if od is not None:
                    v = min(cap[od], nsd); delta = max(delta, abs(v - s[od])); s[od] = v
                if ia is not None:
                    v = min(cap[ia], nda); delta = max(delta, abs(v - d[ia])); d[ia] = v
                if ib is not None:
                    v = min(cap[ib], ndb); delta = max(delta, abs(v - d[ib])); d[ib] = v
            for k, ins in enumerate(self.mrg_in):
                o = self.mrg_out[k]
                if o is None: continue
                I = sum(s[i] for i in ins)
                v = min(cap[o], I); delta = max(delta, abs(v - s[o])); s[o] = v
                O = d[o]
                for i in ins:
                    others = I - s[i]
                    v = min(cap[i], max(O / len(ins), O - others))
                    delta = max(delta, abs(v - d[i])); d[i] = v
            if delta < tol:
                break
        f = [min(a, b) for a, b in zip(s, d)]
        fin = [f[e] if e is not None else 0.0 for e in self.src_e]
        fout = [f[e] if e is not None else 0.0 for e in self.snk_e]
        return fin, fout, it


def spread(v):
    return max(v) - min(v) if v else 0.0


def patterns(K, n_random, rnd):
    """Test patterns over K belts: singles, all-but-one, adjacent pairs, prefixes, random mixes."""
    pats = [[1.0 if i == k else 0.0 for i in range(K)] for k in range(K)]
    pats += [[0.0 if i == k else 1.0 for i in range(K)] for k in range(K)]
    pats += [[1.0 if i in (k, (k + 1) % K) else 0.0 for i in range(K)] for k in range(K)]
    pats += [[1.0 if i < k else 0.0 for i in range(K)] for k in range(1, K)]
    pats += [[1.0 if i >= k else 0.0 for i in range(K)] for k in range(1, K)]
    for _ in range(n_random):
        pats.append([rnd.choice([0.0, 1.0, rnd.random()]) for _ in range(K)])
    for _ in range(n_random // 2):
        pats.append([rnd.random() for _ in range(K)])
    for _ in range(n_random // 2):
        pats.append([rnd.choice([0.0, 0.0, 1.0]) for _ in range(K)])
    return [p for p in pats if any(p)]


def heavy_patterns(K, rnd, scale=1):
    pats = patterns(K, 0, rnd)
    if K <= 10:
        pats += [[float((b >> i) & 1) for i in range(K)] for b in range(1, 1 << K)]
    for _ in range(3000 * scale):
        pats.append([rnd.choice([0.0, 1.0, rnd.random()]) for _ in range(K)])
    for _ in range(1500 * scale):
        hi = rnd.choice([0.2, 0.5, 1.0])
        pats.append([rnd.random() * hi for _ in range(K)])
    for _ in range(1500 * scale):
        dens = rnd.choice([0.1, 0.3, 0.5, 0.7, 0.9])
        pats.append([1.0 if rnd.random() < dens else 0.0 for _ in range(K)])
    return [p for p in pats if any(p)]


def check_balancer(g, n_random=40, seed=1, tol=1e-6, verbose=False, heavy=False):
    """Run the standard battery. Returns dict of results."""
    sim = Sim(g)
    N, M = g.n_src, g.n_snk
    rnd = random.Random(seed)
    res = dict(N=N, M=M, warnings=list(g.warnings))
    # 1. full throughput
    fin, fout, it = sim.run([1.0] * N, [1.0] * M)
    res['full_tp'] = sum(fout)
    res['full_ok'] = abs(sum(fout) - min(N, M)) < tol and spread(fout) < tol and spread(fin) < tol
    res['conserve'] = abs(sum(fin) - sum(fout)) < 1e-6
    # 2. output balance with arbitrary inputs, all outputs open
    worst_out = 0.0
    tu_out = 0.0  # throughput deficit when all outputs open
    pats = heavy_patterns(N, rnd) if heavy else patterns(N, n_random, rnd)
    res['n_patterns'] = len(pats)
    for p in pats:
        fin, fout, it = sim.run(p, [1.0] * M)
        worst_out = max(worst_out, spread(fout))
        tu_out = max(tu_out, min(sum(p), M) - sum(fout))
    res['out_balance_err'] = worst_out
    res['tp_deficit_inputs_partial'] = tu_out
    # 3. input balance with arbitrary outputs, all inputs saturated
    worst_in = 0.0
    tu_in = 0.0
    pats = heavy_patterns(M, rnd) if heavy else patterns(M, n_random, rnd)
    res['n_patterns'] += len(pats)
    for p in pats:
        fin, fout, it = sim.run([1.0] * N, p)
        worst_in = max(worst_in, spread(fin))
        tu_in = max(tu_in, min(sum(p), N) - sum(fout))
    res['in_balance_err'] = worst_in
    res['tp_deficit_outputs_partial'] = tu_in
    res['ok'] = res['full_ok'] and worst_out < tol and worst_in < tol and res['conserve']
    return res
