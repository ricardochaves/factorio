#!/usr/bin/env python3
"""Build the GitHub Pages site from blueprints/ into build/site/.

Everything on the site comes from the repository: blueprint.toml (hand-written metadata), the blueprint strings
(numbers, materials, recipes, book contents), each README.md (the report), the images and the git history (dates,
changes). Nothing is typed twice.

usage (from the repository root, inside the virtual environment with site/requirements.txt installed):
  python3 site/build.py                    build into build/site/
  python3 site/build.py --out DIR          build somewhere else
  python3 -m http.server -d build/site     preview at http://localhost:8000/
Environment: SITE_URL (absolute URL of the site, for canonical links and the sitemap) and GITHUB_REPOSITORY
(owner/name, for links to the code); both default to this project's values. GA_MEASUREMENT_ID is the Google
Analytics 4 id ("G-..."); it defaults to this project's own id only when building this repository, so a fork gets no
analytics (and no privacy page) unless it sets its own. An empty value turns analytics off.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markdown_it import MarkdownIt
from PIL import Image

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
sys.path.insert(0, str(SITE))
sys.path.insert(0, str(ROOT / 'scripts'))
import bp  # noqa: E402  (scripts/bp.py)
import i18n  # noqa: E402  (site/i18n.py)

REPO = os.environ.get('GITHUB_REPOSITORY') or 'ricardochaves/factorio'
REPO_URL = f'https://github.com/{REPO}'
BRANCH = 'main'
SITE_URL = (os.environ.get('SITE_URL') or 'https://ricardochaves.github.io/factorio/').rstrip('/') + '/'
SITE_PATH = urlparse(SITE_URL).path  # '/factorio/' on GitHub Pages
GA_ID = os.environ.get('GA_MEASUREMENT_ID', 'G-4RJVJBEXXY' if REPO == 'ricardochaves/factorio' else '')
if GA_ID and not re.fullmatch(r'G-[A-Z0-9]{4,12}', GA_ID):
    raise SystemExit(f'GA_MEASUREMENT_ID must look like G-XXXXXXXXXX, got {GA_ID!r}')
IMAGE_WIDTHS = (320, 640, 1280, 1920)
IMAGE_QUALITY = {1920: 72}  # WebP quality per width (default 80); the largest one is the page's LCP image
CACHE_VERSION = 2  # bump when the image or string output changes, so build/.cache is not reused
CACHE = ROOT / 'build' / '.cache'
NXM_LABEL = re.compile(r'^(\d+) to (\d+)(?: \(([^)]+)\))?$')
THROUGHPUT = re.compile(r'full throughput \((\d+) belts?\)')
BIG_TABLE_ROWS = 25

USES = {  # feature -> item names that reveal it (bill of materials or inserted items)
    'modules': None,  # any inserted item whose name contains "module"
    'beacons': {'beacon'},
    'bots': {'roboport', 'active-provider-chest', 'passive-provider-chest', 'storage-chest', 'buffer-chest',
             'requester-chest', 'construction-robot', 'logistic-robot'},
    'trains': {'locomotive', 'cargo-wagon', 'fluid-wagon', 'artillery-wagon', 'rail', 'train-stop', 'rail-signal',
               'rail-chain-signal'},
    'circuits': {'arithmetic-combinator', 'decider-combinator', 'constant-combinator', 'selector-combinator',
                 'power-switch', 'programmable-speaker'},
}


def load_validator():
    spec = importlib.util.spec_from_file_location('validate', ROOT / 'scripts' / 'catalog' / 'validate.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(*args):
    try:
        return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ''


def git_commits():
    """Commits that touched blueprints/, newest first, with the files each one changed."""
    commits = []
    for block in git('log', '--format=%x1e%H%x1f%cI%x1f%s', '--name-only', '--', 'blueprints').split('\x1e')[1:]:
        head, _, files = block.partition('\n')
        sha, when, subject = head.split('\x1f')
        commits.append({
            'sha': sha, 'date': dt.datetime.fromisoformat(when).date(),
            'subject': re.sub(r'\s*\(#\d+\)$', '', subject.strip()),
            'url': f'{REPO_URL}/commit/{sha}', 'files': [f for f in files.split('\n') if f],
        })
    return commits


def string_commits(commits, slug):
    """Commits that changed a blueprint string of this folder (its versions)."""
    pattern = re.compile(rf'^blueprints/{re.escape(slug)}/[^/]+\.txt$')
    return [c for c in commits if any(pattern.match(f) for f in c['files'])]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slugify(text):
    """GitHub's heading anchors: lower case, punctuation dropped, spaces to hyphens (accents kept)."""
    s = re.sub(r'[^\w\- ]', '', text.strip().lower())
    return s.replace(' ', '-')


