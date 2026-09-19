#!/usr/bin/env python3
"""Extract the in-game names of the base game's items, entities, recipes and fluids (English, Portuguese, Spanish).

The site shows materials and recipes with the names the game itself uses. They come from the game's locale files, so
this runs on a machine with Factorio installed and writes catalog/vanilla-locale.json, which is committed (the CI has
no game). Only names of prototypes listed in catalog/vanilla-prototypes.json are kept. Re-run after a Factorio update.

usage:
  python3 scripts/catalog/dump_locale.py [--data-dir <Factorio data dir>]
The data dir defaults to the one next to $FACTORIO_BIN (or the Steam install on macOS).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANGS = ('en', 'pt-BR', 'es-ES')
DEFAULT_BIN = '~/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio'
REF = re.compile(r'__(ITEM|ENTITY|FLUID|RECIPE|TILE)__([a-z0-9_-]+)__')
REF_SECTION = {'ITEM': 'item-name', 'ENTITY': 'entity-name', 'FLUID': 'fluid-name', 'RECIPE': 'recipe-name',
               'TILE': 'tile-name'}


def parse_cfg(path):
    sections, current = {}, None
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line[0] in ';#':
            continue
        if line.startswith('[') and line.endswith(']'):
            current = sections.setdefault(line[1:-1], {})
        elif '=' in line and current is not None:
            key, value = line.split('=', 1)
            current[key.strip()] = value.strip()
    return sections


def resolver(cfg):
    def lookup(section, key, depth=0):
        value = cfg.get(section, {}).get(key)
        if value is None or depth > 5:
            return value
        return REF.sub(lambda m: lookup(REF_SECTION[m.group(1)], m.group(2), depth + 1) or m.group(0), value)
    return lookup


def names_for(cfg, protos):
    get = resolver(cfg)

    def first(*pairs):
        for section, key in pairs:
            value = get(section, key)
            if value:
                return value
        return None

    def barrel(section, key, name, prefix=''):
        """Filled barrels are generated at runtime: their names are a template with the fluid name as __1__."""
        fluid = name[len(prefix):-len('-barrel')] if name.startswith(prefix) and name.endswith('-barrel') else None
        template = get(section, key)
        if fluid in protos['fluid'] and template and get('fluid-name', fluid):
            return template.replace('__1__', get('fluid-name', fluid))
        return None

    out = {'entity': {}, 'item': {}, 'recipe': {}, 'fluid': {}}
    for name in protos['entity']:
        out['entity'][name] = first(('entity-name', name), ('item-name', name))
    for name in protos['item']:
        out['item'][name] = (first(('item-name', name), ('entity-name', name), ('equipment-name', name),
                                   ('tile-name', name))
                             or barrel('item-name', 'filled-barrel', name))
    for name in protos['fluid']:
        out['fluid'][name] = first(('fluid-name', name))
    for name in protos['recipe']:
        out['recipe'][name] = (first(('recipe-name', name), ('item-name', name), ('fluid-name', name),
                                     ('entity-name', name), ('equipment-name', name))
                               or barrel('recipe-name', 'empty-filled-barrel', name, 'empty-')
                               or barrel('recipe-name', 'fill-barrel', name))
    for kind in out:
        out[kind] = {k: v for k, v in sorted(out[kind].items()) if v}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    default_bin = Path(os.path.expanduser(os.environ.get('FACTORIO_BIN', DEFAULT_BIN)))
    ap.add_argument('--data-dir', type=Path, default=default_bin.parent.parent / 'data')
    ap.add_argument('--prototypes', type=Path, default=HERE / 'vanilla-prototypes.json')
    ap.add_argument('--out', type=Path, default=HERE / 'vanilla-locale.json')
    args = ap.parse_args()
    protos = json.loads(args.prototypes.read_text(encoding='utf-8'))
    result = {'factorio_version': protos.get('factorio_version')}
    for lang in LANGS:
        cfg_path = args.data_dir / 'base' / 'locale' / lang / 'base.cfg'
        if not cfg_path.is_file():
            sys.exit(f'{cfg_path} not found (pass --data-dir)')
        result[lang] = names_for(parse_cfg(cfg_path), protos)
    missing = {k: len(protos[k]) - len(result['en'][k]) for k in ('entity', 'item', 'recipe', 'fluid')}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print(f'wrote {args.out} (prototypes without an English name: {missing})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
