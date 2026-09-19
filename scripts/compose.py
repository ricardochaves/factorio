"""Physical composition of belt-balancer blocks (all flows go north: inputs bottom, outputs top).

A Block keeps entities in a local frame: tile (0,0) is the top-left of the bounding box,
y grows downwards (Factorio convention). Entities are dicts with tile-center coordinates.
"""
import copy
import sim

import tier
BELT, UG, SPL = tier.BELT, tier.UG, tier.SPL
N_, E_, S_, W_ = 0, 4, 8, 12


class Block:
    def __init__(self, ents, W, H, ins, outs, label=''):
        self.ents = ents          # list of dict(name,x,y,direction,[type],...)
        self.W, self.H = W, H
        self.ins = list(ins)      # columns of inputs (bottom row, H-1), sorted
        self.outs = list(outs)    # columns of outputs (top row, 0), sorted
        self.label = label

    @property
    def cost(self):
        return len(self.ents)

    def moved(self, dx, dy):
        out = []
        for e in self.ents:
            e = dict(e); e['x'] += dx; e['y'] += dy; out.append(e)
        return out


def belt(x, y, d):
    return dict(name=BELT, x=x + 0.5, y=y + 0.5, direction=d, gen=True)


DXY = {0: (0, -1), 4: (1, 0), 8: (0, 1), 12: (-1, 0)}


def compress(block, min_chunk=4, max_chunk=tier.UG_MAX + 1):
    """Replace long straight runs of generated belts by underground pairs.
    Port tiles (first/last row) and run heads (possible corners) stay as belts."""
    tile = {}
    for e in block.ents:
        for t in ent_tiles(e):
            tile[t] = e
    gen = {t: e for t, e in tile.items() if e.get('gen') and e['name'] == BELT}
    feeds_into = {}
    for t, e in tile.items():
        if e['name'] == BELT:
            dx, dy = DXY[e.get('direction', 0)]
            feeds_into.setdefault((t[0] + dx, t[1] + dy), []).append(t)
    drop = set(); conv = {}
    for t, e in gen.items():
        d = e['direction']; dx, dy = DXY[d]
        prev = (t[0] - dx, t[1] - dy)
        if prev in gen and gen[prev]['direction'] == d:
            continue                      # not a run head
        run = [t]
        while True:
            n = (run[-1][0] + dx, run[-1][1] + dy)
            if n in gen and gen[n]['direction'] == d:
                run.append(n)
            else:
                break
        # usable tiles: skip head (may be a corner / port), skip tail if it is a port or feeds sideways oddly
        usable = run[1:]
        usable = [u for u in usable if 0 < u[1] < block.H - 1 or d in (4, 12)]
        usable = [u for u in usable if len(feeds_into.get(u, [])) <= 1]
        # keep only a contiguous prefix chain
        segs = []; cur = []
        for u in usable:
            if cur and (u[0] - cur[-1][0], u[1] - cur[-1][1]) != (dx, dy):
                segs.append(cur); cur = []
            cur.append(u)
        if cur: segs.append(cur)
        for seg in segs:
            i = 0
            while len(seg) - i >= min_chunk:
                c = min(max_chunk, len(seg) - i)
                conv[seg[i]] = 'input'; conv[seg[i + c - 1]] = 'output'
                drop.update(seg[i + 1:i + c - 1])
                i += c
    ents = []
    for e in block.ents:
        t = ent_tiles(e)[0]
        if e.get('gen') and e['name'] == BELT:
            if t in drop:
                continue
            if t in conv:
                ents.append(dict(name=UG, x=e['x'], y=e['y'], direction=e['direction'], type=conv[t], gen=True))
                continue
        ents.append(dict(e))
    return Block(ents, block.W, block.H, block.ins, block.outs)


def ent_tiles(e):
    """Tiles covered by an entity (local integer tiles)."""
    if e['name'].endswith('splitter'):
        if e.get('direction', 0) in (0, 8):
            return [(int(round(e['x'] - 1)), int(e['y'] - 0.5)), (int(round(e['x'])), int(e['y'] - 0.5))]
        return [(int(e['x'] - 0.5), int(round(e['y'] - 1))), (int(e['x'] - 0.5), int(round(e['y'])))]
    return [(int(e['x'] - 0.5), int(e['y'] - 0.5))]


