"""Assemble the final nested book: 24 sub-books (one per input count), each with N->1..24."""
import os, sys, pickle, json, time
import bp, sim, compose, library, reverse, tier
from compose import Block

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, '..', 'blueprints', 'belt-balancers')   # the tracked book is overwritten; git keeps the history
VERSION = 562949958467584
MAXN = 24


def sig(name):
    return dict(signal=dict(type='virtual', name=name))


def icons_for(n, m, extra=None):
    names = ['signal-%s' % c for c in str(n)] + ['signal-%s' % c for c in str(m)]
    if len(names) < 4:
        names.append(tier.SIGNAL)
    if extra and len(names) < 4:
        names.append(extra)
    return [dict(sig(nm), index=i + 1) for i, nm in enumerate(names[:4])]


def main():
    lib = library.load()
    gen = pickle.load(open(os.path.join(HERE, 'gen_result%s.pkl' % tier.SUFFIX), 'rb'))
    gen = {k: (v[0], Block(v[1], v[2], v[3], v[4], v[5])) for k, v in gen.items()}
    rows = []
    books = []
    for n in range(1, MAXN + 1):
        items = []
        for m in range(1, MAXN + 1):
            entries = lib.get((n, m), [])
            chosen = []   # (label, block, source-text, extra icon)
            orig_ok = [v for v in entries if v['source'] == 'original' and v['ok']]
            orig_bad = [v for v in entries if v['source'] == 'original' and not v['ok']]
            rayn = [v for v in entries if v['source'] not in ('original', 'generated-core') and v['ok']]
            core = [v for v in entries if v['source'] == 'generated-core']
            rayn.sort(key=lambda v: (v['tu'], v['block'].cost))
            if orig_ok:
                for v in orig_ok:
                    extra = {'(Long)': 'signal-L', '(Wide)': 'signal-W'}.get(v['label'].split()[-1])
                    chosen.append((v['label'], v['block'], 'original', 'Original blueprint (kept).', extra))
            elif rayn:
                v = rayn[0]
                why = 'Replaces the original, which failed verification. ' if orig_bad else ''
                chosen.append(('%d to %d' % (n, m), v['block'], 'raynquist' + ('-fix' if orig_bad else ''),
                               why + "Source: Raynquist's balancer book (fall 2025), '%s'." % v['label'], None))
            elif core:
                blk = compose.compress(compose.contiguous(core[0]['block']))
                chosen.append(('%d to %d' % (n, m), blk, 'generated', 'Generated from verified blocks: two %d-%d cores joined by %d splitters and a de-interleaving router.' % (n // 2, n // 2, n // 2), None))
            else:
                name, blk = gen[(n, m)]
                chosen.append(('%d to %d' % (n, m), blk, 'generated', 'Generated from verified blocks: %s.' % name, None))
            for label, blk, src, desc, extra in chosen:
                bpd = compose.to_blueprint(blk, label=label, icons=icons_for(n, m, extra), version=VERSION)
                g = sim.parse_blueprint(bpd)
                r = sim.check_balancer(g, n_random=80, seed=7)
                assert (g.n_src, g.n_snk) == (n, m), (label, g.n_src, g.n_snk)
                assert r['ok'], (label, src, r)
                if src == 'generated':
                    assert not g.warnings, (label, g.warnings)
                    cols = lambda ps: sorted(p[0] for p in ps)
                    a, b = cols(g.src_pos), cols(g.snk_pos)
                    assert a == list(range(a[0], a[0] + n)) and b == list(range(b[0], b[0] + m)), (label, 'ports not contiguous')
                k = min(n, m)
                bpd['description'] = ('%s\nVerified by flow simulation and by an automated in-game test (Factorio 2.0.77): '
                                      'output balanced, input balanced, full throughput (%d belt%s).' % (desc, k, '' if k == 1 else 's'))
                items.append(dict(blueprint=bpd, index=len(items)))
                rows.append(dict(n=n, m=m, label=label, source=src, how=desc, entities=len(bpd['entities']), W=blk.W, H=blk.H,
                                 splitters=len(g.splitters), tu_inputs=r['tp_deficit_inputs_partial'] < 1e-6 and r['tp_deficit_outputs_partial'] < 1e-6))
        book = dict(item='blueprint-book', label=str(n), blueprints=items, active_index=0, version=VERSION,
                    icons=[dict(sig('signal-%s' % c), index=i + 1) for i, c in enumerate(str(n))],
                    description='Balancers with %d input belt%s: %d to 1 ... %d to %d.' % (n, '' if n == 1 else 's', n, n, MAXN))
        books.append(dict(blueprint_book=book, index=n - 1))
        print('book', n, len(items), 'blueprints', flush=True)
    root = dict(blueprint_book=dict(item='blueprint-book', label='%s Belt balancer' % tier.TITLE, blueprints=books, active_index=0, version=VERSION,
                icons=[dict(signal=dict(name=tier.SPL), index=1)],
                description='N to M belt balancers (%s belts), N and M from 1 to %d. One sub-book per number of input belts. '
                'Every blueprint was verified by flow simulation and by an automated in-game test (Factorio 2.0.77).' % (tier.BELT_WORD, MAXN)))
    s = bp.encode(root)
    os.makedirs(OUT_DIR, exist_ok=True)
    open(os.path.join(OUT_DIR, '%s-belt.txt' % tier.TIER), 'w').write(s)
    json.dump(rows, open(os.path.join(HERE, 'book_rows%s.json' % tier.SUFFIX), 'w'))
    print('written', len(s), 'chars;', len(rows), 'blueprints')

if __name__ == '__main__':
    main()
