#!/usr/bin/env python3
"""Pack the game's own icons of items, fluids and recipes for the website.

The site puts an icon in front of every material and recipe it lists. The game builds many icons from layers (oil
cracking, barrel filling...), so this takes the images the game itself dumps with --dump-icon-sprites instead of
redrawing them. Icons that look the same (a recipe and the item it makes) share one file. The result is committed,
because the CI has no game: catalog/vanilla-icons/*.webp (64x64, lossless) and catalog/vanilla-icons.json (prototype
name -> file, per kind). site/build.py packs the ones a page shows into one small sprite.

Run catalog/dump_icons.sh, which runs the game with the base mod only and then this script. Needs Pillow.

usage:
  python3 scripts/catalog/dump_icons.py <script-output dir of the dump> [<catalog dir>]
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

SIZE = 64
KINDS = ('item', 'fluid', 'recipe')  # a file shared by several prototypes is named after the first one in this order


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dump = Path(sys.argv[1])
    catalog = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent
    protos = json.loads((catalog / 'vanilla-prototypes.json').read_text(encoding='utf-8'))
    index, files, by_pixels = {}, {}, {}
    for kind in KINDS:
        index[kind] = {}
        for name in sorted(protos[kind]):
            path = dump / kind / f'{name}.png'
            if not path.exists():
                sys.exit(f'{path} is missing: the dump does not match vanilla-prototypes.json')
            image = Image.open(path).convert('RGBA')
            if image.size != (SIZE, SIZE):
                image = image.resize((SIZE, SIZE), Image.LANCZOS)  # the three wire icons are 56 px in the game data
            digest = hashlib.sha256(image.tobytes()).hexdigest()
            if digest not in by_pixels:
                by_pixels[digest] = f'{kind}-{name}.webp'
                files[by_pixels[digest]] = image
            index[kind][name] = by_pixels[digest]
    out = catalog / 'vanilla-icons'
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    for name, image in files.items():
        image.save(out / name, 'WEBP', lossless=True, quality=100, method=6)
    (catalog / 'vanilla-icons.json').write_text(
        json.dumps(index, indent=1, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    total = sum(p.stat().st_size for p in out.iterdir())
    print(f'saved {len(files)} icons ({total / 1e6:.2f} MB) for '
          + ', '.join(f'{len(index[k])} {k}s' for k in KINDS) + f' in {out}')


if __name__ == '__main__':
    main()
