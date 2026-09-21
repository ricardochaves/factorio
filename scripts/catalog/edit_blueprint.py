"""Helpers for correcting a blueprint string: decode it to JSON that you can edit, and list what differs between two strings.

  python3 scripts/catalog/edit_blueprint.py decode <bp.txt> --out <bp.json>   write the decoded JSON, two-space indented
  python3 scripts/catalog/edit_blueprint.py diff <before.txt> <after.txt>      list every path whose value differs

The way back is scripts/catalog/extract_blueprint.py: given the edited JSON file it encodes the string, proves that it decodes
and reports what it holds. `decode` never overwrites --out, accepts --out once, refuses a path with a `..` component
(outpath.py) and refuses a string whose top-level object holds a key other than the four kinds, so that a crafted string cannot
leave a file that another tool reads as its configuration. `diff` prints `<path>: <before> -> <after>` for each difference (`-`
stands for a value that is missing on that side), then `N difference(s)` or `identical`, and exits 0 whenever both strings
decode. It pairs the items of a list by the first of `entity_number` (entities), `index` (icons and the blueprints of a book)
and `position` (tiles, and entities that have no usable entity_number) that every item has and no two share, so that removing
an entity does not shift the paths of the others, and it compares a list of number lists (the wires) as rows, whatever their
order, counting a repeated row. Any other list is compared by position, and a `note:` line says when a list of entities had to
be compared that way because an `entity_number` is missing or repeated and no other key pairs them. Numbers compare by value,
so 1 and 1.0 are the same, in wire rows and in positions too, and paired items are listed in natural order (entity_number 2
before 10; a minus sign is part of the text). A value is cut to 80 characters (two long strings that differ show a window
around their first difference) and a path to 300, keeping its end; at most 200 difference lines and 200 note lines are printed,
and the rest is counted as `... and N more`. Invisible characters are written as \\u escapes. A file that is missing, or a
string that does not decode, exits 2 with the reason. Standard library only (Python 3.11+).
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bp  # noqa: E402  (scripts/bp.py)
import extract_blueprint as ex  # noqa: E402  (its reader and its bounded decoder refuse oversized input)
from outpath import OutPath  # noqa: E402  (scripts/catalog/outpath.py)

MAX_LINES = 200
MAX_VALUE = 80
MAX_PATH = 300
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


def is_nan(v):
    return isinstance(v, float) and v != v


def canon(v):
    """A number as it compares: 1.0 is 1."""
    return int(v) if isinstance(v, float) and v.is_integer() else v


def natural(label):
    """A sort key that puts entity_number=2 before entity_number=10 and settles a tie by the text itself."""
    return [int(t) if i % 2 else t for i, t in enumerate(re.split(r'(\d+)', label))], label


def label_number(item, name):
    v = item.get(name)
    return f'{name}={v}' if isinstance(v, int) and not isinstance(v, bool) else None


def label_position(item):
    p = item.get('position')
    if isinstance(p, dict) and is_number(p.get('x')) and is_number(p.get('y')):
        return f'position=({canon(p["x"])}, {canon(p["y"])})'
    return None


LABELS = (('entity_number', lambda i: label_number(i, 'entity_number')), ('index', lambda i: label_number(i, 'index')),
          ('position', label_position))


def keyed(items):
    """(kind, {label: item}) when every item of the list is an object with the same kind of key and no two share it, or None."""
    if not items or not all(isinstance(i, dict) for i in items):
        return None
    for kind, label in LABELS:
        labels = [label(i) for i in items]
        if None not in labels and len(set(labels)) == len(labels):
            return kind, dict(zip(labels, items))
    return None


def pair(a, b):
    """(kind, {label: item} of a, {label: item} of b) when both lists pair by the same kind of key; an empty list pairs with
    any."""
    ka, kb = keyed(a), keyed(b)
    if ka and kb and ka[0] == kb[0]:
        return ka[0], ka[1], kb[1]
    if not a and kb:
        return kb[0], {}, kb[1]
    if not b and ka:
        return ka[0], ka[1], {}
    return None


def rows(items):
    """True for a list whose items are all lists of numbers, like the wires of a blueprint (an empty list counts)."""
    return all(isinstance(i, list) and all(is_number(x) for x in i) for i in items)


def key_text(k):
    """A dictionary key as it appears in a path: plain words as they are, anything else quoted."""
    return k if PLAIN_KEY.fullmatch(k) else json.dumps(k, ensure_ascii=False)


def compare(a, b, path, out, notes):
    """Append (path, before, after) to `out` for every leaf or subtree that differs, and a sentence to `notes` for a list that
    could not be paired the way its items suggest."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f'{path}.{key_text(k)}' if path else key_text(k)
            if k not in b:
                out.append((p, a[k], MISSING))
            elif k not in a:
                out.append((p, MISSING, b[k]))
            else:
                compare(a[k], b[k], p, out, notes)
    elif isinstance(a, list) and isinstance(b, list):
        paired = pair(a, b)
        if paired:
            _, by_a, by_b = paired
            for label in sorted(set(by_a) | set(by_b), key=natural):
                p = f'{path}[{label}]'
                if label not in by_b:
                    out.append((p, by_a[label], MISSING))
                elif label not in by_a:
                    out.append((p, MISSING, by_b[label]))
                else:
                    compare(by_a[label], by_b[label], p, out, notes)
        elif (a or b) and rows(a) and rows(b):
            count_a = Counter(json.dumps([canon(x) for x in r]) for r in a)
            count_b = Counter(json.dumps([canon(x) for x in r]) for r in b)
            for row in sorted(set(count_a) | set(count_b), key=natural):
                if count_a[row] > count_b[row]:
                    out.append((f'{path}[{row}]', json.loads(row), MISSING))
                elif count_b[row] > count_a[row]:
                    out.append((f'{path}[{row}]', MISSING, json.loads(row)))
        else:
            if a and b and any(isinstance(i, dict) and 'entity_number' in i for i in a + b):
                where = path or '(top level)'
                notes.append(f'{where}: an entity_number is missing or repeated, so the list is compared by position')
            for i in range(max(len(a), len(b))):
                p = f'{path}[{i}]'
                if i >= len(b):
                    out.append((p, a[i], MISSING))
                elif i >= len(a):
                    out.append((p, MISSING, b[i]))
                else:
                    compare(a[i], b[i], p, out, notes)
    elif is_number(a) and is_number(b):
        if a != b and not (is_nan(a) and is_nan(b)):
            out.append((path, a, b))
    elif type(a) is not type(b) or a != b:
        out.append((path, a, b))