def norm(text):
    """Search text: lower case without accents, same as normalize() in catalog.js."""
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')


# ---------------------------------------------------------------- README -> HTML
class Readme:
    def __init__(self):
        self.md = MarkdownIt('commonmark', {'html': False, 'linkify': False, 'typographer': False}).enable('table')

    def inline(self, text):
        return self.md.renderInline(text)

    def rewrite(self, href, slug):
        if not href or href.startswith(('#', 'http://', 'https://', 'mailto:')):
            return href
        path, _, anchor = href.partition('#')
        target = posixpath.normpath(posixpath.join('blueprints', slug, path))
        if target.startswith('..'):
            return href
        if posixpath.dirname(target) == 'blueprints' and (ROOT / target / 'blueprint.toml').is_file():
            # another catalog entry: its page, in the same language (pages live at <language>/blueprints/<slug>/)
            return f'../{posixpath.basename(target)}/' + (f'#{anchor}' if anchor else '')
        kind = 'blob' if posixpath.splitext(target)[1] else 'tree'
        return f'{REPO_URL}/{kind}/{BRANCH}/{target}' + (f'#{anchor}' if anchor else '')

    def sections(self, text, slug):
        """Split a README into an intro and its level-2 sections, rendered to HTML."""
        tokens = self.md.parse(text)
        used = Counter()
        groups, current, skip_h1 = [], {'title': None, 'id': None, 'tokens': []}, False
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.type == 'heading_open':
                title = tokens[i + 1].content
                anchor = slugify(title)
                used[anchor] += 1
                if used[anchor] > 1:
                    anchor = f'{anchor}-{used[anchor] - 1}'
                if tok.tag == 'h1':
                    i += 3
                    continue
                if tok.tag == 'h2':
                    groups.append(current)
                    current = {'title': title, 'id': anchor, 'tokens': []}
                    i += 3
                    continue
                tok.attrSet('id', anchor)
            if tok.type == 'inline' and tok.children:
                kept = []
                for child in tok.children:
                    if child.type == 'image':
                        continue
                    if child.type == 'link_open':
                        child.attrSet('href', self.rewrite(child.attrGet('href'), slug))
                    kept.append(child)
                tok.children = kept
            current['tokens'].append(tok)
            i += 1
        groups.append(current)
        out = []
        for g in groups:
            body = self.md.renderer.render(g['tokens'], self.md.options, {})
            body = re.sub(r'<p>\s*</p>\n?', '', body).strip()
            if not body:
                continue
            rows = body.count('<tr>')
            # scrollable regions must be reachable with the keyboard (WCAG 2.1.1)
            body = body.replace('<table>', '<div class="table-wrap" tabindex="0"><table>').replace('</table>', '</table></div>')
            body = body.replace('<pre>', '<pre tabindex="0">')
            out.append({'title': g['title'] and self.inline(g['title']), 'id': g['id'], 'html': body,
                        'big': rows > BIG_TABLE_ROWS + 1})
        return out


