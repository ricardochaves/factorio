#!/usr/bin/env python3
"""Validate the blueprint catalog and compute its numbers from the blueprint strings.

Each folder blueprints/<slug>/ holds the final blueprint string file(s), a blueprint.toml with the hand-written
metadata and the README in the site's three languages (README.md, README.en.md, README.es.md). Numbers (entities,
size, materials, recipes, blueprints per book) are never written by hand: this script computes them from the strings.

usage:
  python3 scripts/catalog/validate.py                          check everything, print the computed stats
  python3 scripts/catalog/validate.py --json build/catalog.json  also write the catalog index (build/ is git-ignored)
  python3 scripts/catalog/validate.py --readme                 also refresh the catalog table in README.md
Exit status is 1 when anything is wrong. Standard library only (Python 3.11+ for tomllib).
"""
import argparse
import hashlib
import json
import re
import sys
import tomllib
import unicodedata
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))  # site/build.py loads this file by path, so its own folder is not on sys.path
import bp  # noqa: E402  (scripts/bp.py)
from extract_blueprint import is_blank  # noqa: E402  (the characters that draw nothing although their category is visible)
from outpath import OutPath  # noqa: E402  (scripts/catalog/outpath.py)

CATEGORIES = {
    'belts': 'Belts', 'mining-smelting': 'Mining & smelting', 'oil': 'Oil processing', 'production': 'Production',
    'science': 'Science', 'power': 'Power', 'trains': 'Trains', 'bots': 'Logistic robots',
    'city-blocks': 'City blocks', 'circuits': 'Circuits',
    'defense': 'Defense', 'rocket': 'Rocket',
}
TEST_STATUS = {'in-game': 'in game', 'simulation': 'simulation only', 'untested': 'not tested'}
VIEWERS = {'nxm-matrix'}
IMAGE_EXT = {'.webp', '.png', '.jpg', '.jpeg'}
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')  # always matched with fullmatch: `$` would also accept a trailing newline
TAG = SLUG
VERSION_STR = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+')
SCHEMA = {  # key: (required, type)
    'title': (True, str), 'summary': (True, str), 'category': (True, str), 'tags': (True, list),
    'files': (True, list), 'test': (False, dict), 'images': (True, list), 'viewer': (False, str),
    'credits': (False, str), 'en': (True, dict), 'es': (True, dict),
}
# The site shows every text of an entry in Portuguese (the top-level keys and README.md), English and Spanish, and
# nothing falls back to another language, so every translation is required: the [en] / [es] tables (with `credits`
# whenever the entry has credits), the name_<lang> / alt_<lang> keys and README.<lang>.md.
TRANSLATION = {'title': (True, str), 'summary': (True, str), 'credits': (False, str)}
SUB_SCHEMA = {
    'files': {'name': (True, str), 'name_en': (True, str), 'name_es': (True, str), 'path': (True, str)},
    'images': {'path': (True, str), 'alt': (True, str), 'alt_en': (True, str), 'alt_es': (True, str)},
    'test': {'status': (True, str), 'game_version': (False, str), 'report': (False, str)},
    'en': TRANSLATION, 'es': TRANSLATION,
}
READMES = {'pt': 'README.md', 'en': 'README.en.md', 'es': 'README.es.md'}  # the entry's README in each site language
README_START, README_END = '<!-- catalog:start -->', '<!-- catalog:end -->'


SAFE_PATH = re.compile(r'[A-Za-z0-9][A-Za-z0-9._/-]*')  # a file named in blueprint.toml ends up in a link of the README table
MARKDOWN_SPECIAL = re.compile(r'([\\|\[\]<>`])')


EMOJI_SELECTORS = (0xFE0E, 0xFE0F)
# Characters that take an emoji selector (Unicode's emoji-variation-sequences.txt) although their category is not So: U+203C,
# U+2049, U+2139, U+2194, U+25FB to U+25FE, U+2934, U+2935, U+3030 and U+303D.
EMOJI_TEXT_BASES = tuple(chr(cp) for cp in (0x203C, 0x2049, 0x2139, 0x2194, 0x25FB, 0x25FC, 0x25FD, 0x25FE, 0x2934, 0x2935,
                                              0x3030, 0x303D))


