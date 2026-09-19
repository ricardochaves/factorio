"""Export the city block blueprints as a Lua table for the scenarios city-test and city-shot.

usage: python3 scripts/export_city.py
Writes strings.lua next to each scenario's control.lua (generated, git-ignored). Besides each blueprint string it
carries the numbers the scenario must find in the game (entities and tiles by name, wires by kind, size), counted here
from the decoded JSON, so the game run is checked against an independent count.
"""
import os
import re
import sys
from collections import Counter

import bp

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(HERE, '../blueprints/city-block-100x100')
SCENARIOS = ['city-test', 'city-shot']
VARIANTS = ['partial-concrete', 'full-concrete']   # simplest first, as listed in blueprint.toml
WIRE_KINDS = {1: 'red', 2: 'green', 5: 'copper'}   # wire connector ids in the blueprint JSON
STRING = re.compile(r'0[A-Za-z0-9+/=]+')           # a blueprint string is the version byte plus base64: safe in a Lua literal


def lua_counts(counter):
    return '{' + ', '.join('[%r]=%d' % (k, v) for k, v in sorted(counter.items())) + '}'


def main():
    rows = []
    for name in VARIANTS:
        text = open(os.path.join(FOLDER, name + '.txt')).read().strip()
        assert STRING.fullmatch(text), f'{name}: not a plain blueprint string'
        b = bp.decode(text)['blueprint']
        ents, tiles = b['entities'], b['tiles']
        grid = b['snap-to-grid']
        assert b.get('absolute-snapping') and grid == {'x': 100, 'y': 100}, 'expected a 100x100 absolute grid'
        wires = Counter(WIRE_KINDS[w[1]] for w in b['wires'])   # KeyError: a wire kind this test does not know
        rows.append('{name=%r, label=%r, entities=%s, tiles=%s, wires=%s, n_entities=%d, n_tiles=%d, n_wires=%d, cell=%d,\n bp="%s"}' % (
            name, b['label'], lua_counts(Counter(e['name'] for e in ents)), lua_counts(Counter(t['name'] for t in tiles)),
            lua_counts(wires), len(ents), len(tiles), len(b['wires']), grid['x'], text))
        print(f'{name:16} {len(ents)} entities, {len(tiles)} tiles, {len(b["wires"])} wires {dict(wires)}')
    for scenario in SCENARIOS:
        dst = os.path.join(HERE, 'ingame/data/scenarios', scenario, 'strings.lua')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w') as f:
            f.write('return {\n' + ',\n'.join(rows) + '\n}\n')
        print('wrote', os.path.relpath(dst))


if __name__ == '__main__':
    main()
