import json, collections, sys, os
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ingame', 'data', 'script-output', 'fluid_results.json')
r=json.load(open(RESULTS))
L=lambda v:(v.values() if isinstance(v,dict) else v)
for t in r:
    secs=t['meas_ticks']/60; mx=t['rate_max']*secs
    P=list(L(t['plants'])); tot=sum(p['crafts'] for p in P)
    print(f"\n{t['label']}: ghosts={t['ghosts']} revived={t['revived']} inf={t.get('infinity')} modules={t.get('modules')} poles={t.get('poles')} eei={t.get('eei')} errors={t['errors']}")
    print('  refinery ports',t.get('refinery_ports'),'sulfur ports',t.get('sulfur_ports'))
    print('  plant status:',dict(collections.Counter((p['status'],round(p['speed'],2)) for p in P)))
    print(f"  plastic total {100*tot/(mx*len(P)):.1f}% of max ({len(P)} plants)")
    rows=collections.defaultdict(list)
    for p in P: rows[(p['x']<(min(q['x'] for q in P)+max(q['x'] for q in P))/2, p['y'])].append(p['crafts'])
    for k in sorted(rows): print(f"  {'left ' if k[0] else 'right'} row y={k[1]}: n={len(rows[k])} mean={sum(rows[k])/len(rows[k])/mx*100:.1f}% min={min(rows[k])/mx*100:.1f}%")
    pumps=list(L(t['pumps']))
    print('  pump status:',dict(collections.Counter(p['status'] for p in pumps)))
    for p in sorted(pumps,key=lambda p:(p['y'],p['x'])):
        if p.get('cond') and 'petroleum' in p['cond']: print(f"   pump ({p['x']},{p['y']}) {p['cond']} {p['status']} {p['fluid']} {p['amount']:.0f}")
    tanks=list(L(t['tanks']))
    agg=collections.defaultdict(lambda:[0,0.0])
    for tk in tanks: agg[tk['fluid']][0]+=1; agg[tk['fluid']][1]+=tk['amount']
    for name,v in sorted(t.get('recipes',{}).items()): print(f"   recipe {name}: n={v['n']} products/s={v['crafts']/secs:.1f} status={v['status']}")
    print('  tanks:',{k:(v[0],round(v[1])) for k,v in agg.items()})