def to_blueprint(block, label='', icons=None, description=None, version=562949958467584, center=True):
    ents = []
    cx = block.W // 2 if center else 0; cy = block.H // 2 if center else 0
    for i, e in enumerate(sorted(block.ents, key=lambda e: (e['y'], e['x']))):
        o = dict(entity_number=i + 1, name=e['name'], position=dict(x=e['x'] - cx, y=e['y'] - cy))
        if e.get('direction', 0):
            o['direction'] = e['direction']
        for k in ('type', 'input_priority', 'output_priority', 'filter'):
            if k in e:
                o[k] = e[k]
        ents.append(o)
    bpd = dict(icons=icons or [dict(signal=dict(name=SPL), index=1)], entities=ents, item='blueprint',
               label=label, version=version)
    if description:
        bpd['description'] = description
    return bpd


def from_blueprint(b, label=None):
    """Normalise a blueprint dict into a Block (requires north flow, ports on the edges)."""
    raw = []
    for e in b['entities']:
        r = dict(name=e['name'], x=e['position']['x'], y=e['position']['y'], direction=e.get('direction', 0))
        for k in ('type', 'input_priority', 'output_priority', 'filter'):
            if k in e:
                r[k] = e[k]
        raw.append(r)
    ts = [t for e in raw for t in ent_tiles(e)]
    x0 = min(t[0] for t in ts); y0 = min(t[1] for t in ts)
    x1 = max(t[0] for t in ts); y1 = max(t[1] for t in ts)
    for e in raw:
        e['x'] -= x0; e['y'] -= y0
    W, H = x1 - x0 + 1, y1 - y0 + 1
    g = sim.parse_blueprint(b)
    tile_dir = {}
    for e in raw:
        for t in ent_tiles(e):
            tile_dir[t] = e.get('direction', 0)
    ins = sorted(p[0] - x0 for p in g.src_pos)
    outs = sorted(p[0] - x0 for p in g.snk_pos)
    for p in g.src_pos:
        assert p[1] - y0 == H - 1 and tile_dir[(p[0] - x0, p[1] - y0)] == 0, 'input not on bottom edge'
    for p in g.snk_pos:
        assert p[1] - y0 == 0 and tile_dir[(p[0] - x0, p[1] - y0)] == 0, 'output not on top edge'
    return Block(raw, W, H, ins, outs, label or b.get('label', ''))


# ----------------------------------------------------------------------------
# planar routing
# ----------------------------------------------------------------------------

def route_rows(xs, xt):
    """Row assignment for an order-preserving routing xs[i] -> xt[i]. Returns (rows, H)."""
    n = len(xs)
    assert n == len(xt) and list(xs) == sorted(xs) and list(xt) == sorted(xt)
    rows = [None] * n
    for i in range(n - 1, -1, -1):           # right movers, rightmost first
        if xt[i] > xs[i]:
            r = 0
            for j in range(i + 1, n):
                if xt[j] > xs[j] and xs[j] <= xt[i]:
                    r = max(r, rows[j] + 1)
            rows[i] = r
    for i in range(n):                        # left movers, leftmost first
        if xt[i] < xs[i]:
            r = 0
            for j in range(i):
                if xt[j] < xs[j] and xs[j] >= xt[i]:
                    r = max(r, rows[j] + 1)
            rows[i] = r
    H = max([r for r in rows if r is not None], default=-1) + 1
    return rows, H


def route_block(xs, xt):
    """Block routing lanes from bottom columns xs to top columns xt (may contain negative cols)."""
    rows, H = route_rows(xs, xt)
    ents = []
    for i, (a, b) in enumerate(zip(xs, xt)):
        for r in range(H):
            y = H - 1 - r
            if rows[i] is None:
                ents.append(belt(a, y, N_))
            elif r < rows[i]:
                ents.append(belt(a, y, N_))
            elif r > rows[i]:
                ents.append(belt(b, y, N_))
            else:
                step = 1 if b > a else -1
                for x in range(a, b, step):
                    ents.append(belt(x, y, E_ if step == 1 else W_))
                ents.append(belt(b, y, N_))
    return ents, H


def merge_entities(parts):
    """parts: list of entity lists already in a common frame. Normalise to a Block frame."""
    ents = [e for p in parts for e in p]
    seen = {}
    for e in ents:
        for t in ent_tiles(e):
            if t in seen:
                raise ValueError('tile collision at %s' % (t,))
            seen[t] = e
    x0 = min(t[0] for t in seen); y0 = min(t[1] for t in seen)
    x1 = max(t[0] for t in seen); y1 = max(t[1] for t in seen)
    for e in ents:
        e['x'] -= x0; e['y'] -= y0
    return ents, x1 - x0 + 1, y1 - y0 + 1, x0, y0


