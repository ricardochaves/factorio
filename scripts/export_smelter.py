"""Export the stone brick smelter blueprint as a Lua table for the scenario smelter-test.

usage: python3 scripts/export_smelter.py
Writes strings.lua next to the scenario's control.lua (generated, git-ignored). Besides the blueprint string it carries
the numbers the scenario must find in the game (entities by name, modules by item), counted here from the decoded JSON,
so the game run is checked against an independent count. It also refuses a blueprint whose stone input or brick output
does not fit how the scenario feeds and drains it: the input is the express belt with the largest y and must face north,
the output is the express underground belt with the smallest y and must be a north-facing exit. It also refuses a tie
at either end, anything but exactly one substation (the scenario wires a second one to it) and fewer than four electric
furnaces (the scenario reads the fourth).
"""
import os
import re
from collections import Counter

import bp

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = 'stone-brick-smelter'
SCENARIO = 'smelter-test'
STRING = re.compile(r'0[A-Za-z0-9+/=]+')   # a blueprint string is the version byte plus base64: safe in a Lua literal


def lua_counts(counter):
    return '{' + ', '.join('[%r]=%d' % (k, v) for k, v in sorted(counter.items())) + '}'


def main():
    text = open(os.path.join(HERE, '../blueprints', FOLDER, FOLDER + '.txt')).read().strip()
    assert STRING.fullmatch(text), 'not a plain blueprint string'
    b = bp.decode(text)['blueprint']
    ents = b['entities']
    modules = Counter()
    for e in ents:
        for request in e.get('items', []):
            modules[request['id']['name']] += sum(s.get('count', 1) for s in request['items']['in_inventory'])
    belts = [e for e in ents if e['name'] == 'express-transport-belt']
    entry = max(belts, key=lambda e: e['position']['y'])
    assert entry.get('direction', 0) == 0, 'the stone input belt must face north'
    assert sum(e['position']['y'] == entry['position']['y'] for e in belts) == 1, 'two belts share the southern end'
    exits = [e for e in ents if e['name'] == 'express-underground-belt']
    leave = min(exits, key=lambda e: e['position']['y'])
    assert leave.get('type') == 'output' and leave.get('direction', 0) == 0, \
        'the brick output must be a north-facing exit'
    assert sum(e['position']['y'] == leave['position']['y'] for e in exits) == 1, \
        'two undergrounds share the northern end'
    # The scenario connects a second substation to the design's one substation and reads the fourth furnace.
    assert sum(e['name'] == 'substation' for e in ents) == 1, 'expected exactly one substation'
    assert sum(e['name'] == 'electric-furnace' for e in ents) >= 4, 'expected at least four electric furnaces'
    row = 'return {label=%r, n_entities=%d, entities=%s, modules=%s,\n bp="%s"}\n' % (
        b['label'], len(ents), lua_counts(Counter(e['name'] for e in ents)), lua_counts(modules), text)
    path = os.path.join(HERE, 'ingame/data/scenarios', SCENARIO, 'strings.lua')
    with open(path, 'w') as f:
        f.write(row)
    print(f'{b["label"]}: {len(ents)} entities, modules {dict(modules)}; wrote {os.path.relpath(path, HERE)}')


if __name__ == '__main__':
    main()
