#!/usr/bin/env python3
"""Install a catalog entry that /add-blueprint built in its scratch directory into blueprints/.

usage:
  python3 scripts/catalog/install_entry.py <entry-root> <slug>

<entry-root> is build/add-blueprint.<random>/root (or root-<k>) of this repository, and it holds blueprints/<slug>/. The tool
copies that folder to blueprints/<slug>/ and nothing else, so that a command which only lets it run cannot put anything else in
the folder the owner commits: it refuses a slug that is not lower-case words joined by "-", an entry root anywhere but
build/add-blueprint.*/ of this repository, a target that already exists, a symbolic link, any file that is not
`blueprint.toml`, `README.md`, a `.txt` string in the folder or a `.webp` photo in images/, and an entry that the catalog
validator (validate.py) rejects. The copy goes to a temporary folder in build/, the validator runs over that copy, and the
folder is moved into place in one step, so a failure leaves no half-installed entry and what is validated is what is
installed; each file is opened without following a link and must be a regular file. Nothing is overwritten and nothing of the
entry is deleted. It prints `installed blueprints/<slug> (<n> files)` and exits 0, or prints `refused: <reason>` (or
`failed: <reason>` for an input or output error) and exits 2. Standard library only (Python 3.11+).
"""
import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SLUG = re.compile(r'[a-z0-9]+(-[a-z0-9]+)*')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*')
ROOT_NAME = re.compile(r'root(-[0-9]+)?')


class Refuse(Exception):
    """The entry cannot be installed; the message says why."""


def entry_folder(entry_root, slug):
    """The folder blueprints/<slug>/ inside the scratch entry root, after checking where it is."""
    if not SLUG.fullmatch(slug):
        raise Refuse(f'"{slug}" is not lower-case words joined by "-"')
    root = Path(entry_root).resolve()
    scratch = root.parent
    if scratch.parent != REPO / 'build' or not scratch.name.startswith('add-blueprint.') or not ROOT_NAME.fullmatch(root.name):
        raise Refuse(f'{entry_root} is not build/add-blueprint.*/root of this repository')
    src = root / 'blueprints' / slug
    if src.resolve() != src or not src.is_dir():
        raise Refuse(f'{src} is not a folder (or a link leads elsewhere)')
    return src


def unreadable(error):
    raise error  # os.walk skips a folder that it cannot list unless it is told to raise


def files_to_copy(src):
    """The paths, relative to `src`, of every file to copy, after checking each entry of the tree."""
    files = []
    for folder, dirnames, filenames in os.walk(src, followlinks=False, onerror=unreadable):  # a link to a folder is listed only
        dirnames.sort()
        for name in dirnames + sorted(filenames):
            p = Path(folder) / name
            rel = p.relative_to(src)
            if p.is_symlink():
                raise Refuse(f'{rel} is a symbolic link')
            if p.is_dir():
                if rel.parts != ('images',):
                    raise Refuse(f'{rel} is a folder other than images/')
                continue
            if not p.is_file():
                raise Refuse(f'{rel} is not a regular file')
            parts = rel.parts
            top = len(parts) == 1 and (parts[0] in ('blueprint.toml', 'README.md') or
                                       (parts[0].endswith('.txt') and NAME.fullmatch(parts[0])))
            photo = len(parts) == 2 and parts[0] == 'images' and parts[1].endswith('.webp') and NAME.fullmatch(parts[1])
            if not (top or photo):
                raise Refuse(f'{rel} is not a file of a catalog entry')
            files.append(rel)
    if not files:
        raise Refuse(f'{src} holds no file')
    return files


def run_validator(root):
    """The catalog validator over the entry root: the files were named right, and their content has to be right too."""
    tool = REPO / 'scripts' / 'catalog' / 'validate.py'
    done = subprocess.run([sys.executable, '-B', str(tool), '--root', str(root)], capture_output=True, text=True)
    if done.returncode != 0:
        # ascii(): the messages can quote text from the entry, and an escape or a bidirectional control must not reach a terminal
        raise Refuse('the validator rejects the entry: ' + ascii(' '.join(done.stderr.split())[:300]))


def copy_regular(source, target):
    """Copy one file, opened without following a link and without blocking on a pipe; it must be a regular file."""
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as a:
        if not stat.S_ISREG(os.fstat(a.fileno()).st_mode):
            raise Refuse(f'{source} is not a regular file')
        with open(target, 'xb') as b:
            shutil.copyfileobj(a, b)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('entry_root', help='build/add-blueprint.<random>/root or root-<k>')
    ap.add_argument('slug', help='the folder name under blueprints/')
    args = ap.parse_args()
    stage = None
    try:
        src = entry_folder(args.entry_root, args.slug)
        files = files_to_copy(src)
        target = REPO / 'blueprints' / args.slug
        if target.exists() or target.is_symlink():
            raise Refuse(f'blueprints/{args.slug} already exists; it is never overwritten')
        stage = Path(tempfile.mkdtemp(prefix='install.', dir=REPO / 'build'))
        staged = stage / 'blueprints' / args.slug
        staged.mkdir(parents=True)
        for rel in files:
            (staged / rel).parent.mkdir(exist_ok=True)
            copy_regular(src / rel, staged / rel)
        run_validator(stage)  # over the copy, so that what is validated is exactly what is installed
        os.rename(staged, target)  # one step, and it fails when the target exists and is not empty
        print(f'installed blueprints/{args.slug} ({len(files)} files)')
        return 0
    except Refuse as e:
        print(f'refused: {e}', file=sys.stderr)
    except OSError as e:
        print(f'failed: {type(e).__name__}: {e}', file=sys.stderr)
    finally:
        if stage is not None:
            shutil.rmtree(stage, ignore_errors=True)  # the tool's own temporary folder, whatever happened
    return 2


if __name__ == '__main__':
    sys.exit(main())
