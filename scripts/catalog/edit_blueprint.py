"""Helpers for correcting a blueprint string: decode it to JSON that you can edit, and list what differs between two strings.

  python3 scripts/catalog/edit_blueprint.py decode <bp.txt> --out <bp.json>   write the decoded JSON, two-space indented
  python3 scripts/catalog/edit_blueprint.py diff <before.txt> <after.txt>      list every path whose value differs

The way back is scripts/catalog/extract_blueprint.py: given the edited JSON file it encodes the string, proves that it decodes
and reports what it holds. `decode` never overwrites --out. `diff` prints `<path>: <before> -> <after>` for each difference
(`-` stands for a value that is missing on that side), then `N difference(s)` or `identical`, and exits 0 whenever both strings
decode. It pairs the items of a list by `entity_number` (or by `index`, for icons and for the blueprints of a book) when every item
has one, so that removing an entity does not shift the paths of the others; any other list is compared by position. Numbers compare
by value, so 1 and 1.0 are the same. A path or a value is cut to 80 characters (two long strings that differ show a window around
their first difference), at most 200 lines are printed and the rest is counted as `... and N more`. Invisible characters are written
as \\u escapes. A file that is missing, or a string that does not decode, exits 2 with the reason.
Standard library only (Python 3.11+).
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bp  # noqa: E402  (scripts/bp.py)
import extract_blueprint as ex  # noqa: E402  (its reader and its bounded decoder refuse oversized input)

MAX_LINES = 200
MAX_VALUE = 80
KEYS = ('entity_number', 'index')  # what pairs the items of a list: entities, and icons and the blueprints of a book
PLAIN_KEY = re.compile(r'[A-Za-z0-9_-]+')
MISSING = object()


def load(path):
    """Decode the blueprint string in the file at `path` into its JSON object."""
    p = Path(path)
    if not p.is_file():
        raise ex.Refuse(f'{path} is not a file')
    text = ''.join(ex.read_file(p, ex.MAX_BYTES).split())
    try:
        return ex.describe(text)[0]
    except Exception as e:  # noqa: BLE001 - whatever is wrong with the text, the reason is what the caller needs
        raise ex.Refuse(f'{path} does not hold a blueprint, a book or a planner that decodes ({type(e).__name__}: {e})') from e


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def key_of(items):
    """The key that identifies every item of a list of objects, when each item has it and no two share its value."""
    for key in KEYS:
        if items and all(isinstance(i, dict) and key in i for i in items):
            values = [i[key] for i in items]
            if all(isinstance(v, int) and not isinstance(v, bool) for v in values) and len(set(values)) == len(values):
                return key
    return None


def key_text(k):
    """A dictionary key as it appears in a path: plain words as they are, anything else quoted."""
    return k if PLAIN_KEY.fullmatch(k) else json.dumps(k, ensure_ascii=False)


def compare(a, b, path, out):
    """Append (path, before, after) to `out` for every leaf or subtree that differs."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f'{path}.{key_text(k)}' if path else key_text(k)
            if k not in b:
                out.append((p, a[k], MISSING))
            elif k not in a:
                out.append((p, MISSING, b[k]))
            else:
                compare(a[k], b[k], p, out)
    elif isinstance(a, list) and isinstance(b, list):
        key = key_of(a)
        if key and key == key_of(b):
            by_a, by_b = {i[key]: i for i in a}, {i[key]: i for i in b}
            for v in sorted(set(by_a) | set(by_b)):
                p = f'{path}[{key}={v}]'
                if v not in by_b:
                    out.append((p, by_a[v], MISSING))
                elif v not in by_a:
                    out.append((p, MISSING, by_b[v]))
                else:
                    compare(by_a[v], by_b[v], p, out)
            return
        for i in range(max(len(a), len(b))):
            p = f'{path}[{i}]'
            if i >= len(b):
                out.append((p, a[i], MISSING))
            elif i >= len(a):
                out.append((p, MISSING, b[i]))
            else:
                compare(a[i], b[i], p, out)
    elif is_number(a) and is_number(b):
        if a != b:
            out.append((path, a, b))
    elif type(a) is not type(b) or a != b:
        out.append((path, a, b))


def clip(text):
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE - 3] + '...'


def show(v):
    return '-' if v is MISSING else clip(json.dumps(v, ensure_ascii=False))


def excerpts(a, b):
    """Two strings that differ, each cut to a window that starts a little before their first difference."""
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    start, width = max(0, first - 20), MAX_VALUE - 20

    def window(s):
        return ('...' if start else '') + json.dumps(s[start:start + width], ensure_ascii=False) + ('...' if start + width < len(s) else '')
    return window(a), window(b)


def line(path, a, b):
    """The output line for one difference, with invisible characters escaped."""
    if isinstance(a, str) and isinstance(b, str) and (len(a) > MAX_VALUE or len(b) > MAX_VALUE):
        left, right = excerpts(a, b)
    else:
        left, right = show(a), show(b)
    return ex.make_visible(f'{clip(path)}: {left} -> {right}')


def cmd_decode(args):
    obj = load(args.string)
    if not args.out.parent.is_dir():
        raise ex.Refuse(f'{args.out.parent} does not exist')
    # Built before the file exists, so that a failure while building leaves nothing behind.
    data = (ex.make_visible(json.dumps(obj, indent=2, ensure_ascii=False)) + '\n').encode('utf-8')
    try:
        with open(args.out, 'xb') as f:  # 'x' fails when the file exists: nothing is overwritten
            f.write(data)
    except FileExistsError:
        raise ex.Refuse(f'{args.out} already exists; it is never overwritten') from None
    print(f'wrote {args.out} ({bp.kind(obj)}, {len(data)} bytes)')
    return 0


def cmd_diff(args):
    before, after = load(args.before), load(args.after)
    found = []
    try:
        compare(before, after, '', found)
    except RecursionError:
        raise ex.Refuse('the blueprints are nested too deeply to compare') from None
    for path, a, b in found[:MAX_LINES]:
        print(line(path, a, b))
    if len(found) > MAX_LINES:
        print(f'... and {len(found) - MAX_LINES} more')
    print(f'{len(found)} difference{"" if len(found) == 1 else "s"}' if found else 'identical')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='command', required=True)
    dec = sub.add_parser('decode', help='write the decoded JSON of a string')
    dec.add_argument('string', help='a file that holds one blueprint string')
    dec.add_argument('--out', type=Path, required=True, help='where to write the JSON (must not exist)')
    dec.set_defaults(run=cmd_decode)
    dif = sub.add_parser('diff', help='list what differs between two strings')
    dif.add_argument('before', help='a file that holds the string as it was')
    dif.add_argument('after', help='a file that holds the string as it is now')
    dif.set_defaults(run=cmd_diff)
    args = ap.parse_args()
    try:
        return args.run(args)
    except ex.Refuse as e:
        print(f'refused: {e}', file=sys.stderr)
    except Exception as e:  # noqa: BLE001 - every failure must end as exit 2 with a reason, never a traceback
        print(f'refused: unexpected {type(e).__name__}: {e}', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