def bad_chars(text):
    """The characters of `text` that draw nothing or reorder text, as U+XXXX: control characters other than tab and line
    breaks, format ones (bidirectional controls, zero-width characters, tags), private-use and surrogate ones, and the fillers
    and selectors that the extractor lists as blank. The emoji selectors U+FE0E and U+FE0F are allowed only right after a
    symbol above ASCII (category So, or one of the few emoji that are not), or after `#`, `*` or a digit that a keycap
    (U+20E3) follows: after any other character they could carry a bit that nobody sees. Unassigned characters are tested
    only through the extractor's list of reserved ones that draw nothing: which characters are unassigned depends on the
    Unicode version of the Python that runs the check."""
    found = set()
    for i, c in enumerate(text):
        if ord(c) in EMOJI_SELECTORS:
            before = text[i - 1] if i else ' '
            symbol = (ord(before) > 0x7F and unicodedata.category(before) == 'So') or before in EMOJI_TEXT_BASES
            keycap = before in '#*0123456789' and text[i + 1:i + 2] == chr(0x20E3)
            bad = not (symbol or keycap)
        else:
            category = unicodedata.category(c)
            bad = (category in ('Cf', 'Co', 'Cs', 'Zl', 'Zp') or (category == 'Cc' and c not in '\t\n\r') or is_blank(c))
        if bad:
            found.add(f'U+{ord(c):04X}')
    return sorted(found)


def strings_of(value, path):
    """(path, text) for every string inside a TOML value."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from strings_of(v, f'{path}.{k}' if path else str(k))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from strings_of(v, f'{path}[{i}]')


FENCE = re.compile(r' {0,3}(`{3,}|~{3,})')
HEADING = re.compile(r' {0,3}(#{1,6})(?:[ \t]|$)')
TABLE_RULE = re.compile(r' {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*')
CODE_SPAN = re.compile(r'(?<!`)(`+)(?!`)((?:(?!\n[ \t]*\n).)+?)(?<!`)\1(?!`)', re.S)  # never across a blank line
LINK_TARGET = re.compile(r'\]\(\s*<?([^\s)>]+)')


def table_cells(row):
    """The cells of a Markdown table row; an escaped `\\|` does not split one."""
    row = row.strip()
    row = row[1:] if row.startswith('|') else row
    row = row[:-1] if row.endswith('|') and not row.endswith('\\|') else row
    return re.split(r'(?<!\\)\|', row)


def heading_anchor(title):
    """The anchor of a heading, as site/build.py (slugify) and GitHub make it: lower case, punctuation dropped, spaces to
    hyphens, accents kept."""
    return re.sub(r'[^\w\- ]', '', title.strip().lower()).replace(' ', '-')


def readme_shape(text):
    """What a translation of a README keeps from the original: the sequence of heading levels, the rows and columns
    of each table, the number of code blocks, and (outside code blocks) the link and image targets and the code spans,
    which hold ids, file names, labels and commands. A link to a heading of the same README (`#anchor`) changes with
    the translated heading, so only the number of those links is kept; `anchors` lists the headings' anchors so that
    the caller can check where each one leads. The same parser reads every language, so the comparison holds even where
    it reads Markdown more simply than the site's renderer."""
    heads, anchors, tables, blocks, prose = [], Counter(), [], 0, []
    lines = text.splitlines()
    fence, i = None, 0
    while i < len(lines):
        line = lines[i]
        m = FENCE.match(line)
        if fence:
            if m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not line.strip()[len(m[1]):]:
                fence = None
            i += 1
            continue
        if m:
            fence, blocks = m[1], blocks + 1
            i += 1
            continue
        prose.append(line)
        m = HEADING.match(line)
        if m:
            heads.append(len(m[1]))
            anchor = heading_anchor(re.sub(r'[ \t]+#+[ \t]*$', '', line[m.end():]))  # without a closing run of #
            anchors[anchor] += 1
            if anchors[anchor] > 1:
                anchors[f'{anchor}-{anchors[anchor] - 1}'] += 1  # a repeated heading gets -1, -2, ... as on the site
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1] and TABLE_RULE.fullmatch(lines[i + 1]):
            columns, rows = len(table_cells(line)), 1
            prose.append(lines[i + 1])
            i += 2
            while i < len(lines) and lines[i].strip() and '|' in lines[i]:
                prose.append(lines[i])
                rows += 1
                i += 1
            tables.append((rows, columns))
            continue
        i += 1
    body = '\n'.join(prose)
    spans = Counter(re.sub(r'[ \t]*\n[ \t]*', ' ', m[2]) for m in CODE_SPAN.finditer(body))  # a line break is a space
    found = LINK_TARGET.findall(CODE_SPAN.sub('', body))
    targets = Counter(t for t in found if not t.startswith('#'))
    inpage = [t[1:] for t in found if t.startswith('#')]
    return {'heading levels': heads, 'tables (rows, columns)': tables, 'code blocks': blocks,
            'link and image targets': targets, 'links to its own headings': len(inpage), 'code spans': spans,
            'anchors': anchors, 'inpage': inpage}


