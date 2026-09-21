"""Helpers for correcting a blueprint string: decode it to JSON that you can edit, and list what differs between two strings.

  python3 scripts/catalog/edit_blueprint.py decode <bp.txt> --out <bp.json>   write the decoded JSON, two-space indented
  python3 scripts/catalog/edit_blueprint.py diff <before.txt> <after.txt>      list every path whose value differs

The way back is scripts/catalog/extract_blueprint.py: given the edited JSON file it encodes the string, proves that it decodes
and reports what it holds. `decode` never overwrites --out. `diff` prints `<path>: <before> -> <after>` for each difference
(`-` stands for a value that is missing on that side), at most 200 lines, then `N difference(s)` or `identical`, and exits 0
whenever both strings decode. A file that is missing, or a string that does not decode, exits 2 with the reason.
Standard library only (Python 3.11+).
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import bp  # noqa: E402  (scripts/bp.py)
import extract_blueprint as ex  # noqa: E402  (its decoder refuses a compressed bomb)

MAX_LINES = 200
MAX_VALUE = 80
MISSING = object()


def load(path):
    """Decode the blueprint string in the file at `path` into its JSON object."""
    p = Path(path)
    if not p.is_file():
        raise ex.Refuse(f'{path} is not a file')
    if p.stat().st_size > ex.MAX_BYTES:
        raise ex.Refuse(f'{path} is larger than {ex.MAX_BYTES} bytes')
    text = ''.join(p.read_text(encoding='utf-8-sig').split())
    try:
        obj = ex.decode_bounded(text)
    except Exception as e:  # noqa: BLE001 - whatever is wrong with the text, the reason is what the caller needs
        raise ex.Refuse(f'{path} does not hold a blueprint string that decodes ({type(e).__name__}: {e})') from e
    if not isinstance(obj, dict):
        raise ex.Refuse(f'{path} decodes to something that is not an object')
    bp.kind(obj)  # raises ValueError for anything that is not a blueprint, a book or a planner
    return obj


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def compare(a, b, path, out):
    """Append (path, before, after) to `out` for every leaf or subtree that differs."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f'{path}.{k}' if path else k
            if k not in b:
                out.append((p, a[k], MISSING))
            elif k not in a:
                out.append((p, MISSING, b[k]))
            else:
                compare(a[k], b[k], p, out)
    elif isinstance(a, list) and isinstance(b, list):
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


def show(v):
    if v is MISSING:
        return '-'
    text = json.dumps(v, ensure_ascii=False)
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE - 3] + '...'


def cmd_decode(args):
    obj = load(args.string)
    if not args.out.parent.is_dir():
        raise ex.Refuse(f'{args.out.parent} does not exist')
    try:
        with open(args.out, 'x', encoding='utf-8') as f:  # 'x' fails when the file exists: nothing is overwritten
            f.write(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
    except FileExistsError:
        raise ex.Refuse(f'{args.out} already exists; it is never overwritten') from None
    print(f'wrote {args.out} ({bp.kind(obj)}, {args.out.stat().st_size} bytes)')
    return 0


def cmd_diff(args):
    before, after = load(args.before), load(args.after)
    try:
        found = []
        compare(before, after, '', found)
    except RecursionError:
        raise ex.Refuse('the blueprints are nested too deeply to compare') from None
    for path, a, b in found[:MAX_LINES]:
        print(f'{path}: {show(a)} -> {show(b)}')
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