# ---------------------------------------------------------------- images
def build_images(entry, out):
    result = []
    for img in entry['images']:
        src = ROOT / 'blueprints' / entry['slug'] / img['path']
        stem = Path(img['path']).stem
        dest = out / 'img' / entry['slug']
        dest.mkdir(parents=True, exist_ok=True)
        digest = sha256(src)[:16]
        with Image.open(src) as im:
            w, h = im.size
            full = dest / src.name
            shutil.copyfile(src, full)
            variants = []
            for width in IMAGE_WIDTHS:
                if width >= w:
                    break
                height = round(h * width / w)
                name = f'{stem}-{width}.webp'
                quality = IMAGE_QUALITY.get(width, 80)
                cached = CACHE / 'img' / f'v{CACHE_VERSION}-{digest}-{width}-q{quality}.webp'
                if not cached.exists():
                    cached.parent.mkdir(parents=True, exist_ok=True)
                    im.convert('RGB').resize((width, height), Image.LANCZOS).save(cached, 'WEBP', quality=quality,
                                                                                   method=6)
                shutil.copyfile(cached, dest / name)
                variants.append((f'img/{entry["slug"]}/{name}', width, height))
            if w <= IMAGE_WIDTHS[-1]:
                variants.append((f'img/{entry["slug"]}/{src.name}', w, h))
        # the hero is at most 1164 px wide and 640 px tall (object-fit: contain), so it rarely needs its full width
        shown = min(1164, round(640 * w / h))
        result.append({
            'alt': translated_key(img, 'alt'),
            'full': f'img/{entry["slug"]}/{src.name}', 'width': w, 'height': h, 'shown': shown,
            'variants': variants, 'small': variants[0][0],
            'og': next((v for v in variants if v[1] >= 1200), variants[-1]),
        })
    return result


