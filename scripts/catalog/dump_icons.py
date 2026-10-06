#!/usr/bin/env python3
"""Pack the game's own icons of items, fluids and recipes for the website.

The site puts an icon in front of every material and recipe it lists. The game builds many icons from layers (oil
cracking, barrel filling...), so this takes the images the game itself dumps with --dump-icon-sprites instead of
redrawing them. Icons that look the same (a recipe and the item it makes) share one file. The result is committed,
because the CI has no game: catalog/vanilla-icons/*.webp (64x64, lossless) and catalog/vanilla-icons.json (prototype
kind -> name -> file). site/build.py packs the ones a page shows into one small sprite per page.

Run catalog/dump_icons.sh, which runs the game with the base mod only and then this script with the repository's
.venv. Re-run it with the Pillow version pinned in site/requirements.txt: another version can encode the same pixels
to different bytes and rewrite every file in git.

usage:
  .venv/bin/python scripts/catalog/dump_icons.py <script-output dir of the dump> [<catalog dir>]
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

SIZE = 64
KINDS = ('item', 'fluid', 'recipe')  # a file shared by several prototypes is named after the first one in this order
FILE_NAME = re.compile(r'(item|fluid|recipe)-[a-z0-9_-]+\.webp')  # the same pattern site/build.py accepts


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
            file_name = f'{kind}-{name}.webp'
            if not FILE_NAME.fullmatch(file_name):  # before the name becomes a path
                sys.exit(f'{file_name}: a prototype name that site/build.py would refuse as a file name')
            path = dump / kind / f'{name}.png'
            if not path.exists():
                sys.exit(f'{path} is missing: the dump does not match vanilla-prototypes.json')
            image = Image.open(path).convert('RGBA')
            if image.width > SIZE or image.height > SIZE:
                sys.exit(f'{path} is {image.width}x{image.height}, larger than {SIZE}x{SIZE}: it would be cropped')
            if image.size != (SIZE, SIZE):  # the three wire icons are 56 px: centre them, as the game draws them
                canvas = Image.new('RGBA', (SIZE, SIZE))
                canvas.paste(image, ((SIZE - image.width) // 2, (SIZE - image.height) // 2))
                image = canvas
            digest = hashlib.sha256(image.tobytes()).hexdigest()
            if digest not in by_pixels:
                by_pixels[digest] = file_name
                files[file_name] = image
            index[kind][name] = by_pixels[digest]
    # write next to the final folder and swap at the end, so a failure leaves the committed icons and index untouched
    out, tmp = catalog / 'vanilla-icons', catalog / 'vanilla-icons.tmp'
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    try:
        for name, image in files.items():
            image.save(tmp / name, 'WEBP', lossless=True, quality=100, method=6)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)  # a failed save leaves nothing behind in the repository
        raise
    shutil.rmtree(out)  # no ignore_errors: a folder that cannot be removed must stop the run, not the rename
    tmp.rename(out)
    (catalog / 'vanilla-icons.json').write_text(
        json.dumps(index, indent=1, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    total = sum(p.stat().st_size for p in out.iterdir())
    print(f'saved {len(files)} icons ({total / 1e6:.2f} MB) for '
          + ', '.join(f'{len(index[k])} {k}s' for k in KINDS) + f' in {out}')


if __name__ == '__main__':
    main()