def vstack(bottom, top, offsets=None):
    """Connect bottom.outs -> top.ins with a planar route, choosing the best horizontal offset."""
    assert len(bottom.outs) == len(top.ins), (len(bottom.outs), len(top.ins))
    if not bottom.outs:
        raise ValueError('no lanes')
    best = None
    if offsets is None:
        base = bottom.outs[0] - top.ins[0]
        offsets = range(base - max(bottom.W, top.W), base + max(bottom.W, top.W) + 1)
    for off in offsets:
        xt = [x + off for x in top.ins]
        _, H = route_rows(bottom.outs, xt)
        width = max(bottom.W, top.W + off) - min(0, off)
        key = (H, width, abs(off))
        if best is None or key < best[0]:
            best = (key, off)
    off = best[1]
    xt = [x + off for x in top.ins]
    rents, RH = route_block(bottom.outs, xt)
    # frame: bottom block's frame. bottom occupies y in [0,H); route above: y in [-RH,0); top above that
    parts = [bottom.moved(0, 0)]
    parts.append([dict(e, y=e['y'] - RH) for e in rents])
    parts.append(top.moved(off, -RH - top.H))
    ents, W, H, x0, y0 = merge_entities(parts)
    return Block(ents, W, H, [x - x0 for x in bottom.ins], [x + off - x0 for x in top.outs])


def hstack(blocks, gap=0):
    """Place blocks side by side (left to right); shorter blocks get their outputs extended upwards."""
    Hmax = max(b.H for b in blocks)
    parts = []; ins = []; outs = []; x = 0
    for b in blocks:
        pad = Hmax - b.H
        parts.append(b.moved(x, pad))
        if pad:
            parts.append([belt(x + c, y, N_) for c in b.outs for y in range(pad)])
        ins += [x + c for c in b.ins]; outs += [x + c for c in b.outs]
        x += b.W + gap
    ents, W, H, x0, y0 = merge_entities(parts)
    return Block(ents, W, H, [c - x0 for c in ins], [c - x0 for c in outs])


def with_loops(core, nl, nr):
    """Loop the outermost outputs of `core` back into inputs, around the sides.
    nl / nr: either a count (the outermost inputs are used) or an explicit list of input columns.
    No real input may lie outside a loop input (keeps the rings planar)."""
    P_out = len(core.outs)
    left_in = sorted(core.ins[:nl] if isinstance(nl, int) else nl)
    right_in = sorted(core.ins[len(core.ins) - nr:] if isinstance(nr, int) else nr, reverse=True) if (nr if isinstance(nr, int) else len(nr)) else []
    nl, nr = len(left_in), len(right_in)
    assert nl + nr <= P_out and set(left_in) <= set(core.ins) and set(right_in) <= set(core.ins)
    assert not (set(left_in) & set(right_in))
    real_in = [c for c in core.ins if c not in left_in and c not in right_in]
    if real_in:
        if left_in and min(real_in) < max(left_in): raise ValueError('real input outside a left loop')
        if right_in and max(real_in) > min(right_in): raise ValueError('real input outside a right loop')
    k = max(nl, nr)
    parts = [core.moved(0, 0)]
    ents = []
    H = core.H
    # frame: core frame; top rows are y=-1..-k ; bottom rows y=H..H+k-1 ; ring 0 = innermost = outermost port
    for j in range(nl):
        o, i = core.outs[j], left_in[j]
        col = -1 - j
        ytop, ybot = -1 - j, H + j
        for y in range(-1, ytop, -1): ents.append(belt(o, y, N_))
        for x in range(o, col, -1): ents.append(belt(x, ytop, W_))
        for y in range(ytop, ybot): ents.append(belt(col, y, S_))
        for x in range(col, i): ents.append(belt(x, ybot, E_))
        for y in range(ybot, H - 1, -1): ents.append(belt(i, y, N_))
    for j in range(nr):
        o, i = core.outs[P_out - 1 - j], right_in[j]
        col = core.W + j
        ytop, ybot = -1 - j, H + j
        for y in range(-1, ytop, -1): ents.append(belt(o, y, N_))
        for x in range(o, col): ents.append(belt(x, ytop, E_))
        for y in range(ytop, ybot): ents.append(belt(col, y, S_))
        for x in range(col, i, -1): ents.append(belt(x, ybot, W_))
        for y in range(ybot, H - 1, -1): ents.append(belt(i, y, N_))
    real_out = core.outs[nl:P_out - nr]
    for c in real_in:
        for y in range(H, H + k): ents.append(belt(c, y, N_))
    for c in real_out:
        for y in range(-k, 0): ents.append(belt(c, y, N_))
    parts.append(ents)
    ents, W, H2, x0, y0 = merge_entities(parts)
    return Block(ents, W, H2, [c - x0 for c in real_in], [c - x0 for c in real_out])