# ---------------------------------------------------------------- blueprint strings
def write_string(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = bp.encode(obj)
    if bp.decode(text) != obj:  # never publish a string that does not round-trip
        raise SystemExit(f'{path}: encoded string does not decode to the same blueprint')
    path.write_text(text + '\n', encoding='utf-8')


def split_book(entry, f, out):
    """Write each top-level child of a book (and, for an N x M viewer, each blueprint) as its own string."""
    src = ROOT / 'blueprints' / entry['slug'] / f['path']
    stem = Path(f['path']).stem
    rel = f'files/{entry["slug"]}/{stem}'
    cached = CACHE / 'strings' / f'v{CACHE_VERSION}-{sha256(src)[:16]}-{entry.get("viewer") or "book"}'
    data = bp.decode(src.read_text(encoding='utf-8'))
    book = data['blueprint_book']
    children = []
    for child in book.get('blueprints', []):
        kind = bp.kind(child)
        inner = child[kind]
        label = inner.get('label') or ''
        leaves = [b.get('label') or '' for _, b in bp.walk({kind: inner})]
        pairs = [nxm_pair(x) for x in (leaves[0], leaves[-1])] if leaves else [None, None]
        children.append({'label': label, 'kind': kind, 'count': len(leaves), 'description': inner.get('description', ''),
                         'url': f'{rel}/{slugify(label) or "item"}.txt', 'obj': {kind: inner},
                         # "N to 1 ... N to 24": the page writes it in its own language
                         'range': pairs if all(pairs) else None})
    names = [Path(c['url']).name for c in children]
    if len(set(names)) != len(names):
        raise SystemExit(f'{src}: two top-level items of the book have the same label, rename one')
    if not cached.exists():
        tmp = cached.with_suffix('.tmp')
        shutil.rmtree(tmp, ignore_errors=True)
        for c in children:
            write_string(tmp / (Path(c['url']).name), c['obj'])
        if entry.get('viewer') == 'nxm-matrix':
            seen = set()
            for labels, b in bp.walk(data):
                m = NXM_LABEL.match(b.get('label') or '')
                if m:
                    name = f'{m[1]}-{m[2]}' + (f'-{slugify(m[3])}' if m[3] else '')
                    if name in seen:
                        raise SystemExit(f'{src}: two blueprints are labelled "{b.get("label")}"')
                    seen.add(name)
                    write_string(tmp / f'{name}.txt', {'blueprint': b})
        shutil.rmtree(cached, ignore_errors=True)
        tmp.rename(cached)
    shutil.copytree(cached, out / rel, dirs_exist_ok=True)
    for c in children:
        del c['obj']
    return children, data


def nxm_pair(label):
    """'2 to 3 (Wide)' -> {'n': 2, 'm': 3, 'variant': 'wide'}; None when the label is not an N x M pair."""
    m = NXM_LABEL.match(label or '')
    return {'n': int(m[1]), 'm': int(m[2]), 'variant': slugify(m[3]) if m[3] else None} if m else None


def origin_code(description):
    first = (description or '').split('\n')[0]
    for o in i18n.ORIGINS:
        if first.startswith(o['prefix']):
            return o['code']
    return 'u'


def translated(default, table, key):
    """{lang: text} from the Portuguese default and the [en] / [es] tables of blueprint.toml."""
    return {lang: (default if lang == i18n.DEFAULT else (table.get(lang) or {}).get(key) or default)
            for lang in i18n.LANGS}


def translated_key(item, key):
    """{lang: text} from item[key] (Portuguese) and item[f'{key}_{lang}']."""
    return {lang: item.get(key if lang == i18n.DEFAULT else f'{key}_{lang}') or item[key] for lang in i18n.LANGS}


def nxm_grid(entry, f, data):
    cells, variants, sizes = {}, {}, set()
    for labels, b in bp.walk(data):
        m = NXM_LABEL.match(b.get('label') or '')
        if not m:
            continue
        n, k, variant = int(m[1]), int(m[2]), m[3]
        sizes.update((n, k))
        key = f'{n}-{k}'
        stats = next(s for s in f['blueprints'] if s['label'] == b['label'])
        if variant:  # the panel shows each variant's own numbers; the cell shows the first variant's
            variants.setdefault(key, []).append([slugify(variant), variant, stats['entities'], stats['width'],
                                                 stats['height']])
        if key in cells:
            continue
        thr = THROUGHPUT.search(b.get('description', ''))
        cells[key] = (origin_code(b.get('description')), stats['entities'], stats['width'], stats['height'],
                      int(thr[1]) if thr else 0, labels[-2] if len(labels) > 1 else '')
    size = max(sizes)
    order = [f'{n}-{k}' for n in range(1, size + 1) for k in range(1, size + 1)]
    get = lambda i: [cells[key][i] if key in cells else None for key in order]  # noqa: E731
    return {
        'size': size, 'o': ''.join(cells[key][0] if key in cells else '-' for key in order),
        'e': get(1), 'w': get(2), 'h': get(3), 't': get(4), 'sub': get(5), 'v': variants,
    }


# ---------------------------------------------------------------- catalog model
def load_catalog():
    validate = load_validator()
    protos = json.loads((ROOT / 'scripts' / 'catalog' / 'vanilla-prototypes.json').read_text(encoding='utf-8'))
    chk = validate.Checker(ROOT, protos)
    folders = sorted(p for p in (ROOT / 'blueprints').iterdir() if p.is_dir())
    catalog = [c for c in (chk.check_folder(f) for f in folders) if c]
    if chk.errors:
        for e in chk.errors:
            print(f'ERROR {e}', file=sys.stderr)
        raise SystemExit('the catalog has errors: run scripts/catalog/validate.py')
    return catalog


def machines_of(bom):
    return [(name, bom[name]) for name in i18n.MACHINES if bom.get(name)][:i18n.STAT_MACHINES]


def uses_of(bom, requests):
    found = []
    for feature, names in USES.items():
        if feature == 'modules':
            if any('module' in k for k in requests):
                found.append(feature)
        elif names & set(bom) or names & set(requests):
            found.append(feature)
    return found


def build_model(out):
    catalog = load_catalog()
    locale = json.loads((ROOT / 'scripts' / 'catalog' / 'vanilla-locale.json').read_text(encoding='utf-8'))
    commits = git_commits()
    readme = Readme()
    entries = []
    for c in catalog:
        slug = c['slug']
        tables = {lang: c.get(lang) or {} for lang in i18n.LANGS}
        e = {
            'slug': slug, 'category': c['category'], 'tags': c['tags'], 'viewer': c.get('viewer'),
            'test': c['test'],
            'title': translated(c['title'], tables, 'title'),
            'summary': translated(c['summary'], tables, 'summary'),
            'credits': None,
        }
        if c.get('credits'):
            e['credits'] = {lang: readme.inline(text)
                            for lang, text in translated(c['credits'], tables, 'credits').items()}
        history = string_commits(commits, slug)
        e['history'] = history
        e['date'] = history[0]['date'] if history else None
        e['images'] = build_images(c, out)
        e['kind'] = 'book' if any(f['kind'] == 'blueprint_book' for f in c['files']) else 'blueprint'
        files = []
        for f in c['files']:
            stem = Path(f['path']).stem
            src = ROOT / 'blueprints' / slug / f['path']
            fo = {
                'id': stem, 'name': translated_key(f, 'name'),
                'path': f['path'], 'bytes': f['bytes'], 'kind': f['kind'], 'count': f['blueprint_count'],
                'entities': f['entities'], 'largest': f['largest'], 'url': f'files/{slug}/{f["path"]}',
                'color': i18n.BELT_COLORS.get(stem, '#f2a531'),
            }
            dest = out / 'files' / slug / f['path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            if f['kind'] == 'blueprint_book':
                fo['children'], data = split_book(c, f, out)
                if c.get('viewer') == 'nxm-matrix':
                    fo['grid'] = nxm_grid(c, f, data)
                    # count blueprints, not matrix cells: a pair can have several variants (2 to 3 Long and Wide)
                    codes = Counter(origin_code(b.get('description')) for _, b in bp.walk(data)
                                    if NXM_LABEL.match(b.get('label') or ''))
                    fo['origins'] = {o['code']: codes.get(o['code'], 0) for o in i18n.ORIGINS}
                    if sum(fo['origins'].values()) != f['blueprint_count']:
                        raise SystemExit(f'{slug}/{f["path"]}: origins cover {sum(fo["origins"].values())} of '
                                         f'{f["blueprint_count"]} blueprints')
            if fo['largest']:
                fo['largest'] = dict(fo['largest'], pair=nxm_pair(fo['largest']['label']))
            files.append(fo)
        e['files'] = files
        e['default_file'] = len(files) - 1  # files go from the simplest to the most advanced variant
        total_bom, total_req, recipes = Counter(), Counter(), Counter()
        for f in c['files']:
            total_bom.update(f['bom']); total_req.update(f['item_requests'])
        e['bom'] = total_bom.most_common()
        e['requests'] = total_req.most_common()
        e['uses'] = uses_of(total_bom, total_req)
        e['blueprint_count'] = sum(f['blueprint_count'] for f in c['files'])
        single = e['kind'] == 'blueprint' and len(c['files']) == 1 and c['files'][0]['blueprint_count'] == 1
        e['single'] = None
        if single:
            s = c['files'][0]['blueprints'][0]
            data = bp.decode((ROOT / 'blueprints' / slug / c['files'][0]['path']).read_text(encoding='utf-8'))
            for ent in data['blueprint'].get('entities', []):
                if ent.get('recipe'):
                    recipes[(ent['recipe'], ent['name'])] += 1
            by_recipe = {}
            for (recipe, machine), n in recipes.items():
                by_recipe.setdefault(recipe, []).append((machine, n))
            rows = sorted(by_recipe.items(), key=lambda kv: (-sum(n for _, n in kv[1]), kv[0]))
            e['single'] = {'entities': s['entities'], 'width': s['width'], 'height': s['height'],
                           'machines': machines_of(total_bom), 'recipes': rows}
        readme_path = ROOT / 'blueprints' / slug / 'README.md'
        e['report'] = readme.sections(readme_path.read_text(encoding='utf-8'), slug)
        # search text in every language, so a query in any of them finds the blueprint
        cat = next(x for x in i18n.CATEGORIES if x['id'] == e['category'])
        words = []
        for lang in i18n.LANGS:
            words += [e['title'][lang], e['summary'][lang], cat[lang]]
            words += [i18n.TAGS[t][lang] if t in i18n.TAGS else t.replace('-', ' ') for t in e['tags']]
            words += [f['name'][lang] for f in files]
            names = locale[i18n.GAME_LOCALE[lang]]['recipe']
            words += [names.get(recipe, recipe) for (recipe, _machine) in recipes]
        e['search'] = norm(' '.join(dict.fromkeys(words)))
        entries.append(e)
    # newest first, then by name
    entries.sort(key=lambda e: (-(e['date'].toordinal() if e['date'] else 0), e['title']['pt'].lower()))
    for e in entries:
        scored = []
        for o in entries:
            if o is e:
                continue
            score = (2 if o['category'] == e['category'] else 0) + len(set(o['tags']) & set(e['tags']))
            if score:
                scored.append((-score, o['title']['pt'], o))
        e['related'] = [o for *_, o in sorted(scored, key=lambda x: x[:2])][:3]
    news = []
    titles = {e['slug']: e['title'] for e in entries}
    for cmt in commits:
        slugs = []
        for f in cmt['files']:
            m = re.match(r'^blueprints/([^/]+)/[^/]+\.txt$', f)
            if m and m[1] in titles and m[1] not in slugs:
                slugs.append(m[1])
        if slugs:  # one entry per commit, naming every blueprint it changed
            news.append({'date': cmt['date'], 'subject': cmt['subject'], 'url': cmt['url'],
                         'blueprints': [{'slug': s, 'title': titles[s]} for s in slugs]})
    return entries, news[:4], locale


# ---------------------------------------------------------------- rendering
class DataEnvironment(Environment):
    """In templates, d.key reads the dict key first. Plain Jinja tries the attribute first, so t.clear printed the
    method dict.clear instead of the text of the key "clear"."""

    def getattr(self, obj, attribute):
        if isinstance(obj, dict) and attribute in obj:
            return obj[attribute]
        return super().getattr(obj, attribute)


class Site:
    def __init__(self, out, entries, news, locale):
        self.out, self.entries, self.news, self.locale = out, entries, news, locale
        self.env = DataEnvironment(loader=FileSystemLoader(SITE / 'templates'), autoescape=select_autoescape(['html']),
                                   undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        self.assets = {}
        self.pages = []

    def copy_static(self):
        dest = self.out / 'assets'
        shutil.copytree(SITE / 'static' / 'fonts', dest / 'fonts')
        for name in ('site.css', 'site.js', 'catalog.js', 'book.js') + (('analytics.js',) if GA_ID else ()):
            src = SITE / 'static' / name
            digest = hashlib.sha256(src.read_bytes()).hexdigest()[:10]
            stem, ext = name.rsplit('.', 1)
            shutil.copyfile(src, dest / f'{stem}.{digest}.{ext}')
            self.assets[name] = f'assets/{stem}.{digest}.{ext}'
        shutil.copyfile(SITE / 'static' / 'favicon.svg', self.out / 'favicon.svg')

    def context(self, lang, path, page, root=None):
        prefix = i18n.PREFIX[lang]
        if root is None:
            root = '../' * (path.count('/') + prefix.count('/'))
        t = i18n.T[lang]
        game = self.locale[i18n.GAME_LOCALE[lang]]
        game_en = self.locale['en']

        def loc(d):
            return i18n.label(d, lang) if isinstance(d, dict) else d

        def link(p=''):
            return root + prefix + p

        def tag_label(tag):
            if tag in i18n.TAGS:
                return i18n.TAGS[tag][lang]
            m = re.fullmatch(r'(\d+)x(\d+)', tag)
            return f'{m[1]} × {m[2]}' if m else tag.replace('-', ' ')

        def cat_label(cid):
            return next(x for x in i18n.CATEGORIES if x['id'] == cid)[lang]

        def machine_label(name, n):
            if name in i18n.MACHINES:
                return i18n.MACHINES[name][lang][0 if n == 1 else 1]
            return game['entity'].get(name, name)

        def kind_label(e):
            base = t['kind_book'] if e['kind'] == 'book' else t['kind_blueprint']
            n = len(e['files'])
            return base + (f' · {t["variants"].format(n=n)}' if n > 1 else '')

        def facts(e):
            if e['single']:
                s = e['single']
                return t['facts_bp'].format(e=i18n.fmt_int(s['entities'], lang), w=s['width'], h=s['height'])
            if e['blueprint_count'] == 1:
                return t['facts_book_one']
            return t['facts_book'].format(n=i18n.fmt_int(e['blueprint_count'], lang))

        def variant_name(slug, fallback=''):
            return i18n.VARIANTS[slug][lang] if slug in i18n.VARIANTS else fallback or slug

        def pair_label(p):
            """{'n', 'm', 'variant'} from nxm_pair -> '17 para 18' (+ ' (Largo)')."""
            text = t['pair_label'].format(n=p['n'], m=p['m'])
            return text + (f' ({variant_name(p["variant"])})' if p.get('variant') else '')

        def count_label(n, one_key, many_key):
            return t[one_key] if n == 1 else t[many_key].format(n=i18n.fmt_int(n, lang))

        def srcset(img):
            return ', '.join(f'{root}{p} {w}w' for p, w, _ in img['variants'])

        return {
            'lang': lang, 'html_lang': i18n.HTML_LANG[lang], 'og_locale': i18n.OG_LOCALE[lang], 't': t,
            'root': root, 'path': path, 'page': page, 'link': link, 'loc': loc,
            'asset': lambda n: root + self.assets[n],
            'languages': [{'code': code, 'short': code.upper(), 'name': i18n.LANG_NAME[code],
                           'html_lang': i18n.HTML_LANG[code], 'url': root + i18n.PREFIX[code] + path,
                           'abs': SITE_URL + i18n.PREFIX[code] + path, 'current': code == lang}
                          for code in i18n.LANGS],
            'canonical': SITE_URL + prefix + path, 'site_url': SITE_URL,
            'repo_url': REPO_URL, 'branch': BRANCH, 'all_t': i18n.T,
            'ga_id': GA_ID, 'ga_host': urlparse(SITE_URL).hostname, 'ga_path': SITE_PATH.rstrip('/'),
            'fmt_int': lambda n: i18n.fmt_int(n, lang), 'fmt_bytes': lambda n: i18n.fmt_bytes(n, lang),
            'fmt_date': lambda d: i18n.fmt_date(d, lang) if d else '',
            'tag_label': tag_label, 'cat_label': cat_label, 'machine_label': machine_label,
            'kind_label': kind_label, 'facts': facts, 'srcset': srcset,
            'pair_label': pair_label, 'variant_name': variant_name, 'count_label': count_label,
            'recipe_name': lambda r: game['recipe'].get(r, r),
            # items with their in-game name in the page's language (English name when the game has no translation)
            'item_name': lambda i: game['item'].get(i) or game['entity'].get(i) or game_en['item'].get(i, i),
            'categories': i18n.CATEGORIES, 'origins': i18n.ORIGINS,
            'phases': i18n.PHASES, 'city': i18n.CITY, 'uses': i18n.USES,
            'entries': self.entries, 'news': self.news,
        }

    def write(self, dest, html):
        if 'built-in method' in html or 'bound method' in html:  # a template printed a Python method, not text
            raise SystemExit(f'{dest}: a template printed a Python method; check the attribute names')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding='utf-8')

    def render(self, template, lang, path, page, **extra):
        ctx = self.context(lang, path, page)
        ctx.update(extra)
        self.write(self.out / i18n.PREFIX[lang] / path / 'index.html', self.env.get_template(template).render(**ctx))
        self.pages.append(ctx['canonical'])

    def render_404(self):
        """GitHub Pages serves /404.html for any missing path, so its links are absolute and it speaks every language."""
        ctx = self.context(i18n.DEFAULT, '', '404', root=SITE_PATH)  # root-relative: works on any missing path
        self.write(self.out / '404.html', self.env.get_template('404.html').render(**ctx))

    def catalog_index(self, lang):
        rows = []
        for e in self.entries:
            nxm = None
            if e['viewer'] == 'nxm-matrix':
                f = e['files'][e['default_file']]
                nxm = {'size': f['grid']['size'], 'file': f['id']}
            rows.append({
                'slug': e['slug'], 'cat': e['category'], 'kind': e['kind'], 'test': e['test'].get('status', 'untested'),
                'tags': e['tags'], 'uses': e['uses'], 'date': e['date'].isoformat() if e['date'] else '',
                'size': e['single']['entities'] if e['single'] else sum(f['entities'] for f in e['files']),
                'title': e['title'][lang], 'text': e['search'], 'nxm': nxm,
            })
        return rows

    def book_data(self, e, lang):
        def localized(grid):
            variants = {key: [[slug, i18n.VARIANTS[slug][lang] if slug in i18n.VARIANTS else name, *numbers]
                              for slug, name, *numbers in vs] for key, vs in grid['v'].items()}
            return dict(grid, v=variants)
        return [{'id': f['id'], 'name': i18n.label(f['name'], lang), 'grid': localized(f['grid'])} for f in e['files']]

    def privacy(self, lang):
        """The privacy page is plain Markdown per language (site/content/privacy.<lang>.md), rendered like a README."""
        text = (SITE / 'content' / f'privacy.{lang}.md').read_text(encoding='utf-8')
        # the name of the per-property cookie comes from the id, so the text cannot drift from the tag
        return Readme().sections(text.replace('%GA_COOKIE%', '_ga_' + GA_ID[2:]), '')

    def og_image(self, e, lang):
        img = e['images'][0] if e else None
        return {'variant': img['og'], 'alt': i18n.label(img['alt'], lang)} if img else None

    def build(self):
        self.copy_static()
        first = self.entries[0] if self.entries else None
        for lang in i18n.LANGS:
            self.render('home.html', lang, '', 'home', og_image=self.og_image(first, lang))
            self.render('catalog.html', lang, 'catalog/', 'catalog', index=self.catalog_index(lang),
                        og_image=self.og_image(first, lang))
            for e in self.entries:
                template = 'book.html' if e['kind'] == 'book' else 'blueprint.html'
                extra = {'e': e, 'og_image': self.og_image(e, lang)}
                if e['viewer'] == 'nxm-matrix':
                    extra['book_data'] = self.book_data(e, lang)
                self.render(template, lang, f'blueprints/{e["slug"]}/', 'blueprint', **extra)
            if GA_ID:  # the page that explains the analytics only exists when there are analytics
                self.render('privacy.html', lang, 'privacy/', 'privacy', sections=self.privacy(lang))
        self.render_404()
        urls = '\n'.join(f'  <url><loc>{u}</loc></url>' for u in self.pages)
        (self.out / 'sitemap.xml').write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n', encoding='utf-8')
        # No robots.txt: a project site lives under /factorio/ and crawlers only read /robots.txt at the host's root.


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', type=Path, default=ROOT / 'build' / 'site')
    args = ap.parse_args()
    out = args.out.resolve()
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    entries, news, locale = build_model(out)
    Site(out, entries, news, locale).build()
    total = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    print(f'built {len(entries)} blueprints, {sum(1 for _ in out.rglob("*.html"))} pages, '
          f'{total / 1e6:.1f} MB in {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
