# HISTORICAL: this one-off patch produced refinery v2 (archive/original_blue_prints/refinaria.txt -> archive/refinery-v2/refinaria_v2.txt).
# It is kept for reference only; the current blueprint is blueprints/oil-refinery/oil-refinery.txt and
# later versions live in git history. The archive/ inputs are local-only (git-ignored).
"""Add two parallel feed pumps (S29 -> S59) for the right plastic block, same 95000 threshold as the left block.
Verifies with the fluid model that no other segment changes. Wrote refinaria_v2.txt (+ .json); usage: patch_plastic_feed.py <src.txt> <dst.txt>."""
import sys, json, copy, collections
sys.path.insert(0, __file__.rsplit('/', 2)[0]); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import bp as BP, fluidnet as F, label as LB

SRC, DST = sys.argv[1], sys.argv[2]
orig = BP.decode(open(SRC).read())
bpd = copy.deepcopy(orig['blueprint'])
ents = bpd['entities']; byid = {e['entity_number']: e for e in ents}
nid = max(byid) + 1
def add(e):
    global nid
    e['entity_number'] = nid; ents.append(e); nid += 1; return e['entity_number']
COND = lambda c: {'circuit_enabled': True, 'circuit_condition': {'first_signal': {'type': 'fluid', 'name': 'petroleum-gas'}, 'constant': c, 'comparator': '>'}}
POLE = 7113  # medium pole that carries the tank signal (green) next to pump 6997

# 1. underground pair 6992 (w) / 6994 (e) on row 456 -> plain pipes, plus the two tiles between them
for eid in (6992, 6994):
    assert byid[eid]['name'] == 'pipe-to-ground'
    byid[eid]['name'] = 'pipe'; byid[eid].pop('direction', None)
add({'name': 'pipe', 'position': {'x': -241.5, 'y': 456.5}})
add({'name': 'pipe', 'position': {'x': -240.5, 'y': 456.5}})
# 2. pump B on row 457: tap pipe + pump straight into S59 pipe 6996
add({'name': 'pipe', 'position': {'x': -239.5, 'y': 457.5}})
pb = add({'name': 'pump', 'position': {'x': -238, 'y': 457.5}, 'direction': 4, 'control_behavior': COND(95000)})
# 3. pump A on row 455: tap pipe + pump + output pipe down into S59 pipe 6995
add({'name': 'pipe', 'position': {'x': -239.5, 'y': 455.5}})
pa = add({'name': 'pump', 'position': {'x': -238, 'y': 455.5}, 'direction': 4, 'control_behavior': COND(95000)})
add({'name': 'pipe', 'position': {'x': -236.5, 'y': 455.5}})
# 4. medium pole so pump A is inside a supply area (the existing poles only touch its edge)
pole = add({'name': 'medium-electric-pole', 'position': {'x': -235.5, 'y': 455.5}})
bpd['wires'] += [[pa, 2, POLE, 2], [pb, 2, POLE, 2], [pole, 5, POLE, 5]]
bpd['label'] = 'refinaria v2 (plastic right feed)'

# --- verification with the fluid model -------------------------------------------------------
def segmap(entities):
    byid_, segs, port_seg, fluid, links = LB.label(entities)
    return [(frozenset(s['ents']), frozenset(s['ports']), fluid[s['id']]) for s in segs], port_seg, byid_
o_segs, o_ps, _ = segmap(orig['blueprint']['entities'])
n_segs, n_ps, nbyid = segmap(ents)
new_ports = {(pa, 0), (pa, 1), (pb, 0), (pb, 1)}
added_ents = {e['entity_number'] for e in ents if e['entity_number'] > max(byid) - 8 and e['name'] == 'pipe'}
changed = []
for ents_o, ports_o, fl in o_segs:
    hits = [t for t in n_segs if ents_o & t[0]]
    if len(hits) != 1: changed.append(('split/lost', len(hits), sorted(ents_o)[:3])); continue
    ents_n, ports_n, fl_n = hits[0]
    if ents_n - ents_o - added_ents: changed.append(('merged ents', sorted(ents_n - ents_o - added_ents)[:5]))
    if ports_n - ports_o - new_ports or ports_o - ports_n: changed.append(('ports', sorted(ports_n ^ ports_o)[:5]))
    if fl != fl_n and not fl.startswith('UNKNOWN'): changed.append(('fluid', fl, fl_n))
print('segments original', len(o_segs), 'new', len(n_segs), 'unexpected changes:', changed)
sa, sb = n_ps[(pa, 1)], n_ps[(pa, 0)]
print('pump A: from seg', sa, 'to seg', sb, '| pump B: from', n_ps[(pb, 1)], 'to', n_ps[(pb, 0)])
print('pump 6997: from', n_ps[(6997, 1)], 'to', n_ps[(6997, 0)], '| 6637:', n_ps[(6637, 1)], '->', n_ps[(6637, 0)])
assert (n_ps[(pa, 1)], n_ps[(pa, 0)]) == (n_ps[(6997, 1)], n_ps[(6997, 0)]) == (n_ps[(pb, 1)], n_ps[(pb, 0)])
assert not changed
# collision check on tiles
occ = collections.Counter()
import math
for e in ents:
    n = e['name']; px, py = e['position']['x'], e['position']['y']; d = e.get('direction', 0)
    if n == 'pump':
        tiles = [(math.floor(px), math.floor(py - 0.5)), (math.floor(px), math.floor(py + 0.5))] if d in (0, 8) else [(math.floor(px - 0.5), math.floor(py)), (math.floor(px + 0.5), math.floor(py))]
    elif n in ('pipe', 'pipe-to-ground', 'medium-electric-pole'):
        tiles = [(math.floor(px), math.floor(py))]
    else: continue
    for t in tiles: occ[t] += 1
newtiles = [(-236, 455), (-242, 456), (-241, 456), (-240, 456), (-239, 456), (-240, 457), (-239, 457), (-238, 457), (-240, 455), (-239, 455), (-238, 455), (-237, 455)]
print('tile occupancy of touched tiles:', {t: occ[t] for t in newtiles})
assert all(occ[t] == 1 for t in newtiles)
out = {'blueprint': bpd}
open(DST, 'w').write(BP.encode(out)); json.dump(out, open(DST.replace('.txt', '.json'), 'w'))
print('written', DST, 'entities', len(ents), 'wires', len(bpd['wires']))
