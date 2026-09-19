"""Export every blueprint of the final book as a Lua table for the in-game test scenario."""
import sys, os, bp, sim, compose, tier
HERE = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '../blueprints/belt-balancers/%s-belt.txt' % tier.TIER)
dst = os.path.join(HERE, 'ingame/data/scenarios/balancer-test')
os.makedirs(dst, exist_ok=True)
d = bp.decode(open(src).read())
flt = sys.argv[2] if len(sys.argv) > 2 else None
import re
chunks = []; cnt = 0
for p, b in bp.walk(d):
    if flt and not re.search(flt, b['label']): continue
    g = sim.parse_blueprint(b)
    tiles = []
    for e in b['entities']:
        r = dict(name=e['name'], x=e['position']['x'], y=e['position']['y'], direction=e.get('direction', 0))
        tiles += compose.ent_tiles(r)
    minx = min(t[0] for t in tiles)
    W = max(t[0] for t in tiles) - minx + 1; H = max(t[1] for t in tiles) - min(t[1] for t in tiles) + 1
    ins = sorted(q[0] - minx for q in g.src_pos); outs = sorted(q[0] - minx for q in g.snk_pos)
    s = bp.encode({'blueprint': b})
    chunks.append('{label=%r, n=%d, m=%d, w=%d, h=%d, count=%d, ins={%s}, outs={%s}, bp="%s"}' % (
        b['label'], len(ins), len(outs), W, H, len(b['entities']), ','.join(map(str, ins)), ','.join(map(str, outs)), s))
    cnt += 1
# several files to keep each Lua chunk small
per = 60; files = []
for i in range(0, len(chunks), per):
    name = 'tests_%02d' % (i // per)
    open(os.path.join(dst, name + '.lua'), 'w').write('return {\n' + ',\n'.join(chunks[i:i + per]) + '\n}\n')
    files.append(name)
open(os.path.join(dst, 'tier.lua'), 'w').write('return {loader="%s", warm=%d, phases={%s}}\n' % (tier.LOADER, -(-int(os.environ.get('FBWARM', 15000 * 45 // tier.ITEMS_PER_SEC)) // 600) * 600, ','.join('"%s"' % c for c in os.environ.get('FBPHASES', 'ABCDEFGHI'))))
open(os.path.join(dst, 'tests.lua'), 'w').write('local all = {}\nfor _, f in pairs({%s}) do for _, t in pairs(require(f)) do all[#all+1] = t end end\nreturn all\n'
                                                 % ','.join('"%s"' % f for f in files))
print('exported', cnt, 'tests in', len(files), 'files')
