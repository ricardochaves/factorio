"""Compare the dynamic simulator against the in-game measurements (same phase sequence)."""
import json, os, sys, bp, sim
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'ingame/data/script-output')
WARM, MEAS = 9000, 3600
def pattern(ph, n, m):
    sup = [1.0] * n; dem = [1.0] * m
    if ph == 'B' and n > 1: sup = [1.0 if (k + 1) % 2 == 1 else 0.0 for k in range(n)]
    if ph == 'D' and n > 1: sup = [1.0 if (k + 1) <= -(-n // 3) else 0.0 for k in range(n)]
    if ph == 'C' and m > 1: dem = [1.0 if (k + 1) % 2 == 1 else 0.0 for k in range(m)]
    if ph == 'E' and m > 1: dem = [1.0 if (k + 1) <= -(-m // 3) else 0.0 for k in range(m)]
    return sup, dem
def lst(v, n):
    return [v.get(str(i + 1), 0) for i in range(n)] if isinstance(v, dict) else list(v) + [0] * (n - len(v))
def work(args):
    label, b, meas = args
    g = sim.parse_blueprint(b); s = sim.Sim(g); s.dyn_setup(); s.dyn_reset()
    # port order: in-game ports are sorted by column; parser order may differ
    si = sorted(range(g.n_src), key=lambda i: g.src_pos[i][0]); so = sorted(range(g.n_snk), key=lambda j: g.snk_pos[j][0])
    worst = 0; detail = None
    for ph in 'ABCDE':
        sup, dem = pattern(ph, g.n_src, g.n_snk)
        S = [0] * g.n_src; D = [0] * g.n_snk
        for r, i in enumerate(si): S[i] = sup[r]
        for r, j in enumerate(so): D[j] = dem[r]
        s.dyn(S, D, WARM); fi, fo = s.dyn(S, D, MEAS)
        pi = [fi[i] * 2700 for i in si]; po = [fo[j] * 2700 for j in so]
        mi, mo = meas[ph]
        err = max([abs(a - b) for a, b in zip(pi, mi)] + [abs(a - b) for a, b in zip(po, mo)])
        if err > worst: worst = err; detail = (ph, [round(x) for x in pi], mi, [round(x) for x in po], mo)
    return label, worst, detail, len(g.warnings)
if __name__ == '__main__':
    d = bp.decode(open(os.path.join(HERE, '../blueprints/belt-balancers/blue-belt.txt')).read())
    bl = {b['label']: b for p, b in bp.walk(d)}
    meas = {}
    for ph in 'ABCDE':
        for r in json.load(open(os.path.join(OUT, 'balancer_results_%s.json' % ph))):
            meas.setdefault(r['label'], {})[ph] = (lst(r['ins'], r['n']), lst(r['outs'], r['m']))
    jobs = [(l, bl[l], meas[l]) for l in bl if l in meas]
    with Pool(8) as pool: res = pool.map(work, jobs, chunksize=4)
    res = [r for r in res if r[3] == 0]
    res.sort(key=lambda r: -r[1])
    import statistics
    print('blueprints compared:', len(res), ' max abs error (items per 2700-window): median %.1f' % statistics.median(r[1] for r in res))
    for thr in (30, 60, 135, 270): print('  error >', thr, ':', sum(1 for r in res if r[1] > thr))
    for r in res[:12]: print(r[0], round(r[1]), r[2])
    probs = {p[1] for p in json.load(open(os.path.join(HERE, 'ingame_problems.json')))}
    print('in-game problem blueprints:', len(probs), '; of those, sim error > 60:', sum(1 for r in res if r[0] in probs and r[1] > 60))
