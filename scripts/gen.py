"""Recursive N->M balancer generator (N <= M) out of verified library blocks.

Constructions (all physically verified with the simulator before being accepted):
  LIB    : library block as is
  LOOP   : library block (n+L -> m+L) with L loopbacks around the sides
  K1     : square core P>=m, P-m loopbacks, m-n pruned inputs
  STACK  : gen(n,k) below g side-by-side copies of gen(k/g, m/g)
  SQ+K1  : gen(n,n) below a K1 distributor
"""
import sys, math, time, pickle, os
import sim, compose, library, tier
from compose import Block

HERE = os.path.dirname(os.path.abspath(__file__))
MAXN = 24
LIB = None
MEMO = {}
LOG = []


def lib_blocks(n, m):
    return [v for v in LIB.get((n, m), []) if v['ok'] and v['clean']]


def lib_best(n, m):
    c = lib_blocks(n, m)
    return min(c, key=lambda v: v['block'].cost)['block'] if c else None


def graph_of(block):
    bpd = compose.to_blueprint(block, center=False)
    return sim.parse_blueprint(bpd)


def prune_inputs(block, dead_cols):
    """Remove the input lanes at the given columns (and everything that becomes unfed)."""
    if not dead_cols:
        return block
    g = graph_of(block)
    dead_cols = set(dead_cols)
    remove = set()
    out_edges = {}
    in_count = {}
    for e in g.edges:
        out_edges.setdefault(e['u'][0], []).append(e)
        in_count[e['v'][0]] = in_count.get(e['v'][0], 0) + 1
    dead_src = [('src', i) for i, p in enumerate(g.src_pos) if p[0] in dead_cols]
    assert len(dead_src) == len(dead_cols)
    # everything not reachable from a live input is dead (covers internal loops fed only by dead lanes)
    live = set(('src', i) for i in range(g.n_src)) - set(dead_src)
    stack = list(live)
    while stack:
        node = stack.pop()
        for e in out_edges.get(node, []):
            v = e['v'][0]
            if v not in live:
                live.add(v); stack.append(v)
    dead_spl = set()
    for e in g.edges:
        if e['u'][0] not in live:
            remove.update(e['tiles'])
            if e['v'][0][0] == 'snk':
                raise ValueError('pruning kills an output')
    for k in range(len(g.splitters)):
        if ('spl', k) not in live:
            dead_spl.add(k)
    for k in dead_spl:
        se = g.spl_ents[k]
        ent = dict(name=se['name'], x=se['position']['x'], y=se['position']['y'], direction=se.get('direction', 0))
        remove.update(compose.ent_tiles(ent))
    ents = [dict(e) for e in block.ents if not any(t in remove for t in compose.ent_tiles(e))]
    return Block(ents, block.W, block.H, [c for c in block.ins if c not in dead_cols], block.outs)


