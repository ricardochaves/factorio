# HISTORICAL: this one-off patch produced refinery v3 (archive/refinery-v2/refinaria_v2.json -> blueprints/oil-refinery/oil-refinery.txt).
# It is kept for reference only; the current blueprint is blueprints/oil-refinery/oil-refinery.txt and
# later versions live in git history. The archive/ inputs are local-only (git-ignored).
"""v3 = v2 + doubled water feed to the sulfuric-acid/sulfur block (path S91 -> S44 -> tank 6843).
P1 parallel to pump 9026 (S91 -> S44), P2 parallel to pump 6844 (S44 -> S37 tank, water<23500)."""
import sys, json, copy, collections, math
sys.path.insert(0, __file__.rsplit('/', 2)[0]); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import bp as BP, fluidnet as F, label as LB

SRC, DST = sys.argv[1], sys.argv[2]
orig = json.load(open(SRC))
bpd = copy.deepcopy(orig['blueprint']); ents = bpd['entities']; byid = {e['entity_number']: e for e in ents}
nid = max(byid) + 1
def add(e):
    global nid
    e['entity_number'] = nid; ents.append(e); nid += 1; return e['entity_number']
def pipe(x, y): return add({'name': 'pipe', 'position': {'x': x, 'y': y}})
WATER_LOW = {'circuit_enabled': True, 'circuit_condition': {'first_signal': {'type': 'fluid', 'name': 'water'}, 'constant': 23500, 'comparator': '<'}}

# --- P1: S91 -> S44, parallel to 9026 (-116.5,485) ---------------------------------------
assert byid[8748]['name'] == 'pipe-to-ground' and byid[8748]['position'] == {'x': -116.5, 'y': 479.5}
byid[8748]['name'] = 'pipe'; byid[8748].pop('direction', None)              # surface junction of S44
add({'name': 'pipe-to-ground', 'position': {'x': -116.5, 'y': 480.5}, 'direction': 0})  # new partner of 8882 (483.5, d8)
pipe(-115.5, 486.5)                                                          # tap S91 (pipe 9137 to the west)
p1 = add({'name': 'pump', 'position': {'x': -115.5, 'y': 485}, 'direction': 0})
for y in (483.5, 482.5, 481.5, 480.5, 479.5): pipe(-115.5, y)               # up to the S44 junction at 8748
pole = add({'name': 'medium-electric-pole', 'position': {'x': -114.5, 'y': 486.5}})
# --- P2: S44 -> S37 tank 6843 (south connection), parallel to 6844 (-127,453.5) -----------
pipe(-116.5, 452.5)                                                          # tap S44 (pipe 6846 to the south)
for x in (-117.5, -118.5, -119.5, -120.5, -121.5, -122.5, -123.5, -124.5): pipe(x, 452.5)
pipe(-124.5, 453.5); pipe(-124.5, 454.5)
p2 = add({'name': 'pump', 'position': {'x': -126, 'y': 454.5}, 'direction': 12, 'control_behavior': copy.deepcopy(WATER_LOW)})
pipe(-127.5, 454.5); pipe(-128.5, 454.5)                                     # into tank 6843 south connection
bpd['wires'] += [[p2, 2, 6843, 2], [pole, 5, 9135, 5]]
bpd['label'] = 'refinaria v3 (plastic feed + acid water)'

# --- verification -------------------------------------------------------------------------
def segmap(entities):
    b, segs, ps, fl, _ = LB.label(entities)
    return [(frozenset(s['ents']), frozenset(s['ports']), fl[s['id']]) for s in segs], ps
o_segs, o_ps = segmap(orig['blueprint']['entities']); n_segs, n_ps = segmap(ents)
new_ports = {(p1, 0), (p1, 1), (p2, 0), (p2, 1)}
added = {e['entity_number'] for e in ents if e['entity_number'] not in byid or e['entity_number'] >= max(orig['blueprint']['entities'], key=lambda e: e['entity_number'])['entity_number'] + 1}
changed = []
for ents_o, ports_o, fl in o_segs:
    hits = [t for t in n_segs if ents_o & t[0]]
    if len(hits) != 1: changed.append(('split/lost', len(hits), sorted(ents_o)[:3])); continue
    ents_n, ports_n, fl_n = hits[0]
    if ents_n - ents_o - added: changed.append(('merged', fl, sorted(ents_n - ents_o - added)[:5]))
    if ports_n - ports_o - new_ports or ports_o - ports_n: changed.append(('ports', fl, sorted(ports_n ^ ports_o)[:5]))
    if fl != fl_n: changed.append(('fluid', fl, fl_n))
print('segments', len(o_segs), '->', len(n_segs), 'unexpected:', changed)
print('P1', n_ps[(p1, 1)], '->', n_ps[(p1, 0)], '| 9026', n_ps[(9026, 1)], '->', n_ps[(9026, 0)])
print('P2', n_ps[(p2, 1)], '->', n_ps[(p2, 0)], '| 6844', n_ps[(6844, 1)], '->', n_ps[(6844, 0)])
assert not changed
assert (n_ps[(p1, 1)], n_ps[(p1, 0)]) == (n_ps[(9026, 1)], n_ps[(9026, 0)])
assert (n_ps[(p2, 1)], n_ps[(p2, 0)]) == (n_ps[(6844, 1)], n_ps[(6844, 0)])
# tile collisions
occ = collections.Counter()
SIZE = {'chemical-plant': 3, 'oil-refinery': 5, 'storage-tank': 3, 'assembling-machine-3': 3, 'beacon': 3, 'substation': 2, 'roboport': 4, 'radar': 3}
for e in ents:
    n = e['name']; px, py = e['position']['x'], e['position']['y']; d = e.get('direction', 0)
    if n in ('pump', 'decider-combinator', 'arithmetic-combinator'):
        tiles = [(math.floor(px), math.floor(py - 0.5)), (math.floor(px), math.floor(py + 0.5))] if d in (0, 8) else [(math.floor(px - 0.5), math.floor(py)), (math.floor(px + 0.5), math.floor(py))]
    else:
        s = SIZE.get(n, 1)
        tiles = [(math.floor(px) + i, math.floor(py) + j) for i in range(-(s // 2), s // 2 + 1) for j in range(-(s // 2), s // 2 + 1)] if s % 2 else [(int(px) - s // 2 + i, int(py) - s // 2 + j) for i in range(s) for j in range(s)]
    for t in tiles: occ[t] += 1
dup = [t for t, c in occ.items() if c > 1]
print('overlapping tiles:', dup); assert not dup
out = {'blueprint': bpd}
open(DST, 'w').write(BP.encode(out)); json.dump(out, open(DST.replace('.txt', '.json'), 'w'))
print('written', DST, 'entities', len(ents), 'wires', len(bpd['wires']))