STRUCTURE = ('heading levels', 'tables (rows, columns)', 'code blocks', 'link and image targets',
             'links to its own headings', 'code spans')  # the keys of readme_shape that a translation keeps


def md_cell(text):
    """`text` as one cell of a Markdown table: one line, with what would open a link, a tag or a column escaped."""
    return MARKDOWN_SPECIAL.sub(r'\\\1', ' '.join(text.split()))


def game_version(v):
    return f'{v >> 48}.{(v >> 32) & 0xffff}.{(v >> 16) & 0xffff}'


def fmt(n):
    return f'{n:,}'


class Checker:
    def __init__(self, root, protos):
        self.root = root
        self.errors = []
        self.p = protos
        self.entity = protos['entity']
        self.tiles = set(protos['tile'])
        self.names = (set(self.entity) | set(protos['item']) | set(protos['recipe']) | set(protos['fluid'])
                      | self.tiles | set(protos['virtual_signal']) | set(protos['quality'])
                      | set(protos.get('space_location', [])) | set(protos.get('asteroid_chunk', [])))

    def err(self, where, msg):
        self.errors.append(f'{where}: {msg}')

    # ---------- metadata ----------
    def check_fields(self, where, table, schema):
        ok = True
        for key in table:
            if key not in schema:
                self.err(where, f'unknown key {key!r}'); ok = False
        for key, (required, typ) in schema.items():
            if key not in table:
                if required:
                    self.err(where, f'missing required key "{key}"'); ok = False
                continue
            if not isinstance(table[key], typ) or (typ is str and not table[key].strip()):
                self.err(where, f'"{key}" must be a non-empty {typ.__name__}'); ok = False
        return ok

    def rel_file(self, where, folder, rel, exts=None):
        path = (folder / rel)
        if Path(rel).is_absolute() or '..' in Path(rel).parts:
            self.err(where, f'path "{rel}" must stay inside the folder'); return None
        if not SAFE_PATH.fullmatch(rel):
            self.err(where, f'path "{rel}" must start with a letter or digit and may hold only letters, digits, '
                            '".", "_", "-" and "/"')
            return None
        if exts and path.suffix.lower() not in exts:
            self.err(where, f'"{rel}" must be one of {sorted(exts)}'); return None
        if not path.is_file():
            self.err(where, f'file "{rel}" not found'); return None
        return path

    def load_meta(self, folder):
        where = self.where(folder / 'blueprint.toml')
        try:
            meta = tomllib.loads((folder / 'blueprint.toml').read_text(encoding='utf-8'))
        except tomllib.TOMLDecodeError as e:
            self.err(where, f'invalid TOML: {e}'); return None
        for path, text in strings_of(meta, ''):
            found = bad_chars(text)
            if found:
                self.err(where, f'{path!r} holds characters that draw nothing or reorder text (a zero-width joiner and a '
                                'byte-order mark included; an emoji selector is allowed only right after a symbol): '
                                f'{", ".join(found)}')
        self.check_fields(where, meta, SCHEMA)
        # Keep going after a schema error so one run reports every problem; wrong types count as absent.
        for key, (_, typ) in SCHEMA.items():
            if key in meta and not isinstance(meta[key], typ):
                del meta[key]
        meta.setdefault('files', []); meta.setdefault('tags', [])
        if 'category' in meta and meta['category'] not in CATEGORIES:
            self.err(where, f'category "{meta["category"]}" is not one of {sorted(CATEGORIES)}')
        for t in meta['tags']:
            if not isinstance(t, str) or not TAG.fullmatch(t):
                self.err(where, f'tag {t!r} must be lower-case words joined by "-"')
        if 'viewer' in meta and meta['viewer'] not in VIEWERS:
            self.err(where, f'viewer "{meta["viewer"]}" is not one of {sorted(VIEWERS)}')
        for key in ('files', 'images'):
            items = meta.get(key, [])
            if not items:
                # Every page shows real screenshots taken in the game, so a blueprint needs at least one image.
                self.err(where, f'needs at least one [[{key}]] entry')
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    self.err(where, f'{key}[{i}] must be a table'); continue
                self.check_fields(f'{where} {key}[{i}]', item, SUB_SCHEMA[key])
        for key in ('test', 'en', 'es'):
            if key in meta:
                self.check_fields(f'{where} [{key}]', meta[key], SUB_SCHEMA[key])
                if key != 'test' and 'credits' in meta and 'credits' not in meta[key]:
                    self.err(f'{where} [{key}]', 'missing "credits": the entry has credits, and every language shows them')
        test = meta.get('test', {})
        if test.get('status') and test['status'] not in TEST_STATUS:
            self.err(where, f'test.status "{test["status"]}" is not one of {sorted(TEST_STATUS)}')
        if test.get('game_version') and not VERSION_STR.fullmatch(test['game_version']):
            self.err(where, f'test.game_version "{test["game_version"]}" must look like 2.0.77')
        if test.get('report'):
            self.rel_file(where, folder, test['report'])
        for i, img in enumerate(meta.get('images', [])):
            if isinstance(img, dict) and isinstance(img.get('path'), str):
                self.rel_file(f'{where} images[{i}]', folder, img['path'], IMAGE_EXT)
        return meta

    # ---------- blueprint strings ----------
    def check_tree(self, where, data):
        """Walk the decoded JSON once: versions, prototype names, quality."""
        unknown = Counter(); first_seen = {}
        stack = [(data, '')]
        while stack:
            node, path = stack.pop()
            if isinstance(node, dict):
                for k, v in node.items():
                    p = f'{path}.{k}' if path else k
                    if k == 'version' and isinstance(v, int) and not game_version(v).startswith('2.0.'):
                        self.err(where, f'{p} is game version {game_version(v)}, expected 2.0.x')
                    elif k == 'name' and isinstance(v, str) and v not in self.names:
                        unknown[v] += 1; first_seen.setdefault(v, p)
                    elif k in ('quality', 'recipe_quality') and isinstance(v, str) and v != 'normal':
                        self.err(where, f'{p} = "{v}": only normal quality exists in the base game')
                    elif isinstance(v, (dict, list)):
                        stack.append((v, p))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    if isinstance(v, (dict, list)):
                        stack.append((v, f'{path}[{i}]'))
        for name, n in sorted(unknown.items()):
            self.err(where, f'"{name}" is not a vanilla Factorio 2.0 prototype ({n}x, e.g. {first_seen[name]})')

    def blueprint_stats(self, where, b, labels):
        ents, tiles = b.get('entities', []), b.get('tiles', [])
        bom, requests, recipes = Counter(), Counter(), Counter()
        x0 = y0 = float('inf'); x1 = y1 = float('-inf')
        for e in ents:
            proto = self.entity.get(e['name'])
            if proto is None:
                continue  # reported by check_tree
            w, h = proto['w'], proto['h']
            if e.get('direction', 0) in (4, 12):
                w, h = h, w
            x, y = e['position']['x'], e['position']['y']
            x0, x1, y0, y1 = min(x0, x - w / 2), max(x1, x + w / 2), min(y0, y - h / 2), max(y1, y + h / 2)
            placed = (proto.get('placed_by') or [{'name': e['name'], 'count': 1}])[0]
            bom[placed['name']] += placed['count']
            if e.get('recipe'):
                recipes[e['recipe']] += 1
            items = e.get('items')
            if isinstance(items, list):          # 2.0 insert plans
                for plan in items:
                    spots = plan.get('items', {})
                    n = sum(s.get('count', 1) for s in spots.get('in_inventory', [])) + spots.get('grid_count', 0)
                    requests[plan['id']['name']] += n
            elif isinstance(items, dict):        # 1.1 style
                for name, n in items.items():
                    requests[name] += n
        for t in tiles:
            name = t['name']
            if name not in self.tiles:
                continue
            x, y = t['position']['x'], t['position']['y']
            x0, x1, y0, y1 = min(x0, x), max(x1, x + 1), min(y0, y), max(y1, y + 1)
            placed = (self.p['tile_items'].get(name) or [{'name': name, 'count': 1}])[0]
            bom[placed['name']] += placed['count']
        width = round(x1 - x0) if ents or tiles else 0
        height = round(y1 - y0) if ents or tiles else 0
        return {
            'book_path': list(labels[:-1]), 'label': b.get('label') or '', 'description': b.get('description', ''),
            'entities': len(ents), 'tiles': len(tiles), 'width': width, 'height': height,
            'bom': dict(bom.most_common()), 'item_requests': dict(requests.most_common()),
            'recipes': dict(recipes.most_common()),
        }

    def check_file(self, folder, entry):
        where = self.where(folder / entry['path'])
        path = self.rel_file(self.where(folder / 'blueprint.toml'), folder, entry['path'], {'.txt'})
        if path is None:
            return None
        text = path.read_text(encoding='utf-8').strip()
        try:
            if not text.startswith('0'):
                raise ValueError('does not start with version byte 0')
            data = bp.decode(text)
            kind = bp.kind(data)
        except Exception as e:  # noqa: BLE001 - any failure here means "not a blueprint string"
            self.err(where, f'not a valid blueprint string ({type(e).__name__}: {e})'); return None
        self.check_tree(where, data)
        top = data[kind]
        prints = [self.blueprint_stats(where, b, labels) for labels, b in bp.walk(data)] if kind in (
            'blueprint', 'blueprint_book') else []
        if kind in ('blueprint', 'blueprint_book') and not prints:
            self.err(where, 'contains no blueprint')
        total_bom, total_req, total_rec = Counter(), Counter(), Counter()
        for s in prints:
            total_bom.update(s['bom']); total_req.update(s['item_requests']); total_rec.update(s['recipes'])
        largest = max(prints, key=lambda s: (s['entities'], s['width'] * s['height']), default=None)
        return {
            'name': entry['name'], 'name_en': entry.get('name_en'), 'name_es': entry.get('name_es'),
            'path': entry['path'], 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(text.encode()).hexdigest(), 'kind': kind, 'label': top.get('label') or '',
            'description': top.get('description', ''),
            'game_version': game_version(top['version']) if isinstance(top.get('version'), int) else None,
            'icons': [i.get('signal', {}).get('name') for i in top.get('icons', [])],
            'blueprint_count': len(prints), 'entities': sum(s['entities'] for s in prints),
            'largest': None if largest is None else {k: largest[k] for k in ('label', 'entities', 'width', 'height')},
            'bom': dict(total_bom.most_common()), 'item_requests': dict(total_req.most_common()),
            'recipes': dict(total_rec.most_common()), 'blueprints': prints,
        }

    # ---------- folders ----------
    def where(self, path):
        return str(path.relative_to(self.root))

    def check_folder(self, folder):
        where = self.where(folder)
        if not SLUG.fullmatch(folder.name):
            self.err(where, 'folder name must be lower-case words joined by "-"')
        if not (folder / 'blueprint.toml').is_file():
            self.err(where, 'missing blueprint.toml'); return None
        self.check_readmes(folder)
        meta = self.load_meta(folder)
        if meta is None:
            return None
        listed = {Path(f['path']).name for f in meta['files'] if isinstance(f, dict) and isinstance(f.get('path'), str)}
        for stray in sorted(p.name for p in folder.glob('*.txt')):
            if stray not in listed:
                self.err(where, f'"{stray}" is not listed in blueprint.toml; keep only the final version '
                                '(older versions live in git history)')
        files = [self.check_file(folder, f) for f in meta['files'] if isinstance(f, dict) and 'path' in f]
        if any(k not in meta for k in ('title', 'summary', 'category')):
            return None
        return {
            'slug': folder.name, 'title': meta['title'], 'summary': meta['summary'], 'category': meta['category'],
            'tags': meta['tags'], 'viewer': meta.get('viewer'), 'test': meta.get('test', {'status': 'untested'}),
            'images': meta.get('images', []), 'credits': meta.get('credits'), 'en': meta.get('en', {}),
            'es': meta.get('es', {}),
            'readme': dict(READMES),
            'files': [f for f in files if f],
        }

    def check_readmes(self, folder):
        """The README in every site language: present, UTF-8 without invisible characters, and each translation with the
        structure of README.md (readme_shape), so that no section, table row, link or code span is left out."""
        where = self.where(folder)
        texts = {}
        for lang, name in READMES.items():
            if not (folder / name).is_file():
                self.err(where, f'missing {name}' + ('' if lang == 'pt' else
                                                     f' (the translation of README.md: the {lang} pages show it)'))
                continue
            try:
                text = (folder / name).read_text(encoding='utf-8')
            except UnicodeDecodeError:
                self.err(where, f'{name} is not UTF-8 text')
                continue
            found = bad_chars(text)
            if found:
                self.err(where, f'{name} holds characters that draw nothing or reorder text (a zero-width joiner and a '
                                'byte-order mark included; an emoji selector is allowed only right after a symbol): '
                                f'{", ".join(found)}')
            texts[lang] = text
        shapes = {lang: readme_shape(text) for lang, text in texts.items()}
        for lang, shape in shapes.items():
            for anchor in shape['inpage']:
                if anchor not in shape['anchors']:
                    self.err(where, f'{READMES[lang]} links to #{anchor}, which is not a heading of that file')
        if 'pt' not in texts:
            return
        base = shapes['pt']
        for lang, text in texts.items():
            if lang == 'pt':
                continue
            name = READMES[lang]
            if text.strip() == texts['pt'].strip():
                self.err(where, f'{name} is a copy of README.md, not its translation')
                continue
            for key in STRUCTURE:
                want, got = base[key], shapes[lang][key]
                if got == want:
                    continue
                if isinstance(want, Counter):
                    missing, extra = sorted((want - got).elements()), sorted((got - want).elements())
                    detail = f'missing {missing[:5]}, not in README.md {extra[:5]}'
                else:
                    detail = f'README.md has {want}, {name} has {got}'
                self.err(where, f'{name} must keep the structure of README.md ({key} differ: {detail})')


