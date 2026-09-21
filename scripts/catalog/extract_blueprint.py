#!/usr/bin/env python3
"""Extract a Factorio blueprint string from a file, a URL, stdin or Claude Code's paste cache, and check it.

usage:
  python3 scripts/catalog/extract_blueprint.py <file|url> --out <path>
  python3 scripts/catalog/extract_blueprint.py - --out <path>                        raw text on stdin
  python3 scripts/catalog/extract_blueprint.py --from-paste-cache <first chars> --out <path>

The input may be the string itself, a JSON file (a decoded blueprint, or JSON that holds the string in a field), or
any text or HTML page that contains it. The string is accepted only when zlib decodes it (its Adler-32 catches any
typo), the JSON parses, and it is a single blueprint or a blueprint book.

Prints one JSON object and exits 0 when the string was written to --out; `duplicate_of` in it names the catalog file
that holds exactly this string, and `same_design_as` the one that holds the same design under another label,
description, icons or game version (nothing is refused for either). Exit 2: nothing usable, or any other failure
(the reason is on stderr). Exit 3: several different blueprints were found (the list is printed; nothing was written;
choose with --pick N). It never runs anything it reads. Limits: 50 MB of input, 256 MiB once decompressed, 50 candidate
strings. A URL must be http(s) and must resolve to a public address, also after each redirect (a DNS rebinding between
the check and the request is not prevented); --allow-private lifts that for a service you run yourself, and only together
with EXTRACT_BLUEPRINT_ALLOW_PRIVATE=1 in the environment, so a command line alone cannot switch the check off.
Standard library only (Python 3.11+).
"""
import argparse
import base64
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import zlib
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bp  # noqa: E402  (scripts/bp.py)

MAX_BYTES = 50 * 1024 * 1024
MAX_DECOMPRESSED = 256 * 1024 * 1024
MAX_CANDIDATES = 50
KINDS = ('blueprint', 'blueprint_book')
COSMETIC = ('label', 'description', 'icons', 'version', 'active_index')
ALL_KINDS = KINDS + ('upgrade_planner', 'deconstruction_planner')
WHOLE = re.compile(r'0[A-Za-z0-9+/]{40,}={0,2}')
SCAN = re.compile(r'0[A-Za-z0-9+/]{60,}={0,2}')
# Unicode categories that draw nothing: control, format, private-use, surrogate, unassigned, line and paragraph separators and
# spaces (only U+007F and above are tested: JSON already escapes the control characters below U+0020, and U+0020 is the
# ordinary space).
INVISIBLE = ('Cc', 'Cf', 'Co', 'Cs', 'Cn', 'Zl', 'Zp', 'Zs')
# Letters, marks and symbols that draw nothing although their category is not in INVISIBLE, by code point.
BLANK_RANGES = ((0x034F, 0x034F), (0x115F, 0x1160), (0x17B4, 0x17B5), (0x180B, 0x180F), (0x2800, 0x2800),
                (0x3164, 0x3164), (0xFE00, 0xFE0F), (0xFFA0, 0xFFA0), (0xE0100, 0xE01EF))
NON_ASCII = re.compile('[\x7f-\U0010ffff]')


class Refuse(Exception):
    """The input cannot be used; the message says why."""


def is_blank(c):
    return any(lo <= ord(c) <= hi for lo, hi in BLANK_RANGES)


def make_visible(text):
    """`text` with every invisible character written as a JSON \\u escape. A label or a description comes from the source, and a
    character that draws nothing (a zero-width space, a bidirectional control, a Unicode tag character) would otherwise reach the
    reader unseen. `text` is JSON, so each escape decodes back to the same character."""
    def escape(m):
        c = m.group()
        if unicodedata.category(c) not in INVISIBLE and not is_blank(c):
            return c
        return '\\u%04x' % ord(c) if ord(c) <= 0xFFFF else json.dumps(c)[1:-1]  # above U+FFFF JSON writes a surrogate pair
    return NON_ASCII.sub(escape, text)


def game_version(v):
    return f'{v >> 48}.{(v >> 32) & 0xffff}.{(v >> 16) & 0xffff}'


def check_public(url, allow_private):
    """Refuse an address that is not http(s), or that resolves to a private, loopback or link-local address."""
    parts = urlsplit(url)
    if parts.scheme.lower() not in ('http', 'https'):
        raise Refuse(f'only http and https addresses are accepted, not {parts.scheme or "a bare path"}://')
    if allow_private:
        return
    if not parts.hostname:
        raise Refuse('the address has no host name')
    try:
        infos = socket.getaddrinfo(parts.hostname, None)
    except socket.gaierror as e:
        raise Refuse(f'cannot resolve {parts.hostname}: {e}') from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split('%')[0])
        if not ip.is_global:
            raise Refuse(f'{parts.hostname} resolves to {ip}, which is not a public address '
                         '(--allow-private is for a service you run yourself)')


