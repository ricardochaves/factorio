"""Make a blueprint compatible with a shorter underground range by splitting long tunnels where the
surface tiles allow an intermediate exit+entrance."""
import sim, compose, tier

def fix_entities(ents, maxd):
    """ents: list of blueprint entity dicts (position/direction/type). Returns (new_ents, n_split) or None."""
    occ = {}
    for e in ents:
        r = dict(name=e['name'], x=e['position']['x'], y=e['position']['y'], direction=e.get('direction', 0))
        for t in compose.ent_tiles(r):
            occ[t] = e
    ugs = {t: e for t, e in occ.items() if e['name'].endswith('underground-belt')}
    new = []; nsplit = 0
    for t, e in ugs.items():
        if e.get('type', 'input') != 'input':
            continue
        d = e.get('direction', 0); dx, dy = sim.DIRS[d]
        k = None
        for j in range(1, 12):
            o = ugs.get((t[0] + dx * j, t[1] + dy * j))
            if o is not None and o.get('direction', 0) == d:
                k = j if o.get('type') == 'output' else None
                break
        if k is None or k <= maxd:
            continue
        # choose intermediate pairs (exit at a, entrance at a+1) on free tiles, all hops <= maxd
        free = [j for j in range(1, k) if (t[0] + dx * j, t[1] + dy * j) not in occ]
        best = None
        def search(pos, plan):
            nonlocal best
            if k - pos <= maxd:
                if best is None or len(plan) < len(best): best = list(plan)
                return
            if best is not None and len(plan) + 1 >= len(best): return
            for a in range(min(k - 2, pos + maxd), pos, -1):
                if a in free and (a + 1) in free and a + 1 < k:
                    search(a + 1, plan + [a])
        search(0, [])
        if best is None:
            return None
        for a in best:
            for j, typ in ((a, 'output'), (a + 1, 'input')):
                p = (t[0] + dx * j, t[1] + dy * j)
                ne = dict(name=e['name'], position=dict(x=p[0] + 0.5, y=p[1] + 0.5), type=typ)
                if d: ne['direction'] = d
                occ[p] = ne; new.append(ne)
            nsplit += 1
    out = [dict(e) for e in ents] + new
    for i, e in enumerate(out): e['entity_number'] = i + 1
    return out, nsplit

def fix_blueprint(b, maxd=None):
    maxd = maxd or tier.UG_MAX
    r = fix_entities(b['entities'], maxd)
    if r is None:
        return None
    b2 = dict(b); b2['entities'] = r[0]
    return b2

if __name__ == '__main__':
    import bp, re, os
    d = bp.decode(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sources/raynquist_github.txt')).read())
    for p, b in bp.walk(d):
        l = b.get('label') or ''
        if 'FAQ' in ' '.join(map(str, p)) or not re.match(r'^(9-9|10-10|12-12|16-16|32-32|8-8|7-7|9-\d+|\d+-9|8-10|12-25|20-15) ', l): continue
        for maxd in (7, 5):
            b1 = dict(b); b1['entities'] = [dict(e) for e in b['entities']]
            fb = fix_blueprint(b1, maxd)
            if fb is None: print(l, maxd, 'UNFIXABLE'); continue
            import os
            pre = {5: '', 7: 'fast-'}[maxd]
            fb['entities'] = [dict(e, name=pre + e['name'].replace('express-', '')) for e in fb['entities']]
            g = sim.parse_blueprint(fb); r = sim.check_balancer(g, n_random=20)
            print(l, 'max', maxd, 'added', len(fb['entities']) - len(b['entities']), 'ok' if r['ok'] and not g.warnings else ('BAD', g.warnings[:2]))