def contents(entry):
    files = entry['files']
    books = [f for f in files if f['kind'] == 'blueprint_book']
    if books:
        n = sum(f['blueprint_count'] for f in books)
        return f'{len(books)} book{"s" if len(books) > 1 else ""}, {fmt(n)} blueprints'
    if len(files) == 1 and files[0]['blueprint_count'] == 1:
        b = files[0]['blueprints'][0]
        return f'{fmt(b["entities"])} entities, {b["width"]} × {b["height"]} tiles'
    return f'{sum(f["blueprint_count"] for f in files)} blueprints'


def print_report(catalog):
    for e in catalog:
        test = e['test']
        tested = TEST_STATUS.get(test.get('status'), '?') + (f' {test["game_version"]}' if test.get('game_version') else '')
        print(f'blueprints/{e["slug"]}  "{e["title"]}"  [{e["category"]}]  test: {tested}')
        for f in e['files']:
            kind = 'book' if f['kind'] == 'blueprint_book' else f['kind']
            line = f'  {f["path"]}  {kind}'
            if f['kind'] == 'blueprint_book':
                lg = f['largest']
                line += (f' · {f["blueprint_count"]} blueprints · {fmt(f["entities"])} entities in total'
                         f' · largest "{lg["label"]}": {fmt(lg["entities"])} entities, {lg["width"]}×{lg["height"]} tiles')
            elif f['blueprints']:
                b = f['blueprints'][0]
                line += f' · {fmt(b["entities"])} entities · {b["width"]}×{b["height"]} tiles'
            line += f' · game {f["game_version"]} · {f["bytes"] / 1e6:.1f} MB'
            print(line)
            scope = ' (sum over all blueprints)' if f['blueprint_count'] > 1 else ''
            top = ', '.join(f'{k} {fmt(v)}' for k, v in list(f['bom'].items())[:6])
            print(f'    materials{scope}: {top}' + (f' … {len(f["bom"])} kinds' if len(f['bom']) > 6 else ''))
            if f['item_requests']:
                print('    item requests: ' + ', '.join(f'{k} {fmt(v)}' for k, v in f['item_requests'].items()))
            if f['recipes'] and f['blueprint_count'] == 1:
                top = ', '.join(f'{k} {v}' for k, v in list(f['recipes'].items())[:6])
                print(f'    recipes: {top}' + (f' … {len(f["recipes"])} kinds' if len(f['recipes']) > 6 else ''))