def ssl_context():
    """The default context, plus the macOS system bundle when this Python has no CA file (python.org builds ship none
    until "Install Certificates.command" runs). Verification stays on."""
    ctx = ssl.create_default_context()
    paths = ssl.get_default_verify_paths()
    have = (paths.cafile and os.path.exists(paths.cafile)) or (paths.capath and os.path.isdir(paths.capath))
    if not have and os.path.exists('/etc/ssl/cert.pem'):
        ctx.load_verify_locations('/etc/ssl/cert.pem')
    return ctx


def read_url(url, max_bytes, allow_private):
    class CheckedRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            check_public(newurl, allow_private)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    check_public(url, allow_private)
    opener = urllib.request.build_opener(CheckedRedirect(), urllib.request.HTTPSHandler(context=ssl_context()))
    req = urllib.request.Request(url, headers={'User-Agent': 'factorio-blueprints-add-blueprint/1'})
    try:
        with opener.open(req, timeout=30) as resp:
            data = resp.read(max_bytes + 1)
            charset = resp.headers.get_content_charset() or 'utf-8'
    except urllib.error.HTTPError as e:
        why = 'redirected to an address that is not allowed' if 300 <= e.code < 400 else 'answered'
        raise Refuse(f'the server {why} (HTTP {e.code}) for {url}') from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if isinstance(getattr(e, 'reason', None), ssl.SSLCertVerificationError):
            raise Refuse(f'this Python cannot verify the certificate of {url} (a python.org install needs '
                         f'"Install Certificates.command"): {e.reason}') from e
        raise Refuse(f'could not fetch {url}: {e}') from e
    if len(data) > max_bytes:
        raise Refuse(f'the response is larger than {max_bytes} bytes')
    return data.decode(charset, errors='replace')


def read_file(path, max_bytes):
    if path.stat().st_size > max_bytes:
        raise Refuse(f'{path} is larger than {max_bytes} bytes')
    return path.read_bytes().decode('utf-8-sig', errors='replace')


def paste_cache_text(prefix, cache_dir, max_age_hours):
    want = ''.join(prefix.split())
    if len(want) < 20:
        raise Refuse('give at least the first 20 characters of the pasted text')
    if not cache_dir.is_dir():
        raise Refuse(f'{cache_dir} does not exist')
    found = {}
    now = time.time()
    for p in sorted(cache_dir.glob('*.txt'), key=lambda q: q.stat().st_mtime, reverse=True):
        if now - p.stat().st_mtime > max_age_hours * 3600 or p.stat().st_size > MAX_BYTES:
            continue
        text = p.read_bytes().decode('utf-8-sig', errors='replace')
        if ''.join(text[:len(want) * 3 + 200].split()).startswith(want):
            found.setdefault(hashlib.sha256(text.strip().encode()).hexdigest(), (p, text))
    if not found:
        raise Refuse(f'no file in {cache_dir} newer than {max_age_hours} h starts with that text')
    if len(found) > 1:
        names = ', '.join(f'{p.name} ({len(t)} chars)' for p, t in found.values())
        raise Refuse(f'{len(found)} different cached texts start with that text: {names}; give more characters')
    (p, text), = found.values()
    return text, p.name


def decode_bounded(s):
    """Like bp.decode, but never expands more than MAX_DECOMPRESSED bytes (a compressed bomb is refused early)."""
    raw = base64.b64decode(s[1:], validate=True)
    d = zlib.decompressobj()
    out = d.decompress(raw, MAX_DECOMPRESSED)
    if d.unconsumed_tail:
        raise ValueError('the decompressed payload is larger than the limit')
    if not d.eof:
        raise ValueError('the compressed data is cut short')
    return json.loads(out)


def describe(s):
    """Decode a candidate string; return (object, kind) or raise ValueError."""
    obj = decode_bounded(s)
    if not isinstance(obj, dict):
        raise ValueError('the decoded value is not an object')
    return obj, bp.kind(obj)


