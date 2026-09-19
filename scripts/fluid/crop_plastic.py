"""Crop each plastic block (pipes, pumps, plants, poles) from the refinery blueprint into an isolated test blueprint.
An infinity-pipe replaces the source segment at the entry pump's input. Circuit conditions are stripped.
usage: crop_plastic.py <refinery.txt> <out_tests.lua> [extra_json ...]"""
import sys, json, copy, collections
sys.path.insert(0, __file__.rsplit('/', 2)[0])
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import bp as BP
import fluidnet as F

def chain_from(segs, byid, port_seg, entry_pump):
    """Follow pump outputs downstream from the entry pump; return (segment ids, pump ids)."""
    seg_ids, pumps = [], [entry_pump]
    sid = port_seg[(entry_pump, 0)]
    while sid is not None:
        seg_ids.append(sid)
        nxt = None
        for (eid, i) in segs[sid]['ports']:
            if byid[eid]['name'] == 'pump' and i == 1 and eid not in pumps:
                pumps.append(eid); nxt = port_seg.get((eid, 0))
        sid = nxt
    return seg_ids, pumps

def crop(bpd, entry_pump, label):
    ents = bpd['entities']
    byid, conns, adj, segs, _ = F.build(ents)
    port_seg = {p: s['id'] for s in segs for p in s['ports']}
    seg_ids, pumps = chain_from(segs, byid, port_seg, entry_pump)
    keep = set(pumps)
    plants = set()
    for sid in seg_ids:
        keep |= segs[sid]['ents']
        for (eid, i) in segs[sid]['ports']:
            if byid[eid]['name'] == 'chemical-plant': plants.add(eid)
    keep |= plants
    xs = [byid[e]['position']['x'] for e in keep]; ys = [byid[e]['position']['y'] for e in keep]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    for e in ents:
        if e['name'] == 'medium-electric-pole' and x0 <= e['position']['x'] <= x1 and y0 <= e['position']['y'] <= y1:
            keep.add(e['entity_number'])
    out = []
    for eid in sorted(keep):
        e = copy.deepcopy(byid[eid]); e.pop('control_behavior', None); out.append(e)
    # infinity pipe at the entry pump's input tile
    p = byid[entry_pump]; d = p.get('direction', 0)
    ox, oy = F.rot((0, 0.5), d)  # input end is the half opposite to the output
    ix, iy = p['position']['x'] + ox * 3, p['position']['y'] + oy * 3
    out.append({'entity_number': 0, 'name': 'infinity-pipe', 'position': {'x': ix, 'y': iy},
                'infinity_settings': {'name': 'petroleum-gas', 'percentage': 1, 'mode': 'at-least'}})
    for i, e in enumerate(out, 1): e['entity_number'] = i
    return {'blueprint': {'item': 'blueprint', 'label': label, 'version': bpd.get('version', 0), 'entities': out}}, len(plants), len(pumps), seg_ids

def lua_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    bpd = BP.decode(open(src).read())['blueprint']
    tests = []
    for entry, label in ((6637, 'left-original'), (6534, 'right-original')):
        t, nplants, npumps, segids = crop(bpd, entry, label)
        print(label, 'plants', nplants, 'pumps', npumps, 'segments', segids, 'entities', len(t['blueprint']['entities']))
        tests.append((label, nplants, BP.encode(t)))
        open(dst.replace('.lua', '') + '_' + label + '.json', 'w').write(json.dumps(t))
    for extra in sys.argv[3:]:
        t = json.load(open(extra)); lab = t['blueprint']['label']
        n = sum(1 for e in t['blueprint']['entities'] if e.get('recipe') == 'plastic-bar')
        print(lab, 'plants', n, 'entities', len(t['blueprint']['entities']))
        tests.append((lab, n, BP.encode(t)))
    with open(dst, 'w') as f:
        f.write('return {\n')
        for lab, n, s in tests:
            f.write('{label=%s, plants=%d, bp=%s},\n' % (lua_str(lab), n, lua_str(s)))
        f.write('}\n')