def readme_table(catalog):
    rows = ['| Blueprint | Category | What is inside | Files | Tested |', '|---|---|---|---|---|']
    order = list(CATEGORIES)
    for e in sorted(catalog, key=lambda e: (order.index(e['category']), e['title'])):
        title = md_cell(e['en'].get('title', e['title']))
        files = ' · '.join(f'[`{f["path"]}`](blueprints/{e["slug"]}/{f["path"]})' for f in e['files'])
        test = e['test']
        tested = TEST_STATUS.get(test.get('status'), '?') + (f', {test["game_version"]}' if test.get('game_version') else '')
        rows.append(f'| [{title}](blueprints/{e["slug"]}/) | {CATEGORIES[e["category"]]} | {contents(e)} | {files} | {tested} |')
    return '\n'.join(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', type=Path, default=HERE.parent.parent, help='repository root (default: this repo)')
    ap.add_argument('--prototypes', type=Path, default=HERE / 'vanilla-prototypes.json')
    ap.add_argument('--json', action=OutPath, help='write the catalog index here (use a git-ignored path such as build/; an '
                                                   'existing file is overwritten); given once, without a ".." component')
    ap.add_argument('--readme', action='store_true', help='refresh the catalog table in README.md')
    args = ap.parse_args()
    root = args.root.resolve()
    try:
        protos = json.loads(args.prototypes.read_text())
    except FileNotFoundError:
        sys.exit(f'{args.prototypes} not found: run scripts/catalog/dump_prototypes.sh')
    chk = Checker(root, protos)
    folders = sorted(p for p in (root / 'blueprints').iterdir() if p.is_dir()) if (root / 'blueprints').is_dir() else []
    if not folders:
        chk.err('blueprints', 'no blueprint folders found')
    catalog = [c for c in (chk.check_folder(f) for f in folders) if c]
    print_report(catalog)
    if chk.errors:
        sys.stdout.flush()
        print(f'\nFAILED: {len(chk.errors)} error(s)', file=sys.stderr)
        for e in chk.errors:
            print(f'  ERROR {e}', file=sys.stderr)
        return 1
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        index = {'factorio_version': protos.get('factorio_version'), 'blueprints': catalog}
        args.json.write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')))
        print(f'wrote {args.json}')
    if args.readme:
        readme = root / 'README.md'
        text = readme.read_text(encoding='utf-8')
        if README_START not in text or README_END not in text:
            print(f'README.md has no {README_START} / {README_END} markers', file=sys.stderr)
            return 1
        head, rest = text.split(README_START, 1)
        _, tail = rest.split(README_END, 1)
        readme.write_text(f'{head}{README_START}\n{readme_table(catalog)}\n{README_END}{tail}', encoding='utf-8')
        print('updated README.md catalog table')
    n_files = sum(len(e['files']) for e in catalog)
    print(f'\nOK: {len(catalog)} blueprint folders, {n_files} files, 0 errors (vanilla {protos.get("factorio_version")})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