def dead_patterns(total, n):
    """Index sets (into `total` middle ports) to kill so that n stay alive."""
    d = total - n
    if d == 0:
        return [()]
    pats = set()
    pats.add(tuple(range(d)))                                  # dead on the left
    pats.add(tuple(range(n, total)))                           # dead on the right
    l = d // 2
    pats.add(tuple(list(range(l)) + list(range(total - (d - l), total))))   # reals centred
    alive = sorted({int(i * total / n) for i in range(n)})    # reals spread
    if len(alive) == n:
        pats.add(tuple(i for i in range(total) if i not in alive))
    alive = sorted({int(i * total / n) + (total // n - 1) for i in range(n)})
    if len(alive) == n and max(alive) < total:
        pats.add(tuple(i for i in range(total) if i not in alive))
    return sorted(pats)


def paired_layouts(P, n, m):
    """Port roles for a P-core when every pruned input can sit next to a loop input (stage 1 pairs
    columns 2k,2k+1): returns list of (left_loop_idx, right_loop_idx, dead_idx)."""
    L, D = P - m, m - n
    if D > L or D == 0:
        return []
    outs = []
    for pl in sorted({D // 2, (D + 1) // 2, 0, D}):
        pr = D - pl
        extra = L - D
        for el in sorted({max(0, min(extra, (L // 2) - pl)), max(0, min(extra, ((L + 1) // 2) - pl)), 0, extra}):
            er = extra - el
            left_loops = [2 * k for k in range(pl)] + [2 * pl + k for k in range(el)]
            dead = [2 * k + 1 for k in range(pl)]
            right_loops = [P - 1 - 2 * k for k in range(pr)] + [P - 1 - 2 * pr - k for k in range(er)]
            dead += [P - 2 - 2 * k for k in range(pr)]
            if len(set(left_loops + right_loops + dead)) != L + D:
                continue
            outs.append((left_loops, right_loops, dead))
    return outs


def k1_variants(n, m, max_extra=16):
    """Yield candidate K1 blocks (unverified) for n<=m."""
    squares = sorted(P for (P, Q) in LIB if P == Q and P >= m and P <= m + max_extra and lib_best(P, P))
    for P in squares[:3]:
        core = lib_best(P, P)
        L = P - m
        for ll, rl, dead in paired_layouts(P, n, m):
            try:
                pruned = prune_inputs(core, [core.ins[i] for i in dead])
                blk = compose.with_loops(pruned, [core.ins[i] for i in ll], [core.ins[i] for i in rl])
                yield ('K1p P=%d loops=%d+%d' % (P, len(ll), len(rl)), blk)
            except ValueError as ex:
                continue
        for nl in sorted({L // 2, 0, L}):
            for dead in dead_patterns(m, n):
                try:
                    mid = core.ins[nl:P - (L - nl)]
                    pruned = prune_inputs(core, [mid[i] for i in dead])
                    blk = compose.with_loops(pruned, nl, L - nl)
                    yield ('K1 P=%d nl=%d dead=%s' % (P, nl, _short(dead)), blk)
                except ValueError as ex:
                    continue


def _short(t):
    t = list(t)
    return str(t) if len(t) <= 6 else '[%d..%d;%d]' % (t[0], t[-1], len(t))


def try_block(name, blk, n, m, best, n_random=60):
    """Keep `blk` if it is cheaper than the current best and passes the full battery."""
    try:
        blk = compose.compress(compose.contiguous(blk))
    except ValueError as ex:
        return best
    if best is not None and blk.cost >= best[1].cost:
        return best
    ok, r = compose.verify(blk, n, m, n_random=n_random)
    if ok:
        return (name, blk)
    return best


def gen(n, m):
    assert 1 <= n <= m
    if (n, m) in MEMO:
        return MEMO[(n, m)]
    t0 = time.time()
    best = None
    lb = lib_best(n, m)
    if lb is not None:
        best = ('LIB', lb)
    else:
        # LOOP on library blocks
        for L in range(1, 17):
            c = lib_best(n + L, m + L)
            if c is None:
                continue
            for nl in sorted({L // 2, (L + 1) // 2}):
                try:
                    best = try_block('LOOP(%d-%d) nl=%d' % (n + L, m + L, nl), compose.with_loops(c, nl, L - nl), n, m, best)
                except ValueError:
                    pass
        if n < m:
            # STACK
            for k in range(n, m):
                for g in range(2, k + 1):
                    if k % g or m % g:
                        continue
                    bottom = gen(n, k)
                    grp = gen(k // g, m // g)
                    if bottom is None or grp is None:
                        continue
                    try:
                        top = compose.hstack([grp[1]] * g)
                        blk = compose.vstack(bottom[1], top)
                    except ValueError:
                        continue
                    best = try_block('STACK %d->%d + %dx(%d->%d)' % (n, k, g, k // g, m // g), blk, n, m, best)
            # K1 direct: only sound for a single input (pruned inputs break input balance under
            # back-pressure; random testing can miss it), so n>1 always gets a square stage in front
            if n == 1:
                for name, blk in k1_variants(n, m):
                    best = try_block(name, blk, n, m, best)
            # SQ + K1 distributor
            if n > 1:
                sq = gen(n, n)
                if sq is not None:
                    for name, blk in k1_variants(n, m):
                        try:
                            full = compose.vstack(sq[1], compose.contiguous(blk))
                        except ValueError:
                            continue
                        best = try_block('SQ(%d) + %s' % (n, name), full, n, m, best)
    MEMO[(n, m)] = best
    LOG.append((n, m, best[0] if best else None, best[1].cost if best else None, best[1].W if best else None,
                best[1].H if best else None, round(time.time() - t0, 1)))
    print('gen %2d->%-2d %-44s ents=%-5s %sx%s  %.1fs' % ((n, m, best[0], best[1].cost, best[1].W, best[1].H, time.time() - t0)
          if best else (n, m, 'NONE', '-', '-', '-', time.time() - t0)), flush=True)
    return best


DOWN = {}


def lib_any(n, m):
    """Cheapest library block that passes the battery (priorities / filters allowed: not meant to be reversed)."""
    c = [v for v in LIB.get((n, m), []) if v['ok']]
    c.sort(key=lambda v: (v['tu'], v['block'].cost))
    return c[0]['block'] if c else None


def gen_down(n, m):
    """n > m. Built from in-game proven n>m library blocks, reversed forward designs (only when the
    reversal is free of sideloads) and the dual constructions."""
    import reverse
    assert n > m >= 1
    if (n, m) in DOWN:
        return DOWN[(n, m)]
    t0 = time.time()
    best = None
    lb = lib_any(n, m)
    if lb is not None:
        best = ('LIB', lb)
    else:
        fwd = gen(m, n)
        if fwd is not None:
            try:
                best = try_block('REVERSED ' + fwd[0], reverse.reverse_block(fwd[1]), n, m, best)
            except (ValueError, AssertionError):
                pass
        # dual of STACK: g groups reduce n -> k, then k -> m on top
        for k in range(m, n):
            for gg in range(2, k + 1):
                if n % gg or k % gg:
                    continue
                a, b = n // gg, k // gg
                grp = gen_down(a, b) if a > b else gen(a, b)
                top = gen_down(k, m) if k > m else gen(k, m)
                if grp is None or top is None:
                    continue
                try:
                    blk = compose.vstack(compose.hstack([grp[1]] * gg), top[1])
                except ValueError:
                    continue
                best = try_block('DSTACK %dx(%d->%d) + %d->%d' % (gg, a, b, k, m), blk, n, m, best)
        # dual of SQ+K1: reversed distributor below an (unreversed) square balancer
        for name, blk in k1_variants(m, n):
            try:
                rev = reverse.reverse_block(compose.contiguous(blk), prio=(m == 1))
                if m == 1:
                    full = rev
                else:
                    sq = gen(m, m)
                    full = compose.vstack(compose.contiguous(rev), sq[1])
            except (ValueError, AssertionError):
                continue
            best = try_block('REV(%s) + SQ(%d)' % (name, m), full, n, m, best)
    DOWN[(n, m)] = best
    print('down %2d->%-2d %-44s ents=%-5s %sx%s  %.1fs' % ((n, m, best[0], best[1].cost, best[1].W, best[1].H, time.time() - t0)
          if best else (n, m, 'NONE', '-', '-', '-', time.time() - t0)), flush=True)
    return best


def main():
    global LIB
    LIB = library.load()
    pairs = [(n, m) for m in range(1, MAXN + 1) for n in range(1, m + 1)]
    if len(sys.argv) > 1:
        pairs = [tuple(map(int, a.split(','))) for a in sys.argv[1:]]
    for n, m in pairs:
        gen(n, m)
    for n, m in pairs:
        if n < m:
            gen_down(m, n)
    if len(sys.argv) == 1:
        allr = dict(MEMO); allr.update(DOWN)
        pickle.dump({k: (v[0], v[1].ents, v[1].W, v[1].H, v[1].ins, v[1].outs) for k, v in allr.items() if v},
                    open(os.path.join(HERE, 'gen_result%s.pkl' % tier.SUFFIX), 'wb'))
    missing = [p for p in pairs if MEMO.get(p) is None] + [(m, n) for n, m in pairs if n < m and DOWN.get((m, n)) is None]
    print('missing:', missing)


if __name__ == '__main__':
    main()
