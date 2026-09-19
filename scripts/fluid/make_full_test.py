"""Build a full-refinery in-game test: the whole blueprint with infinity pipes replacing one pipe in every
segment that carries petroleum gas from a producer (refinery port 4 / light-oil-cracking outputs) and every
segment attached to a two-fluid consumer's water port. Writes tests.lua for scenario fluid-test.
usage: make_full_test.py out_tests.lua label1=bp1.txt|json [label2=...]"""
import sys, json, copy, collections
sys.path.insert(0, __file__.rsplit('/', 2)[0]); sys.path.insert(0, __file__.rsplit('/', 1)[0])
import bp as BP, fluidnet as F, label as LB

INF = lambda fluid: {'name': fluid, 'percentage': 1, 'mode': 'at-least'}

def producers(ents):
    byid, conns, adj, segs, _ = F.build(ents)
    gas, water, crude = set(), set(), set()
    for s in segs:
        for (eid, i) in s['ports']:
            e = byid[eid]
            if e['name'] == 'oil-refinery' and i == 4: gas.add(s['id'])
            if e['name'] == 'chemical-plant' and e.get('recipe') == 'light-oil-cracking' and F.CONN['chemical-plant'][i][2] == 'out': gas.add(s['id'])
            if e['name'] == 'chemical-plant' and e.get('recipe') in ('sulfur', 'light-oil-cracking', 'heavy-oil-cracking') and i == 0: water.add(s['id'])
            if e['name'] == 'oil-refinery' and i == 0: water.add(s['id'])
            if e['name'] == 'oil-refinery' and i == 1: crude.add(s['id'])
    return byid, segs, gas, water, crude

def make(bpd, label, mode):
    bpd = copy.deepcopy(bpd)
    ents = bpd['entities']
    byid, segs, gas, water, crude = producers(ents)
    n = 0
    todo = [(s, 'water') for s in water] + [(s, 'crude-oil') for s in crude]
    if mode == 'surplus': todo += [(s, 'petroleum-gas') for s in gas]
    if mode == 'inlet':
        # only the segments that receive crude/water from outside the blueprint: no pump inflow, no producer
        byid2, segs2, port_seg, fluid, links = LB.label(ents)
        inflow = set()
        for e in ents:
            if e['name'] == 'pump' and (e['entity_number'], 0) in port_seg: inflow.add(port_seg[(e['entity_number'], 0)])
        todo = []
        for s in segs2:
            f = fluid[s['id']]
            if f in ('water', 'crude-oil') and s['id'] not in inflow:
                prod = [1 for (eid, i) in s['ports'] if byid2[eid]['name'] != 'pump' and F.CONN[byid2[eid]['name']][i][2] == 'out']
                if not prod:
                    todo.append((s['id'], f))
                    xs = [byid2[e]['position']['x'] for e in s['ents']]; ys = [byid2[e]['position']['y'] for e in s['ents']]
                    print(f"  inlet S{s['id']} {f} x[{min(xs)},{max(xs)}] y[{min(ys)},{max(ys)}] ents={len(s['ents'])} tanks={sum(1 for e in s['ents'] if byid2[e]['name']=='storage-tank')}")
        segs = segs2; byid = byid2
    for sid, fluid in todo:
        pipes = [e for e in segs[sid]['ents'] if byid[e]['name'] == 'pipe']
        if not pipes and mode == 'inlet':
            pipes = [e for e in segs[sid]['ents'] if byid[e]['name'] == 'pipe-to-ground']  # inlet is a lone underground stub
        if not pipes:
            print('  segment', sid, 'has no plain pipe; skipped'); continue
        e = byid[sorted(pipes)[len(pipes) // 2]]
        e['name'] = 'infinity-pipe'; e['infinity_settings'] = INF(fluid); e.pop('direction', None); n += 1
    # post-check: every infinity pipe must sit in a segment whose ports are only pumps / consumers of that fluid
    byid3, conns3, adj3, segs3, _ = F.build(ents)
    for s3 in segs3:
        infs = [e for e in s3['ents'] if byid3[e]['name'] == 'infinity-pipe']
        if infs:
            kinds = collections.Counter((byid3[e]['name'], byid3[e].get('recipe'), F.CONN[byid3[e]['name']][i][2]) for e, i in s3['ports'])
            fl = {byid3[e]['infinity_settings']['name'] for e in infs}
            print(f"  infinity seg {s3['id']} fluid={fl} ents={len(s3['ents'])} ports={dict(kinds)}")
            assert len(fl) == 1, 'two different infinity fluids in one segment'
    bpd['label'] = label
    print(label, mode, 'gas segs', sorted(gas), 'water segs', sorted(water), 'crude segs', sorted(crude), 'infinity pipes', n)
    return {'blueprint': bpd}

def lua_str(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

if __name__ == '__main__':
    dst = sys.argv[1]; tests = []
    for arg in sys.argv[2:]:
        label, path = arg.split('=', 1)
        mode = 'surplus' if '-surplus' in label else ('inlet' if '-inlet' in label else 'production')
        clear = ', clear={"plastic-bar"}' if '-plasticonly' in label else ''
        raw = open(path).read()
        bpd = json.loads(raw)['blueprint'] if path.endswith('.json') else BP.decode(raw)['blueprint']
        t = make(bpd, label, mode)
        nplants = sum(1 for e in t['blueprint']['entities'] if e.get('recipe') == 'plastic-bar')
        tests.append((label + clear, nplants, BP.encode(t)))
    with open(dst, 'w') as f:
        f.write('return {\n')
        for lab, n, s in tests:
            lab, _, extra = lab.partition(', ')
            f.write('{label=%s, plants=%d, %sbp=%s},\n' % (lua_str(lab), n, (extra + ', ') if extra else '', lua_str(s)))
        f.write('}\n')