def clip(text):
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE - 3] + '...'


def clip_path(path):
    """A path is kept whole up to 300 characters, and beyond that its start and its end stay: the end says what changed."""
    return path if len(path) <= MAX_PATH else path[:100] + '...' + path[-(MAX_PATH - 103):]


def show(v):
    return '-' if v is MISSING else clip(json.dumps(v, ensure_ascii=False))


def excerpts(a, b):
    """Two strings that differ, each cut to a window that starts a little before their first difference."""
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    start, width = max(0, first - 20), MAX_VALUE - 20

    def window(s):
        text = json.dumps(s[start:start + width], ensure_ascii=False)
        return ('...' if start else '') + text + ('...' if start + width < len(s) else '')
    return window(a), window(b)


def line(path, a, b):
    """The output line for one difference, with invisible characters escaped."""
    if isinstance(a, str) and isinstance(b, str) and (len(a) > MAX_VALUE or len(b) > MAX_VALUE):
        left, right = excerpts(a, b)
    else:
        left, right = show(a), show(b)
    return ex.make_visible(f'{clip_path(path)}: {left} -> {right}')


def cmd_decode(args):
    obj = load(args.file)
    # The decoded object is written as it is, so a crafted string must not be able to bring keys that another tool reads as
    # its own configuration (hooks, mcpServers, ...): a real string holds exactly one of the four kinds at the top.
    extra = sorted(str(k) for k in obj if k not in ex.ALL_KINDS)
    if extra:
        keys = ', '.join(extra)[:120]
        raise ex.Refuse(f'the string decodes to an object with other top-level keys ({keys}); nothing is written')
    if not args.out.parent.is_dir():
        raise ex.Refuse(f'{args.out.parent} is not a directory')
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
    found, notes = [], []
    try:
        compare(before, after, '', found, notes)
    except RecursionError:
        raise ex.Refuse('the blueprints are nested too deeply to compare') from None
    for note in notes[:MAX_LINES]:
        print(ex.make_visible('note: ' + clip_path(note)))
    if len(notes) > MAX_LINES:
        print(f'... and {len(notes) - MAX_LINES} more')
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
    dec.add_argument('file', metavar='bp.txt', help='a file that holds one blueprint string')
    dec.add_argument('--out', action=OutPath, required=True, help='where to write the JSON (must not exist)')
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
