"""Blueprint string encode/decode helpers."""
import base64, zlib, json

def decode(s):
    s = s.strip()
    return json.loads(zlib.decompress(base64.b64decode(s[1:])))

def encode(obj):
    raw = json.dumps(obj, separators=(',', ':')).encode()
    return '0' + base64.b64encode(zlib.compress(raw, 9)).decode()

def kind(o):
    for k in ('blueprint_book', 'blueprint', 'upgrade_planner', 'deconstruction_planner'):
        if k in o:
            return k
    raise ValueError('unknown item: %s' % list(o))

def walk(o, path=()):
    """Yield (path_labels, blueprint_dict) for every blueprint in the tree."""
    k = kind(o)
    b = o[k]
    if k == 'blueprint':
        yield path + (b.get('label'),), b
    elif k == 'blueprint_book':
        for c in b.get('blueprints', []):
            yield from walk(c, path + (b.get('label'),))

def tree(o, dep=0, out=None):
    k = kind(o); b = o[k]
    n = len(b.get('entities', [])) if k == 'blueprint' else len(b.get('blueprints', []))
    print('  ' * dep + f"[{k[:9]}] {b.get('label')!r} n={n}")
    if k == 'blueprint_book':
        for c in b['blueprints']:
            tree(c, dep + 1)