def double_core(core):
    """2P x 2P balancer out of two P x P cores: P splitters pair lane k with lane 2P-1-k (outermost pair
    first). Each pair meets at the two centre columns, is split and returns to its own columns while the
    inner, not yet processed lanes tunnel underneath (5 rows per pair; tunnels span 4 tiles, fine for
    every belt tier). Left half then feeds one core, right half the other."""
    P = len(core.ins)
    assert core.ins == list(range(core.ins[0], core.ins[0] + P)) and len(core.outs) == P
    j = P; H = 5 * j
    ents = []
    Y = lambda u: H - 1 - u
    for k in range(j):
        u0 = 5 * k; a, b = k, 2 * j - 1 - k
        for c in list(range(0, a)) + list(range(b + 1, 2 * j)):          # processed lanes
            for u in range(u0, u0 + 5): ents.append(belt(c, Y(u), N_))
        for c in range(a + 1, b):                                         # inner lanes tunnel
            ents.append(dict(name=UG, x=c + 0.5, y=Y(u0) + 0.5, direction=N_, type='input', gen=True))
            ents.append(dict(name=UG, x=c + 0.5, y=Y(u0 + 4) + 0.5, direction=N_, type='output', gen=True))
        ents.append(belt(a, Y(u0), N_)); ents.append(belt(b, Y(u0), N_))
        for c in range(a, j - 1): ents.append(belt(c, Y(u0 + 1), E_))
        ents.append(belt(j - 1, Y(u0 + 1), N_))
        for c in range(b, j, -1): ents.append(belt(c, Y(u0 + 1), W_))
        ents.append(belt(j, Y(u0 + 1), N_))
        ents.append(dict(name=SPL, x=float(j), y=Y(u0 + 2) + 0.5, direction=N_))
        for c in range(j - 1, a, -1): ents.append(belt(c, Y(u0 + 3), W_))
        ents.append(belt(a, Y(u0 + 3), N_))
        for c in range(j, b): ents.append(belt(c, Y(u0 + 3), E_))
        ents.append(belt(b, Y(u0 + 3), N_))
        ents.append(belt(a, Y(u0 + 4), N_)); ents.append(belt(b, Y(u0 + 4), N_))
    inter = Block(ents, 2 * j, H, list(range(2 * j)), list(range(2 * j)))
    top = hstack([core, core])
    return vstack(inter, top)


def contiguous(block):
    """Add routing so that inputs and outputs are on adjacent columns."""
    def best_target(xs):
        n = len(xs); best = None
        for start in range(min(xs) - n, max(xs) + 1):
            xt = list(range(start, start + n))
            _, H = route_rows(xs, xt)
            key = (H, abs((start + n / 2) - (min(xs) + max(xs) + 1) / 2))
            if best is None or key < best[0]:
                best = (key, xt)
        return best[1]
    b = block
    if b.outs != list(range(b.outs[0], b.outs[0] + len(b.outs))):
        xt = best_target(b.outs)
        rents, RH = route_block(b.outs, xt)
        ents, W, H, x0, y0 = merge_entities([b.moved(0, 0), [dict(e, y=e['y'] - RH) for e in rents]])
        b = Block(ents, W, H, [c - x0 for c in b.ins], [c - x0 for c in xt])
    if b.ins != list(range(b.ins[0], b.ins[0] + len(b.ins))):
        xs = best_target(b.ins)
        rents, RH = route_block(xs, b.ins)
        rents = rents + [belt(c, RH, N_) for c in xs]      # port row: inputs always enter heading north
        ents, W, H, x0, y0 = merge_entities([b.moved(0, 0), [dict(e, y=e['y'] + b.H) for e in rents]])
        b = Block(ents, W, H, [c - x0 for c in xs], [c - x0 for c in b.outs])
    return b


def verify(block, n, m, n_random=25):
    """Physical verification: re-parse the generated entities and run the battery."""
    bpd = to_blueprint(block)
    g = sim.parse_blueprint(bpd)
    if g.n_src != n or g.n_snk != m:
        return False, dict(reason='shape %d->%d' % (g.n_src, g.n_snk), warnings=g.warnings)
    if g.warnings:
        return False, dict(reason='warnings', warnings=g.warnings)
    r = sim.check_balancer(g, n_random=n_random)
    return r['ok'], r