def json_candidates(node, path='$'):
    """Yield (locator, string or object) for everything in a parsed JSON value that could be a blueprint."""
    if isinstance(node, dict):
        if any(k in node and isinstance(node[k], dict) for k in ALL_KINDS):
            yield path, node
            return
        for k, v in node.items():
            yield from json_candidates(v, f'{path}.{k}')
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from json_candidates(v, f'{path}[{i}]')
    elif isinstance(node, str):
        joined = ''.join(node.split())
        if WHOLE.fullmatch(joined):
            yield path, joined


def find_candidates(text):
    """Return a list of (locator, string, reencoded, object, kind) for every distinct string that decodes."""
    raw = []
    joined = ''.join(text.split())
    if WHOLE.fullmatch(joined):
        raw.append(('the whole text', joined, False))
    else:
        try:
            data = json.loads(text)
            raw += [(f'JSON {loc}', bp.encode(val) if isinstance(val, dict) else val, isinstance(val, dict))
                    for loc, val in json_candidates(data)]
        except (ValueError, RecursionError):
            pass  # not JSON, or nested too deeply to be a real blueprint file: scan the text instead
        if len(raw) > MAX_CANDIDATES:
            raise Refuse(f'more than {MAX_CANDIDATES} possible strings in the JSON; give a narrower source')
        if not raw:
            for m in SCAN.finditer(html.unescape(text)):
                raw.append((f'text, offset {m.start()}', m.group(0), False))
                if len(raw) > MAX_CANDIDATES:
                    raise Refuse(f'more than {MAX_CANDIDATES} possible strings in the text; give a narrower source')
    good, seen = [], set()
    for loc, s, reencoded in raw:
        if s in seen:
            continue
        seen.add(s)
        try:
            obj, kind = describe(s)
        except Exception:  # noqa: BLE001 - not a blueprint string; keep looking
            continue
        good.append((loc, s, reencoded, obj, kind))
    return good


def design_key(obj):
    """Canonical text of a blueprint or book without its cosmetic fields (label, description, icons, game version and
    the book's active index) at every level: two strings with the same key are the same design."""
    def strip(node):
        body = {k: v for k, v in node.items() if k not in COSMETIC}
        if isinstance(body.get('blueprints'), list):
            body['blueprints'] = [{k: strip(v) if k in KINDS and isinstance(v, dict) else v for k, v in item.items()}
                                  for item in body['blueprints'] if isinstance(item, dict)]
        return body

    kind = bp.kind(obj)
    return json.dumps({kind: strip(obj[kind])}, sort_keys=True, separators=(',', ':'))


def catalog_matches(s, obj):
    """(exact, same_design): the catalog file that holds exactly this string, and the first other file that holds the
    same design under another label, description, icons or game version. Each is None when there is none."""
    root = HERE.parent.parent
    key = design_key(obj)
    same = None
    for p in sorted((root / 'blueprints').glob('*/*.txt')):
        try:
            text = ''.join(p.read_text(encoding='utf-8').split())
            if text == s:
                return str(p.relative_to(root)), None
            if same is None and design_key(decode_bounded(text)) == key:
                same = str(p.relative_to(root))
        except (OSError, ValueError, KeyError, RecursionError, zlib.error):
            continue  # a file that is not a readable blueprint string cannot match
    return None, same


def summarize(obj, kind, s, source, found_in, reencoded, out):
    top = obj[kind]
    ents = Counter()
    n_bp = n_ent = 0
    largest = None
    for _, b in bp.walk(obj):
        n_bp += 1
        es = b.get('entities', [])
        n_ent += len(es)
        for e in es:
            ents[e.get('name')] += 1
        if es and (largest is None or len(es) > len(largest)):
            largest = es
    extent = None
    if largest:
        try:
            xs = [e['position']['x'] for e in largest]
            ys = [e['position']['y'] for e in largest]
            extent = [round(max(xs) - min(xs) + 1), round(max(ys) - min(ys) + 1)]
        except (KeyError, TypeError):
            pass  # an entity without a position: no extent, but the string is still good
    version = top.get('version')
    warnings = []
    if reencoded:
        warnings.append('the input was decoded JSON, so the string was encoded here (same content, new compression)')
    if isinstance(version, int) and not game_version(version).startswith('2.0.'):
        warnings.append(f'game version {game_version(version)}: the catalog accepts 2.0.x only')
    dup, same = catalog_matches(s, obj)
    if dup:
        warnings.append(f'this exact string is already in the catalog: {dup}')
    if same:
        warnings.append(f'this design is already in the catalog as {same}; only its label, description, icons or '
                        'game version differ')
    return {
        'source': source, 'found_in': found_in, 'kind': kind, 'duplicate_of': dup, 'same_design_as': same,
        'label': top.get('label') or '',
        'description': top.get('description', ''),
        'game_version': game_version(version) if isinstance(version, int) else None,
        'blueprints': n_bp, 'entities': n_ent, 'extent_tiles_approx_largest': extent,
        'top_entities': ents.most_common(8), 'bytes': len(s) + 1,
        'sha256': hashlib.sha256(s.encode()).hexdigest(), 'out': str(out), 'warnings': warnings,
    }


