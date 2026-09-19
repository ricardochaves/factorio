"""Label every fluid segment of a blueprint with its fluid, propagating from recipes, pumps and circuit conditions."""
import sys, json, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import fluidnet as F

# fluids per recipe: (inputs, outputs) in recipe order
RECIPE = {
 'advanced-oil-processing': (['water', 'crude-oil'], ['heavy-oil', 'light-oil', 'petroleum-gas']),
 'heavy-oil-cracking': (['water', 'heavy-oil'], ['light-oil']),
 'light-oil-cracking': (['water', 'light-oil'], ['petroleum-gas']),
 'plastic-bar': (['petroleum-gas'], []), 'sulfur': (['water', 'petroleum-gas'], []),
 'solid-fuel-from-petroleum-gas': (['petroleum-gas'], []), 'solid-fuel-from-light-oil': (['light-oil'], []),
 'lubricant': (['heavy-oil'], ['lubricant']), 'battery': (['sulfuric-acid'], []), 'sulfuric-acid': (['water'], ['sulfuric-acid']),
 'explosives': (['water'], []), 'flamethrower-ammo': (['crude-oil'], []),
 'barrel': ([], []), 'sulfuric-acid-barrel': (['sulfuric-acid'], []), 'lubricant-barrel': (['lubricant'], []),
 'water-barrel': (['water'], []), 'light-oil-barrel': (['light-oil'], []), 'heavy-oil-barrel': (['heavy-oil'], []),
 'rocket-fuel': (['light-oil'], []),
}

def label(ents):
    byid, conns, adj, segs, _ = F.build(ents)
    port_seg = {p: s['id'] for s in segs for p in s['ports']}
    cand = collections.defaultdict(set)   # seg -> candidate fluids (from machine ports)
    fixed = {}                             # seg -> fluid known for sure
    for s in segs:
        for (eid, i) in s['ports']:
            e = byid[eid]; n = e['name']
            if n == 'pump':
                cb = (e.get('control_behavior') or {}).get('circuit_condition')
                if cb and cb['first_signal'].get('type') == 'fluid':
                    cand[s['id']].add(cb['first_signal']['name'])
                continue
            rec = e.get('recipe')
            if rec not in RECIPE: continue
            ins, outs = RECIPE[rec]
            kind = F.CONN[n][i][2]
            # verified in game (2.0.77): refinery ports 1..5 = water, crude, heavy, light, petroleum;
            # chemical plant with two fluid inputs: port 0 = first ingredient (water), port 1 = second.
            if kind == 'in':
                if len(ins) == 1: fixed.setdefault(s['id'], set()).add(ins[0])
                elif len(ins) == 2: fixed.setdefault(s['id'], set()).add(ins[i])
            elif kind == 'out':
                if len(outs) == 1: fixed.setdefault(s['id'], set()).add(outs[0])
                elif n == 'oil-refinery': fixed.setdefault(s['id'], set()).add(outs[i - 2])
    # pumps link segments: same fluid
    pump_links = collections.defaultdict(set)
    for e in ents:
        if e['name'] == 'pump':
            a, b = port_seg.get((e['entity_number'], 0)), port_seg.get((e['entity_number'], 1))
            if a is not None and b is not None:
                pump_links[a].add(b); pump_links[b].add(a)
    fluid = {}
    for sid, fs in fixed.items():
        if len(fs) == 1: fluid[sid] = next(iter(fs))
        else: fluid[sid] = 'CONFLICT:' + ','.join(sorted(fs))
    changed = True
    while changed:
        changed = False
        for sid in range(len(segs)):
            if sid in fluid: continue
            nb = {fluid[o] for o in pump_links[sid] if o in fluid and not fluid[o].startswith('CONFLICT')}
            c = cand.get(sid, set())
            pick = None
            if len(nb) == 1: pick = next(iter(nb))
            elif len(c) == 1: pick = next(iter(c))
            elif len(nb & c) == 1: pick = next(iter(nb & c))
            if pick: fluid[sid] = pick; changed = True
    # second pass: resolve remaining candidates by intersection with pump neighbours
    for sid in range(len(segs)):
        if sid not in fluid:
            c = cand.get(sid, set()); nb = {fluid[o] for o in pump_links[sid] if o in fluid}
            fluid[sid] = 'UNKNOWN:' + ','.join(sorted(c | nb))
    return byid, segs, port_seg, fluid, pump_links

if __name__ == '__main__':
    sys.path.insert(0, __file__.rsplit('/', 2)[0]); import bp as BP
    bpd = BP.decode(open(sys.argv[1]).read())['blueprint']
    byid, segs, port_seg, fluid, links = label(bpd['entities'])
    print(collections.Counter(fluid.values()))
    for sid, f in fluid.items():
        if f.startswith('UNKNOWN') or f.startswith('CONFLICT'):
            s = segs[sid]; xs = [byid[e]['position']['x'] for e in s['ents']]; ys = [byid[e]['position']['y'] for e in s['ents']]
            print(sid, f, len(s['ents']), f"x[{min(xs)},{max(xs)}] y[{min(ys)},{max(ys)}]", {(byid[e]['name'], byid[e].get('recipe'), i) for e, i in s['ports']})
