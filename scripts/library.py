"""Library of verified physical blocks: user's original book + Raynquist fall 2025."""
import re, os, bp, sim, compose, tier
HERE = os.path.dirname(os.path.abspath(__file__))
_cache = None
def load():
    """Returns dict (n,m) -> list of dict(block, source, label, bp, clean) ; all pass the battery."""
    global _cache
    if _cache: return _cache
    lib = {}
    srcs = [('original', os.path.join(HERE, 'sources/original-balancers.txt')),
            ('raynquist-2025', os.path.join(HERE, 'sources/raynquist_github.txt'))]

    for src, path in srcs:
        d = bp.decode(open(path).read())
        for p, b in bp.walk(d):
            label = b.get('label') or ''
            full = ' / '.join(map(str, p))
            if src.startswith('dogmaisea'):
                dm = re.match(r'^(\d+)_(\d+)(?:_alt)?(?:_balancer)?(?:_(yellow|red|blue))?$', label)
                if not dm: continue
                label = '%s-%s balancer' % (dm.group(1), dm.group(2))
            elif src != 'original':
                if 'FAQ' in full: continue
                if 'downgrades' in full:
                    dm = re.match(r'^(\d+-\d+) (yellow|red) ((?:TU )?balancer)$', label)
                    if not dm or tier.TIER == 'blue' or tier.RANK[dm.group(2)] > tier.RANK[tier.TIER]: continue
                    label = '%s %s' % (dm.group(1), dm.group(3))
                if not re.match(r'^\d+-\d+ (TU )?balancer( \(.*\))?$', label): continue
            if len(b['entities']) > 1000: continue
            b = tier.retier_blueprint(b)
            if (b.get('version', 0) >> 48) < 2:      # Factorio 1.x blueprint: 8-way directions
                b['entities'] = [dict(e, direction=e['direction'] * 2) if e.get('direction') else e for e in b['entities']]
                b['version'] = 562949958467584
            m = re.match(r'\s*(\d+)\s*(?:to|-)\s*(\d+)', label)
            if not m: continue
            n, mm = int(m.group(1)), int(m.group(2))
            try:
                blk = compose.from_blueprint(b)
            except AssertionError as ex:
                continue
            g = sim.parse_blueprint(b)
            if (g.n_src, g.n_snk) != (n, mm): continue
            if any('unpaired' in w for w in g.warnings): continue
            r = sim.check_balancer(g, n_random=25)
            clean = not g.warnings and not any(('input_priority' in e or 'output_priority' in e or 'filter' in e) for e in b['entities'])
            lib.setdefault((n, mm), []).append(dict(block=blk, source=src, label=label, bp=b, ok=r['ok'], clean=clean, tu='TU' in label))
    if tier.TIER != 'blue':
        # no 32-32 exists for the short underground ranges: build it from two 16-16 cores
        for P in (8, 16):
            c = [v for v in lib.get((P, P), []) if v['ok'] and v['clean']]
            if c and not [v for v in lib.get((2 * P, 2 * P), []) if v['ok'] and v['clean']]:
                core = min(c, key=lambda v: v['block'].cost)['block']
                import weave
                core0 = core
                core = compose.contiguous(core)
                cands = [compose.compress(compose.double_core(core))]
                try:
                    for base in (core0, core):
                        gp = max(tier.UG_MAX - 1, base.W - P)
                        cands.append(compose.compress(compose.vstack(weave.build(P, core_gap=gp), compose.hstack([base, base], gap=P + gp - base.W))))
                except ValueError:
                    pass
                cands = [c for c in cands if compose.verify(c, 2 * P, 2 * P, n_random=60)[0]]
                blk = min(cands, key=lambda c: c.cost)
                ok, r = compose.verify(blk, 2 * P, 2 * P, n_random=60)
                assert ok, r
                lib.setdefault((2 * P, 2 * P), []).append(dict(block=blk, source='generated-core', label='%d-%d balancer' % (2 * P, 2 * P),
                                                                bp=compose.to_blueprint(blk), ok=True, clean=True, tu=False))
    _cache = lib
    return lib
if __name__ == '__main__':
    lib = load()
    for k in sorted(lib):
        print(k, [(v['source'][:4], v['label'], 'ok' if v['ok'] else 'FAIL', 'clean' if v['clean'] else 'dirty', v['block'].cost) for v in lib[k]])
