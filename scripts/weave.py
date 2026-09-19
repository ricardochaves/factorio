"""De-interleaving router used to double a P x P core: after P splitters on adjacent lanes, left outputs go
to the left core and right outputs to the right core. Horizontal runs are packed in bands of rows; every
lane crossed inside a band tunnels under the whole band (tunnel length fits the belt tier)."""
import random
import tier
from compose import belt, Block, UG, SPL, N_, E_, W_


def schedule(src, rng, park, R, rnd):
    """src: lane -> column; rng: lane -> (lo, hi) final columns; park: columns usable as temporary parking.
    A band holds only moves in one direction, ordered so that sources and targets both grow away from the
    destination side (then no run crosses a lane that moved in the same band)."""
    col = dict(src)
    done = lambda l: rng[l][0] <= col[l] <= rng[l][1]
    bands = []
    guard = 0
    while not all(done(l) for l in col):
        guard += 1
        if guard > 200: return None
        best = None
        for kind in ('a', 'b'):
            sign = 1 if kind == 'a' else -1            # a lanes travel left, b lanes travel right
            lanes = [l for l in col if l[0] == kind and not done(l)]
            lanes.sort(key=lambda l: sign * col[l])
            taken = set(col.values())
            runs = []; last_s = None; last_t = None
            skip = rnd.random() < 0.3
            for l in lanes:
                if len(runs) >= R: break
                s0 = col[l]
                if last_s is not None and sign * s0 <= sign * last_s: continue
                final = [c for c in range(rng[l][0], rng[l][1] + 1) if c not in taken]
                temp = [c for c in park if c not in taken and s0 not in park]
                cands = final if final else temp
                cands = [c for c in cands if sign * c < sign * s0 and (last_t is None or sign * c > sign * last_t)]
                if not cands: continue
                cands.sort(key=lambda c: sign * c)
                t = cands[0] if not (skip and len(cands) > 1 and rnd.random() < 0.3) else cands[1]
                runs.append((l, len(runs), s0, t)); taken.add(t); last_s, last_t = s0, t
            score = sum(2 if rng[l][0] <= t <= rng[l][1] else 1 for l, _, _, t in runs) + rnd.random()
            if runs and (best is None or score > best[0]): best = (score, runs)
        if best is None: return None
        for l, r, s0, t in best[1]: col[l] = t
        bands.append(best[1])
    return bands


def build(j, core_gap=None, tries=300, seed=1):
    core_gap = core_gap or (tier.UG_MAX - 1)
    """Block: 2j contiguous inputs -> j splitters -> left outputs on columns 0..j-1, right outputs on j+gap.."""
    R = tier.UG_MAX - 1
    g = core_gap
    src = {}; tgt = {}
    half = (j + 1) // 2
    pos = list(range(0, 2 * half)) + list(range(2 * half + g, 2 * j + g))      # sources, gap in the middle
    for i in range(j):
        src[('a', i)] = pos[2 * i]; tgt[('a', i)] = (0, j - 1)
        src[('b', i)] = pos[2 * i + 1]; tgt[('b', i)] = (j + g, 2 * j + g - 1)
    park = [c for c in range(2 * j + g) if c not in pos]
    best = None
    for k in range(tries):
        b = schedule(src, tgt, park, R, random.Random(seed * 1000 + k))
        if b is None: continue
        h = sum(max(r for _, r, _, _ in runs) + 1 + 2 for runs in b)
        if best is None or h < best[0]: best = (h, b)
    if best is None:
        raise ValueError('weave deadlock')
    bands = best[1]
    # rows counted upwards: 0 = input belts, 1 = splitters, then bands
    cells = []                         # (col, u, kind, dir/type)
    col = dict(src)
    for c in pos: cells.append((c, 0, 'belt', N_))
    for i in range(j): cells.append((pos[2 * i], 1, 'spl', N_))
    u = 2
    for runs in bands:
        used = max(r for _, r, _, _ in runs) + 1
        moved = {l: (r, s, t) for l, r, s, t in runs}
        crossed = set()
        for l, r, s, t in runs:
            for c in range(min(s, t) + 1, max(s, t)): crossed.add(c)
        for l in col:
            if l in moved:
                r, s, t = moved[l]
                cells.append((s, u, 'belt', N_))
                for rr in range(r): cells.append((s, u + 1 + rr, 'belt', N_))
                step = 1 if t > s else -1
                for c in range(s, t, step): cells.append((c, u + 1 + r, 'belt', E_ if step == 1 else W_))
                cells.append((t, u + 1 + r, 'belt', N_))
                for rr in range(r + 1, used): cells.append((t, u + 1 + rr, 'belt', N_))
                cells.append((t, u + 1 + used, 'belt', N_))
                col[l] = t
            elif col[l] in crossed:
                cells.append((col[l], u, 'ug', 'input')); cells.append((col[l], u + 1 + used, 'ug', 'output'))
            else:
                for rr in range(used + 2): cells.append((col[l], u + rr, 'belt', N_))
        u += used + 2
    H = u
    ents = []
    for c, uu, kind, d in cells:
        y = H - 1 - uu
        if kind == 'belt': ents.append(belt(c, y, d))
        elif kind == 'spl': ents.append(dict(name=SPL, x=float(c + 1), y=y + 0.5, direction=N_))
        else: ents.append(dict(name=UG, x=c + 0.5, y=y + 0.5, direction=N_, type=d, gen=True))
    outs = sorted(col.values())
    return Block(ents, max(outs) + 1, H, pos, outs)


if __name__ == '__main__':
    import compose, render
    for j in (8, 16):
        b = build(j); print(tier.TIER, 'j', j, 'rows', b.H, 'ents', b.cost)
    print(render.render(compose.to_blueprint(build(8))))
