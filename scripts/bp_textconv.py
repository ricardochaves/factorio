"""git textconv driver: prints a blueprint string as line-oriented JSON so `git diff` shows entity-level changes.

One header line per blueprint/book (its path of labels), one line with its metadata, then one line per entity,
tile and wire. Setup once per clone (the matching .gitattributes rule is committed):
    git config diff.factorio-blueprint.textconv "python3 scripts/bp_textconv.py"
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bp

LISTS = ('entities', 'tiles', 'wires', 'blueprints', 'schedules')


def line(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def dump(o, path, out):
    k = bp.kind(o)
    b = o[k]
    here = path + (str(b.get('label') or ''),)
    out.write('### %s: %s\n' % (k, ' / '.join(here)))
    out.write(line({x: v for x, v in b.items() if x not in LISTS}) + '\n')
    for key, tag in (('entities', 'entity'), ('tiles', 'tile'), ('wires', 'wire'), ('schedules', 'schedule')):
        for item in b.get(key, []):
            out.write('%s %s\n' % (tag, line(item)))
    for child in b.get('blueprints', []):
        dump(child, here, out)


def main(path):
    raw = open(path).read()
    try:
        obj = bp.decode(raw)
    except Exception:          # not a blueprint string: show it unchanged
        sys.stdout.write(raw)
        return
    dump(obj, (), sys.stdout)


if __name__ == '__main__':
    main(sys.argv[1])
