"""Reverse the flow of a block: an N->M balancer becomes an M->N balancer.

Every belt is re-pointed along the reversed path, undergrounds swap input/output, and the whole
thing is rotated by 180 degrees so that it flows north again. A splitter that had an unused input
gets an unused output after the reversal; when something sits in front of that output it is blocked
with the usual deconstruction-planner filter trick.
"""
import sim, compose
from compose import Block

DIR_OF = {(0, -1): 0, (1, 0): 4, (0, 1): 8, (-1, 0): 12}
BLOCK_FILTER = {'name': 'deconstruction-planner', 'quality': 'normal', 'comparator': '='}


def scc_of(g):
    """Tarjan SCC over graph nodes. Returns dict node -> component id, plus '_cyclic' = set of ids with a cycle."""
    adj = {}
    for ed in g.edges:
        adj.setdefault(ed['u'][0], []).append(ed['v'][0]); adj.setdefault(ed['v'][0], [])
    index = {}; low = {}; onst = set(); st = []; comp = {}; cyc = set(); counter = [0]; cid = [0]
    import sys
    sys.setrecursionlimit(100000)
    def visit(v):
        index[v] = low[v] = counter[0]; counter[0] += 1; st.append(v); onst.add(v)
        for w in adj[v]:
            if w not in index:
                visit(w); low[v] = min(low[v], low[w])
            elif w in onst:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            members = []
            while True:
                w = st.pop(); onst.discard(w); comp[w] = cid[0]; members.append(w)
                if w == v: break
            if len(members) > 1 or v in adj[v]:
                cyc.add(cid[0])
            cid[0] += 1
    for v in list(adj):
        if v not in index:
            visit(v)
    comp['_cyclic'] = cyc
    return comp


def reverse_block(block, prio=None):
    """prio: add output priorities on loop take-off splitters (default: only for single-output results,
    where it cannot disturb the output balance)."""
    if prio is None:
        prio = len(block.ins) == 1
    bpd = compose.to_blueprint(block, center=False)
    g = sim.parse_blueprint(bpd)
    if g.warnings or g.merges:
        raise ValueError('not reversible: %s' % g.warnings[:2])
    for e in block.ents:
        if any(k in e for k in ('input_priority', 'output_priority', 'filter')):
            raise ValueError('not reversible: priorities/filters')
    came_from = {}                      # tile -> direction of travel INTO the tile (old flow)
    spl_inputs = {}                     # splitter index -> set of fed halves
    for ed in g.edges:
        ts = ed['tiles']
        for a, b in zip(ts, ts[1:]):
            came_from[b] = (b[0] - a[0], b[1] - a[1])
        if ed['v'][0][0] == 'spl':
            spl_inputs.setdefault(ed['v'][0][1], set()).add(ed['v'][1])
    tile = {}
    for e in block.ents:
        for t in compose.ent_tiles(e):
            tile[t] = e
    spl_index = {}
    for k, se in enumerate(g.spl_ents):
        spl_index[(se['position']['x'], se['position']['y'])] = k
    # strongly connected components of the splitter graph: a reversed splitter with one output staying
    # inside its loop and one output leaving it must prefer the leaving one (otherwise, in the real
    # game, the loop saturates and steals capacity from the inputs next to it)
    comp = scc_of(g)
    out_side = {}                       # splitter index -> reversed output half (old input half) that leaves the SCC
    for k in range(len(g.splitters)):
        ins = [ed for ed in g.edges if ed['v'][0] == ('spl', k)]
        if len(ins) != 2:
            continue
        inside = [comp.get(ed['u'][0]) == comp[('spl', k)] and comp[('spl', k)] in comp['_cyclic'] for ed in ins]
        if inside.count(True) == 1:
            leaving = ins[inside.index(False)]
            out_side[k] = leaving['v'][1]
    out = []
    W, H = block.W, block.H
    for e in block.ents:
        e2 = dict(e)
        d = e.get('direction', 0)
        t = compose.ent_tiles(e)[0]
        if e['name'].endswith('splitter'):
            k = spl_index[(e['x'], e['y'])]
            fed = spl_inputs.get(k, set())
            if prio and k in out_side:
                # old input half h sits on the (1-h) side after reversing (rotation keeps handedness)
                e2['output_priority'] = 'right' if out_side[k] == 0 else 'left'
            for h in (0, 1):
                if h in fed:
                    continue
                # tile behind the unused input half (old frame) = in front of the reversed output
                halves = compose.ent_tiles(e)
                dx, dy = sim.DIRS[d]
                left, right = (halves[0], halves[1]) if d in (0, 4) else (halves[1], halves[0])
                ht = left if h == 0 else right
                behind = (ht[0] - dx, ht[1] - dy)
                if behind in tile:
                    e2['filter'] = dict(BLOCK_FILTER)
                    e2['output_priority'] = 'right' if h == 0 else 'left'
        elif e['name'].endswith('underground-belt'):
            e2['type'] = 'output' if e.get('type', 'input') == 'input' else 'input'
        else:
            v = came_from.get(t)
            if v is None:
                # first tile of an edge: fed by a splitter / source -> entered along its feeder direction
                cands = []
                for (dx, dy), dd in DIR_OF.items():
                    p = (t[0] - dx, t[1] - dy)
                    pe = tile.get(p)
                    if pe is not None and pe['name'].endswith('splitter') and pe.get('direction', 0) == dd:
                        cands.append(dd)
                if len(cands) == 1:
                    e2['direction'] = cands[0]
                else:
                    assert not cands, (t, cands)
                    e2['direction'] = d                      # old source tile: keep straight
            else:
                e2['direction'] = DIR_OF[v]
        # rotate by 180 degrees (positions only: reversing + rotating keeps the direction value)
        e2['x'] = W - e['x']; e2['y'] = H - e['y']
        out.append(e2)
    ins = sorted(W - 1 - c for c in block.outs)
    outs = sorted(W - 1 - c for c in block.ins)
    return Block(out, W, H, ins, outs)


if __name__ == '__main__':
    import library, render
    lib = library.load()
    for key in [(1,3),(2,3),(3,5),(4,7),(7,10),(8,12),(12,25),(16,16),(1,17),(9,12)]:
        b = [v for v in lib[key] if v['ok'] and v['clean']][0]['block']
        r = reverse_block(b)
        bpd = compose.to_blueprint(r)
        g = sim.parse_blueprint(bpd)
        res = sim.check_balancer(g, n_random=40)
        print(key, '->', (g.n_src, g.n_snk), res['ok'], g.warnings[:2])
    b = reverse_block([v for v in lib[(1,3)] if v['clean']][0]['block'])
    print(render.render(compose.to_blueprint(b)))
    print([e for e in b.ents if 'filter' in e])
