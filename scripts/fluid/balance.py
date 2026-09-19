"""Mass balance per fluid from the in-game run (products_finished includes productivity crafts; inputs use crafts/(1+prod))."""
import json, collections, sys, os
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ingame', 'data', 'script-output', 'fluid_results.json')
r=json.load(open(RESULTS))
for t in r:
    secs=t['meas_ticks']/60
    print(f"\n=== {t['label']} ===")
    prod=collections.defaultdict(float); cons=collections.defaultdict(float); items=collections.defaultdict(float)
    for name,v in t['recipes'].items():
        rd=t['recipe_data'][name]
        crafts=v['crafts']/secs
        incrafts=sum(m['crafts']/(1+m['prod']) for m in v['per'])/secs
        for g in rd['products']:
            (prod if g['type']=='fluid' else items)[g['name']]+=crafts*g['amount']
        for g in rd['ingredients']:
            if g['type']=='fluid': cons[g['name']]+=incrafts*g['amount']
        tot=sum(v['samples'].values()) or 1
        frac={k:f"{100*x/tot:.0f}%" for k,x in sorted(v['samples'].items(),key=lambda kv:-kv[1])}
        if v['expect_per_s']: print(f"  {name:32s} n={v['n']:3d} {100*crafts/v['expect_per_s']:5.1f}% of max  {frac}")
    tanks=collections.defaultdict(lambda:[0,0.0])
    for tk in (t['tanks'].values() if isinstance(t['tanks'],dict) else t['tanks']): tanks[tk['fluid']][0]+=1; tanks[tk['fluid']][1]+=tk['amount']
    print(f"  {'fluid':15s} {'produced/s':>11s} {'consumed/s':>11s} {'net/s':>9s}   tanks(n, total, %full)")
    for f in ('crude-oil','water','heavy-oil','light-oil','petroleum-gas','lubricant','sulfuric-acid'):
        n,a=tanks.get(f,[0,0]); print(f"  {f:15s} {prod[f]:11.0f} {cons[f]:11.0f} {prod[f]-cons[f]:9.0f}   {n}, {a:.0f}, {100*a/(25000*n) if n else 0:.0f}%")
    v=t['recipes']['advanced-oil-processing']; rows=collections.defaultdict(list)
    for m in v['per']: rows[m['y']].append(m['crafts']/secs/m['expect'])
    print('  refineries by row:',{y:f"n={len(l)} {100*sum(l)/len(l):.1f}%" for y,l in sorted(rows.items())})
    for name in ('sulfur','sulfuric-acid','light-oil-cracking','heavy-oil-cracking','plastic-bar'):
        v=t['recipes'][name]; tot=sum(sum(m['st'].values()) for m in v['per']) or 1
        lw=sum(m.get('low',{}).get('water',0) for m in v['per']); lo=sum(m.get('low',{}).get('other',0) for m in v['per'])
        print(f"  {name:22s} samples with box1 (water/first) low: {100*lw/tot:4.0f}%   box2 low: {100*lo/tot:4.0f}%")
    print('  items/s:',{k:round(v,1) for k,v in items.items() if v})
