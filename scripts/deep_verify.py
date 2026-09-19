"""Heavy, parallel verification of every blueprint inside a final book file (the deliverable itself)."""
import sys, re, json, time, os
from multiprocessing import Pool
import bp, sim, tier

def work(args):
    path, b = args
    label = b.get('label', '')
    m = re.match(r'\s*(\d+) to (\d+)', label)
    n, mm = int(m.group(1)), int(m.group(2))
    t = time.time()
    g = sim.parse_blueprint(b)
    out = dict(book=path[-2] if len(path) > 1 else '', label=label, n=n, m=mm, src=g.n_src, snk=g.n_snk, warnings=g.warnings,
               entities=len(b['entities']))
    names = {e['name'] for e in b['entities']}
    out['names_ok'] = names <= {tier.BELT, tier.UG, tier.SPL}
    r = sim.check_balancer(g, seed=12345, heavy=True)
    cols = lambda ps: sorted(p[0] for p in ps); rows = lambda ps: {p[1] for p in ps}
    a, c = cols(g.src_pos), cols(g.snk_pos)
    out['ports_ok'] = (a == list(range(a[0], a[0] + len(a))) and c == list(range(c[0], c[0] + len(c)))
                       and len(rows(g.src_pos)) == 1 and len(rows(g.snk_pos)) == 1)
    out.update(ok=r['ok'] and (g.n_src, g.n_snk) == (n, mm) and out['names_ok'], full_tp=r['full_tp'], out_err=r['out_balance_err'],
               in_err=r['in_balance_err'], patterns=r['n_patterns'], secs=round(time.time() - t, 1),
               tu=r['tp_deficit_inputs_partial'] < 1e-6 and r['tp_deficit_outputs_partial'] < 1e-6)
    return out

if __name__ == '__main__':
    d = bp.decode(open(sys.argv[1]).read())
    jobs = [(p, b) for p, b in bp.walk(d)]
    jobs.sort(key=lambda j: -len(j[1]['entities']))
    t = time.time()
    with Pool(max(2, (os.cpu_count() or 4) - 1)) as pool:
        res = pool.map(work, jobs, chunksize=1)
    bad = [r for r in res if not r['ok']]
    print('blueprints:', len(res), 'ok:', len(res) - len(bad), 'FAIL:', len(bad), 'patterns run:', sum(r['patterns'] for r in res),
          'wall: %.0fs' % (time.time() - t))
    print('non-contiguous/ragged ports:', [r['label'] for r in res if not r['ports_ok']])
    print('with parser warnings:', len([r for r in res if r['warnings']]))
    for r in bad:
        print('FAIL', r)
    pairs = {(r['n'], r['m']) for r in res if r['ok']}
    print('missing pairs:', [(n, m) for n in range(1, 25) for m in range(1, 25) if (n, m) not in pairs])
    books = {}
    for r in res: books.setdefault(r['book'], 0); books[r['book']] += 1
    print('sub-books:', len(books), sorted(books.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0))
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deep_verify%s.json' % tier.SUFFIX), 'w'))
