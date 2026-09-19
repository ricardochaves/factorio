"""Export the city block blueprints as a Lua table for the scenarios city-test and city-shot.

usage: python3 scripts/export_city.py
Writes strings.lua next to each scenario's control.lua (generated, git-ignored). Besides each blueprint string it
carries the numbers the scenario must find in the game (entities and tiles by name, wires by kind, size), counted here
from the decoded JSON, so the game run is checked against an independent count.
It also refuses a blueprint that is not mirror-symmetric (tiles and entities): neighboring blocks only line up when
each side mirrors the side facing it.
"""
import os
import re
import sys
from collections import Counter

import bp

HERE = os.path.dirname(os.path.abspath(__file__))
SCENARIOS = ['city-test', 'city-shot']
# variant name (used by the scenarios) -> catalog folder; the blueprint file is named after its folder
VARIANTS = {'partial-concrete': 'city-block-100x100-partial-concrete', 'full-concrete': 'city-block-100x100-full-concrete'}
WIRE_KINDS = {1: 'red', 2: 'green', 5: 'copper'}   # wire connector ids in the blueprint JSON
STRING = re.compile(r'0[A-Za-z0-9+/=]+')           # a blueprint string is the version byte plus base64: safe in a Lua literal
SWAP = {'refined-hazard-concrete-left': 'refined-hazard-concrete-right',
        'refined-hazard-concrete-right': 'refined-hazard-concrete-left'}   # a mirror image flips the hazard stripes


def lua_counts(counter):
    return '{' + ', '.join('[%r]=%d' % (k, v) for k, v in sorted(counter.items())) + '}'


def check_mirror(name, b):
    """Every tile and entity must have its mirror image across the block's vertical and horizontal midlines."""
    tiles = {(t['position']['x'], t['position']['y']): t['name'] for t in b['tiles']}
    bad = [(x, y) for (x, y), n in tiles.items()
           if tiles.get((99 - x, y)) != SWAP.get(n, n) or tiles.get((x, 99 - y)) != SWAP.get(n, n)]
    assert not bad, f'{name}: {len(bad)} tiles without a mirror image, e.g. {sorted(bad)[:6]}'
    ents = {(e['name'], e['position']['x'], e['position']['y']) for e in b['entities']}
    bad = [e for e in ents if (e[0], 100 - e[1], e[2]) not in ents or (e[0], e[1], 100 - e[2]) not in ents]
    assert not bad, f'{name}: {len(bad)} entities without a mirror image, e.g. {sorted(bad)[:6]}'


def main():
    rows, tile_maps = [], {}
    for name, folder in VARIANTS.items():
        text = open(os.path.join(HERE, '../blueprints', folder, folder + '.txt')).read().strip()
        assert STRING.fullmatch(text), f'{name}: not a plain blueprint string'
        b = bp.decode(text)['blueprint']
        ents, tiles = b['entities'], b['tiles']
        grid = b['snap-to-grid']
        assert b.get('absolute-snapping') and grid == {'x': 100, 'y': 100}, 'expected a 100x100 absolute grid'
        check_mirror(name, b)
        tile_maps[name] = {(t['position']['x'], t['position']['y']): t['name'] for t in tiles}
        wires = Counter(WIRE_KINDS[w[1]] for w in b['wires'])   # KeyError: a wire kind this test does not know
        rows.append('{name=%r, label=%r, entities=%s, tiles=%s, wires=%s, n_entities=%d, n_tiles=%d, n_wires=%d, cell=%d,\n bp="%s"}' % (
            name, b['label'], lua_counts(Counter(e['name'] for e in ents)), lua_counts(Counter(t['name'] for t in tiles)),
            lua_counts(wires), len(ents), len(tiles), len(b['wires']), grid['x'], text))
        print(f'{name:16} {len(ents)} entities, {len(tiles)} tiles, {len(b["wires"])} wires {dict(wires)}, mirror-symmetric')
    # city-test compares the seams between a partial and a full concrete block only along the edge band; that is enough
    # because every tile of the partial blueprint is also in the full one, under the same name.
    partial, full = tile_maps['partial-concrete'], tile_maps['full-concrete']
    missing = [pos for pos, n in partial.items() if full.get(pos) != n]
    assert not missing, (f'{len(missing)} partial concrete tiles are not in the full concrete blueprint under the same name, '
                         f'e.g. {sorted(missing)[:6]}')
    print(f'every one of the {len(partial)} partial concrete tiles is in the full concrete blueprint under the same name')
    for scenario in SCENARIOS:
        dst = os.path.join(HERE, 'ingame/data/scenarios', scenario, 'strings.lua')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w') as f:
            f.write('return {\n' + ',\n'.join(rows) + '\n}\n')
        print('wrote', os.path.relpath(dst))


if __name__ == '__main__':
    main()
