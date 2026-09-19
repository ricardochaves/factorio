"""Belt tier selection (env FBTIER = blue | red | yellow). Blue is the default and the original behaviour."""
import os
TIER = os.environ.get('FBTIER', 'blue')
PREFIX = {'blue': 'express-', 'red': 'fast-', 'yellow': ''}[TIER]
BELT, UG, SPL, LOADER = PREFIX + 'transport-belt', PREFIX + 'underground-belt', PREFIX + 'splitter', PREFIX + 'loader'
UG_MAX = {'blue': 9, 'red': 7, 'yellow': 5}[TIER]
ITEMS_PER_SEC = {'blue': 45, 'red': 30, 'yellow': 15}[TIER]
SUFFIX = '' if TIER == 'blue' else '_' + TIER
TITLE = {'blue': 'Blue', 'red': 'Red', 'yellow': 'Yellow'}[TIER]
SIGNAL = 'signal-' + TIER
BELT_WORD = {'blue': 'express', 'red': 'fast', 'yellow': 'basic (yellow)'}[TIER]
RANK = {'yellow': 0, 'red': 1, 'blue': 2}

def retier_name(name):
    for kind in ('transport-belt', 'underground-belt', 'splitter'):
        if name.endswith(kind):
            return PREFIX + kind
    return name

def retier_blueprint(b):
    """Copy of a blueprint dict with every belt entity renamed to the selected tier."""
    b2 = dict(b)
    b2['entities'] = [dict(e, name=retier_name(e['name'])) for e in b.get('entities', [])]
    return b2
