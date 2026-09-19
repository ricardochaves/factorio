#!/usr/bin/env python3
"""In-game check of the blueprint strings the website publishes (build/site/files/).

Picks every sub-book, a sample of single blueprints (the 2 to 3 variants, the largest one and a spread of pairs) from
each balancer book, and every single blueprint file, then writes them with the expected blueprint and entity counts to
scenario site-import. Run the scenario headless with run_site_import.sh; it imports each string in the game and
compares.

usage (from scripts/, after site/build.py):
  python3 site_import_test.py && ./run_site_import.sh
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bp  # noqa: E402

FILES = HERE.parent / 'build' / 'site' / 'files'
OUT = HERE / 'ingame' / 'data' / 'scenarios' / 'site-import' / 'strings.lua'
SAMPLE = ['1-1', '1-24', '2-3-long', '2-3-wide', '4-8', '8-8', '9-9', '12-5', '16-16', '24-24', '24-1', '5-7']


def case(path):
    text = path.read_text(encoding='utf-8').strip()
    data = bp.decode(text)
    prints = list(bp.walk(data))
    return {'name': str(path.relative_to(FILES)), 'str': text, 'prints': len(prints),
            'entities': sum(len(b.get('entities', [])) for _, b in prints)}


def main():
    if not FILES.is_dir():
        sys.exit(f'{FILES} not found: run site/build.py first')
    cases = []
    for folder in sorted(p for p in FILES.iterdir() if p.is_dir()):
        for path in sorted(folder.glob('*.txt')):
            if bp.kind(bp.decode(path.read_text(encoding='utf-8'))) == 'blueprint':
                cases.append(case(path))              # a single-blueprint file of the catalog
        for variant in sorted(p for p in folder.iterdir() if p.is_dir()):
            names = {p.stem for p in variant.glob('*.txt')}
            books = sorted(n for n in names if '-' not in n)
            largest = max((n for n in names if '-' in n), key=lambda n: (variant / f'{n}.txt').stat().st_size)
            for name in books + [s for s in SAMPLE if s in names] + [largest]:
                cases.append(case(variant / f'{name}.txt'))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        f.write('return {\n')
        for c in cases:
            f.write(f'  {{name = "{c["name"]}", prints = {c["prints"]}, entities = {c["entities"]}, str = "{c["str"]}"}},\n')
        f.write('}\n')
    print(f'wrote {len(cases)} strings to {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
