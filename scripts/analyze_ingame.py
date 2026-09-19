"""Analyse the in-game measurements written by the balancer-test scenario."""
import json, os, sys, tier
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'ingame/data/script-output')
FULL_BELT = tier.ITEMS_PER_SEC * 60          # items per 3600-tick window on an express belt
verbose = '-v' in sys.argv
def lst(v, n):
    if isinstance(v, dict): return [v.get(str(i + 1), 0) for i in range(n)]
    return list(v) + [0] * (n - len(v))
summary = {}; problems = []
build = json.load(open(os.path.join(OUT, 'balancer_results_build.json')))
for r in build:
    errs = r['errors'] if isinstance(r['errors'], list) else list(r['errors'].values()) if r['errors'] else []
    if errs or r['ghosts'] != r['built'] or r['revived'] != r['ghosts']:
        problems.append(('build', r['label'], errs, r['ghosts'], r['revived'], r['built']))
print('built blueprints:', len(build), 'build problems:', len([p for p in problems if p[0] == 'build']))
for ph in [c for c in 'ABCDEFGHI' if os.path.exists(os.path.join(OUT, 'balancer_results_%s.json' % c))]:
    res = json.load(open(os.path.join(OUT, 'balancer_results_%s.json' % ph)))
    worst_out = worst_in = 0; worst_tp = 0
    for r in res:
        n, m = r['n'], r['m']
        ins, outs = lst(r['ins'], n), lst(r['outs'], m)
        ion, oon = lst(r['in_on'], n), lst(r['out_on'], m)
        a_in = [v for v, on in zip(ins, ion) if on]; a_out = [v for v, on in zip(outs, oon) if on]
        tot_in, tot_out = sum(ins), sum(outs)
        expect = min(len(a_in), len(a_out)) * FULL_BELT
        # output balance is only promised when every output is drained; input balance when every input is fed
        out_spread = (max(a_out) - min(a_out)) if len(a_out) == m else 0
        in_spread = (max(a_in) - min(a_in)) if len(a_in) == n else 0
        tp_def = (expect - tot_out) / expect if (len(a_in) == n and len(a_out) == m) else 0
        tol = 0.012 * FULL_BELT + 6
        unsteady = abs(tot_in - tot_out) > 0.02 * max(tot_out, 1) + 30
        if unsteady: summary.setdefault('unsteady', []).append((ph, r['label'], tot_in, tot_out))
        bad = out_spread > tol or in_spread > tol or tp_def > 0.01
        worst_out = max(worst_out, out_spread); worst_in = max(worst_in, in_spread); worst_tp = max(worst_tp, tp_def)
        if bad: problems.append((ph, r['label'], 'ins', ins, 'outs', outs))
        if verbose: print(ph, r['label'], 'ins', ins, 'outs', outs)
    print('phase %s: %d blueprints, worst output spread %d items, worst input spread %d items (window = %d items/belt), worst throughput deficit %.2f%%'
          % (ph, len(res), worst_out, worst_in, FULL_BELT, worst_tp * 100))
print('not yet steady (in != out within the window; informational):', len(summary.get('unsteady', [])), summary.get('unsteady', [])[:8])
print('PROBLEMS:', len(problems))
for p in problems[:40]: print('  ', p)
json.dump(problems, open(os.path.join(HERE, 'ingame_problems%s.json' % tier.SUFFIX), 'w'))
