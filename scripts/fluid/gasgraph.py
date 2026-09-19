"""Directed graph of the petroleum-gas network: segments as nodes, pumps as edges."""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 2)[0]); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import bp as BP, fluidnet as F, label as LB
bpd = BP.decode(open(sys.argv[1]).read())['blueprint']
byid, segs, port_seg, fluid, links = LB.label(bpd['entities'])
gas = {sid for sid, f in fluid.items() if f == 'petroleum-gas'}
def cond(e):
    cb = (e.get('control_behavior') or {}).get('circuit_condition'); return cb and f"{cb['first_signal']['name'][:3]}{cb['comparator']}{cb['constant']}" or ''
def node(sid):
    s = segs[sid]; xs = [byid[e]['position']['x'] for e in s['ents']]; ys = [byid[e]['position']['y'] for e in s['ents']]
    tanks = sum(1 for e in s['ents'] if byid[e]['name'] == 'storage-tank')
    cons = collections.Counter(byid[e].get('recipe') for e, i in s['ports'] if byid[e]['name'] != 'pump' and F.CONN[byid[e]['name']][i][2] == 'in')
    prod = collections.Counter(byid[e].get('recipe') for e, i in s['ports'] if byid[e]['name'] != 'pump' and F.CONN[byid[e]['name']][i][2] == 'out')
    return f"S{sid} [{min(xs):.0f}..{max(xs):.0f}, {min(ys):.0f}..{max(ys):.0f}] pipes={len(s['ents'])} tanks={tanks} in={dict(cons)} out={dict(prod)}"
print('GAS SEGMENTS'); [print(' ', node(s)) for s in sorted(gas)]
print('PUMP EDGES (from -> to)')
for e in bpd['entities']:
    if e['name'] != 'pump': continue
    a, b = port_seg.get((e['entity_number'], 1)), port_seg.get((e['entity_number'], 0))
    if a in gas or b in gas:
        print(f"  S{a} -> S{b}  pump {e['entity_number']} ({e['position']['x']},{e['position']['y']}) {cond(e)}")