def run(args):
    if bool(args.source) == bool(args.from_paste_cache):
        raise Refuse('give either a source or --from-paste-cache')
    if args.allow_private and os.environ.get('EXTRACT_BLUEPRINT_ALLOW_PRIVATE') != '1':
        raise Refuse('--allow-private also needs EXTRACT_BLUEPRINT_ALLOW_PRIVATE=1 in the environment')
    if args.from_paste_cache:
        text, where = paste_cache_text(args.from_paste_cache, args.paste_cache_dir, args.max_age_hours)
        source = {'type': 'paste-cache', 'where': where}
    elif args.source == '-':
        text = sys.stdin.read()
        source = {'type': 'stdin', 'where': '-'}
    elif re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://', args.source):
        text = read_url(args.source, args.max_bytes, args.allow_private)
        source = {'type': 'url', 'where': args.source}
    else:
        path = Path(args.source).expanduser()
        if not path.is_file():
            raise Refuse(f'{args.source} is not a file, an http(s) URL or -')
        text = read_file(path, args.max_bytes)
        source = {'type': 'file', 'where': str(path)}
    if len(text) > args.max_bytes:
        raise Refuse(f'the text is larger than {args.max_bytes} bytes')
    found = find_candidates(text)
    if not found:
        hint = ''
        if text.lstrip().startswith(('{', '[')):
            try:
                json.loads(text)
            except (ValueError, RecursionError) as e:  # a JSONDecodeError names the line and column
                hint = f'; the text looks like JSON but does not parse ({e})'
        raise Refuse('no blueprint string found: nothing decodes (a copy with a typo fails the zlib checksum)' + hint)
    if args.pick is not None:
        if not 1 <= args.pick <= len(found):
            raise Refuse(f'--pick {args.pick} is outside 1..{len(found)}')
        found = [found[args.pick - 1]]
    if len(found) > 1:
        listing = [{'pick': i, 'found_in': loc, 'kind': k, 'label': o[k].get('label') or '', 'chars': len(s)}
                   for i, (loc, s, _, o, k) in enumerate(found, 1)]
        print(make_visible(json.dumps({'ambiguous': listing}, ensure_ascii=False, indent=1)))
        print(f'{len(found)} different blueprints found; nothing was written (choose one with --pick N)', file=sys.stderr)
        return 3
    loc, s, reencoded, obj, kind = found[0]
    if kind not in KINDS:
        raise Refuse(f'this is a {kind}; the catalog holds blueprints and blueprint books')
    if args.out.exists():
        raise Refuse(f'{args.out} already exists; it is never overwritten')
    if not args.out.parent.is_dir():
        raise Refuse(f'{args.out.parent} does not exist')
    summary = summarize(obj, kind, s, source, loc, reencoded, args.out)  # before writing: a failure leaves no file behind
    args.out.write_text(s + '\n', encoding='utf-8')
    print(make_visible(json.dumps(summary, ensure_ascii=False, indent=1)))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('source', nargs='?', help='a file, an http(s) URL, or - for stdin')
    ap.add_argument('--from-paste-cache', metavar='PREFIX', help='first characters of a text the user pasted')
    claude_dir = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')
    ap.add_argument('--paste-cache-dir', type=Path, default=claude_dir / 'paste-cache')
    ap.add_argument('--max-age-hours', type=float, default=6)
    ap.add_argument('--out', type=Path, required=True, help='where to write the string (must not exist)')
    ap.add_argument('--max-bytes', type=int, default=MAX_BYTES)
    ap.add_argument('--pick', type=int, metavar='N', help='when several blueprints are found, take the Nth (1-based)')
    ap.add_argument('--allow-private', action='store_true',
                    help='also fetch loopback and private addresses; needs EXTRACT_BLUEPRINT_ALLOW_PRIVATE=1 in the environment')
    args = ap.parse_args()
    try:
        return run(args)
    except Refuse as e:
        print(f'refused: {e}', file=sys.stderr)
    except Exception as e:  # noqa: BLE001 - every failure must end as exit 2 with a reason, never a traceback
        print(f'refused: unexpected {type(e).__name__}: {e}', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
