# Contributing

This repository holds vanilla Factorio 2.0 blueprints and the website that publishes them
(<https://ricardochaves.github.io/factorio/>). Write pull requests, commit messages and code comments in English. Everything the
website shows exists in Brazilian Portuguese, English and Spanish: the metadata of each blueprint and its README too.

## How a change reaches `main`

1. Work on a branch created from `main`. Without write access to this repository, fork it and work on your fork.
2. Open a pull request against `main`. Two workflows run on it (on a pull request from a first-time contributor's
   fork, they start only after a maintainer approves the run):
   - **Validate blueprints**, job `validate` ([`validate.yml`](.github/workflows/validate.yml)): checks the metadata,
     decodes every blueprint string, rejects anything that is not vanilla Factorio 2.0 and fails if the catalog table
     in [`README.md`](README.md) is out of date. It must pass before the pull request can be merged.
   - **Site**, job `build` ([`pages.yml`](.github/workflows/pages.yml)): builds the website, to catch errors. It is
     not a required check, but keep it green: after the merge, the same build must pass before the site is published.
3. A maintainer (today, [@ricardochaves](https://github.com/ricardochaves)) reviews it. One approving review is
   required, and it must come after the most recent push: new commits that change the pull request need a new
   approval.
4. The pull request is merged with **squash**, the only merge method enabled, so it lands on `main` as a single
   commit. If its branch is in this repository, GitHub deletes it after the merge.

`main` cannot be deleted or force-pushed, and it only takes changes through pull requests. The repository owner is
the only one who can bypass these rules, which is how they merge their own pull requests: GitHub does not let authors
approve their own.

### The pull request title is what players read

The website shows the title of each commit on `main` that changed a blueprint's `.txt` file: in the **Git history** of
that blueprint's page and, for the four most recent, in **What's new** on the home page. With squash merges, that
title is the pull request title when the pull request has more than one commit, and the commit title when it has only
one (GitHub's default, which can be edited in the merge dialog). GitHub adds ` (#N)` at the end; the website hides it.

So write the pull request title for players, and the commit title too in single-commit pull requests. For example:
`Oil refinery: double the water feed of the sulfuric acid block`.

## Adding a blueprint

1. Create one folder per catalog entry, `blueprints/<slug>/` (lower-case words joined by `-`). One entry is one page on
   the site. Files share a folder only when they are parts of one book-like entry, such as the three belt-tier books of
   `belt-balancers/`; a blueprint that differs from another in what it builds (for example, the partial and full
   concrete versions of the city block) gets its own folder and its own page, and the two READMEs point to each other.
   The folder holds:
   - the `.txt` file: a single blueprint or a book (several files only for the book-like entries above);
   - `blueprint.toml`, the hand-written metadata (copy one from another folder);
   - `README.md` in Portuguese, with `README.en.md` and `README.es.md` as its English and Spanish translations: what
     it does, inputs and outputs, how it was tested, known limits (the website shows the README of the page's language
     as the blueprint's report, one card per `##` section). The translations keep the headings, tables, links, code
     spans and code blocks of `README.md`, which the validator checks;
   - `images/` (WebP): one real screenshot taken in the game per new entry, listed in `blueprint.toml` (the validator
     requires at least one, and the maintainer's review asks to remove a second). The machines in the shot must be
     working (powered, fed), so no "not working" icon shows up. The exception is the photos taken by this repository's
     Claude Code command `/add-blueprint` (`.claude/commands/add-blueprint.md`): they show the build placed and powered
     (the test wires its power source to every group of poles), with no ingredients fed to the machines, and are taken without alt
     mode, so they carry no status icon.
2. Run `python3 scripts/catalog/validate.py --readme` (Python 3.11 or newer, standard library only). It checks the
   metadata, decodes every string and rejects anything that is not vanilla Factorio 2.0 (Space Age entities, quality
   other than normal, other game versions). It also rejects a missing translation, a translated README whose structure differs from `README.md`, and text in
   the metadata or in the entry's READMEs that holds
   zero-width characters, bidirectional controls, other control or format characters or fillers that draw nothing, and
   paths listed in `blueprint.toml` that do not start with a letter or digit or hold anything but letters, digits, `.`,
   `_`, `-` and `/`. Then it refreshes the catalog table in [`README.md`](README.md). Commit the refreshed table with
   the blueprint: the `validate` check fails when it is out of date. Entity counts, size, materials and recipes are
   computed from the string, never typed by hand.
3. Optionally test it in the game with the harness in [`scripts/`](scripts/).
4. Open a pull request, as described [above](#how-a-change-reaches-main). A new version overwrites the same `.txt`
   file and git keeps the history, so never add `-v2` copies.

A blueprint string is one long base64 line. To see its changes entity by entity in `git diff` and `git log -p`,
enable the diff driver once per clone:

```
git config diff.factorio-blueprint.textconv "python3 scripts/bp_textconv.py"
```

The driver runs `scripts/bp_textconv.py` from your working tree, so after checking out a branch you do not trust, read
any change to that script before running `git diff` or `git log -p`.

### `blueprint.toml` fields

| Field | Required | Meaning |
|---|---|---|
| `title`, `summary` | yes | Name and one-sentence description, in Portuguese. |
| `category` | yes | One of `belts`, `mining-smelting`, `oil`, `production`, `science`, `power`, `trains`, `bots`, `city-blocks`, `circuits`, `defense`, `rocket`. |
| `tags` | yes | Lower-case words, e.g. `["early-game", "blue-belt"]`. |
| `[[files]]` | yes, 1+ | One entry per `.txt` file (usually one): `name` shown to players, with its translations `name_en` and `name_es`, and `path` of its `.txt` file. Every `.txt` in the folder must be listed, from the simplest variant to the most advanced; the website opens on the last one. |
| `[[images]]` | yes, 1+ | `path` and `alt` text, with its translations `alt_en` and `alt_es`. The first image is the card cover. |
| `[test]` | no | `status` = `in-game`, `simulation` or `untested`; `game_version`; `report` (usually `README.md`). |
| `credits` | no | Where the design came from, in Markdown (links allowed). |
| `[en]`, `[es]` | yes | English and Spanish `title` and `summary`, and `credits` when the blueprint has credits. Nothing falls back to Portuguese. |
| `viewer` | no | Special page layout; today only `nxm-matrix` (balancer books labeled `N to M`). Its panel states, for every balancer, that it passed the flow simulation, the 9-phase in-game test and (with a splitter) the independent checker, so use it only for books that passed all three, as the belt balancers did. |

### Choosing the category of a city block

A roboport grid becomes a city block when it defines the terrain of the whole base: a fixed lot size, standard edges
and the same lot repeated across the map. Every city block has a roboport grid, but not every roboport grid is a city
block.

- `city-blocks`: the lot template itself, with its edges, intersections and standard station. Tag the kind (`rail` or
  `bot-only`) and the lot size (for example `100x100`).
- `bots`: standalone pieces, such as a loose roboport grid, a recharge station or a storage hub.
- A production block built to fit a lot (for example green circuits for a 100x100 city) goes in its product's
  category with the tag `city-block`.

## The website

The site is generated by [`site/build.py`](site/build.py) (Python, Jinja2, no JavaScript framework) and published to
GitHub Pages by [`.github/workflows/pages.yml`](.github/workflows/pages.yml) on every push to `main`. Pull requests
build it too, to catch errors. To preview it locally (Python 3.11 or newer):

```
python3 -m venv .venv && .venv/bin/pip install -r site/requirements.txt
.venv/bin/python site/build.py
python3 -m http.server -d build/site 8000     # http://localhost:8000/
```

It supports three languages, always kept in sync: Brazilian Portuguese at `/`, US English at `/en/` and Spanish at
`/es/`. Interface text lives in [`site/i18n.py`](site/i18n.py); names of items and recipes come from the game's own
translations ([`scripts/catalog/vanilla-locale.json`](scripts/catalog/vanilla-locale.json), refreshed by
`scripts/catalog/dump_locale.py`). Each blueprint page shows the README of its language (`README.md`, `README.en.md` or `README.es.md`), and the build
fails when a translation is missing.

Visits are measured with Google Analytics 4, but only after the visitor accepts the banner
([`site/static/analytics.js`](site/static/analytics.js)): nothing from Google loads before that, or on any host other
than `ricardochaves.github.io`. The measurement id is public, not a secret. A fork's CI build has no analytics and no
privacy page unless it sets `GA_MEASUREMENT_ID` (a build in a clone falls back to this project's id, and stays silent
because of the host check). What the tag collects, the cookies, the retention time and the account's data-sharing
settings are described in `site/content/privacy.<language>.md`: change those three files whenever the tag or the
Analytics settings change. The event `copy_blueprint` (parameter `blueprint_file`) only appears in reports because
"Blueprint file" is registered as an event-scoped custom dimension in the property.
