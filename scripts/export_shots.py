"""Export the balancers photographed for the site as a Lua table for scenario balancer-shot.

usage: python3 scripts/export_shots.py ["8 to 8"]
Writes scripts/ingame/data/scenarios/balancer-shot/shots.lua (generated, git-ignored): the same label from each of the
three canonical books (yellow, red, blue), with the tile columns of its input (bottom row) and output (top row) belts.
"""
import math
import os
import sys

import bp

HERE = os.path.dirname(os.path.abspath(__file__))
BOOKS = os.path.join(HERE, '../blueprints/belt-balancers')
DST = os.path.join(HERE, 'ingame/data/scenarios/balancer-shot/shots.lua')
TIERS = [  # left to right in the overview shot
    ('yellow', '', 'iron-plate'),
    ('red', 'fast-', 'copper-plate'),
    ('blue', 'express-', 'electronic-circuit'),
]


def tiles(e):
    """Tiles covered by a belt, underground belt or splitter (direction 0/4/8/12 = N/E/S/W)."""
    x, y, d = e['position']['x'], e['position']['y'], e.get('direction', 0)
    if e['name'].endswith('splitter'):
        if d in (0, 8):
            return [(math.floor(x - 0.5), math.floor(y)), (math.floor(x + 0.5), math.floor(y))]
        return [(math.floor(x), math.floor(y - 0.5)), (math.floor(x), math.floor(y + 0.5))]
    return [(math.floor(x), math.floor(y))]


def ports(b):
    """Columns (relative to the leftmost tile) of the north-facing belts in the bottom and top rows."""
    occ = {}
    for e in b['entities']:
        for t in tiles(e):
            occ[t] = e
    minx = min(t[0] for t in occ)
    y0, y1 = min(t[1] for t in occ), max(t[1] for t in occ)
    row = lambda y: sorted(x - minx for (x, yy), e in occ.items() if yy == y and e.get('direction', 0) == 0)
    w = max(t[0] for t in occ) - minx + 1
    return row(y1), row(y0), w, y1 - y0 + 1


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else '8 to 8'
    n, m = (int(v) for v in label.split(' to '))
    out = []
    for tier, prefix, item in TIERS:
        book = bp.decode(open(os.path.join(BOOKS, f'{tier}-belt.txt')).read())
        found = [b for _, b in bp.walk(book) if b.get('label') == label]
        if len(found) != 1:
            sys.exit(f'{tier}: expected one "{label}", found {len(found)}')
        b = found[0]
        ins, outs, w, h = ports(b)
        if len(ins) != n or len(outs) != m:
            sys.exit(f'{tier} {label}: found {len(ins)} inputs / {len(outs)} outputs in the edge rows')
        s = bp.encode({'blueprint': b})
        out.append('{tier=%r, belt=%r, loader=%r, item=%r, label=%r, w=%d, h=%d, ins={%s}, outs={%s}, bp="%s"}' % (
            tier, prefix + 'transport-belt', prefix + 'loader', item, label, w, h,
            ','.join(map(str, ins)), ','.join(map(str, outs)), s))
        print(f'{tier:6} {label}: {w}x{h} tiles, inputs {ins}, outputs {outs}')
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    with open(DST, 'w') as f:
        f.write('return {\n' + ',\n'.join(out) + '\n}\n')
    print('wrote', os.path.relpath(DST))


if __name__ == '__main__':
    main()
