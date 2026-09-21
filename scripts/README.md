# Scripts

Tools used to build and verify the blueprints. You do not need any of this to *use* the blueprints.

Everything runs with Python 3 (standard library only) on macOS; the in-game tests need Factorio 2.0 installed.

## Blueprint strings

| Script | Purpose |
|---|---|
| `bp.py` | Decode / encode blueprint strings, walk books. |
| `bp_textconv.py` | `git diff` driver that shows blueprint changes entity by entity (see below). |
| `render.py` | ASCII view of one balancer: `python3 render.py <book.txt> "4 to 4"`. |

## Catalog (`catalog/`)

| File | Purpose |
|---|---|
| `validate.py` | Checks every `blueprints/*/blueprint.toml`, decodes each string, rejects non-vanilla names, non-normal quality and game versions other than 2.0, and computes entities, size, materials and recipes. `--json build/catalog.json` writes the index for the site; `--readme` refreshes the table in the root README. Runs in CI (`.github/workflows/validate.yml`). |
| `extract_blueprint.py` | Takes a blueprint string out of a file (`.txt`, `.json`, HTML), an http(s) URL, stdin or Claude Code's paste cache, proves that it decodes (zlib checksum, size limits, public addresses only) and writes it to a new file with a JSON summary that also says whether the catalog already holds that string or the same design under another label. It is the first step of the `/add-blueprint` command (`.claude/commands/add-blueprint.md`). |
| `run_blueprint_shot.sh` | The photo step of `/add-blueprint`: `./run_blueprint_shot.sh <blueprint.txt> <out-dir> [timeout-seconds]` builds a blueprint, or the first four of a book, in the game (scenario `blueprint-shot`, see "In-game harness"), powers it where its source reaches the poles, photographs its whole extent and, only after a successful run, writes `<out-dir>/shot-<n>.webp`, replacing any already there. Needs the game and `cwebp`. |
| `vanilla-prototypes.json` | Every prototype name of the base game (entities with tile size and the item that places them, items, recipes, fluids, tiles, signals, quality). |
| `dump_prototypes.sh` | Regenerates the file above from the local game with scenario `ingame/data/scenarios/dump-prototypes`; it refuses to save if any mod other than `base` is active. Re-run after a Factorio update. |
| `vanilla-locale.json` | In-game names of items, entities, recipes and fluids in English, Brazilian Portuguese and Spanish, used by the website. |
| `dump_locale.py` | Regenerates the file above from the game's locale files (`$FACTORIO_BIN` or the Steam install). Re-run after a Factorio update. |

## Belt balancers

| Script | Purpose |
|---|---|
| `tier.py` | Belt tier from env `FBTIER` = `blue` (default), `red` or `yellow`. |
| `sim.py`, `csim.c`, `csim_dyn.c` | Flow simulator with back-pressure (C kernels loaded through ctypes). |
| `library.py` | Verified building blocks: the base book plus Raynquist's book. |
| `compose.py`, `reverse.py`, `weave.py`, `ugfix.py` | Block composition, flow reversal, 2N cores, underground-length fixes. |
| `gen.py` → `build_book.py` | Generate all 576 pairs, then write `blueprints/belt-balancers/<tier>-belt.txt` (overwrites; git keeps history). |
| `check_book.py`, `deep_verify.py` | Quick / heavy simulation of every blueprint in a book. |
| `export_tests.py` → `run_ingame.sh` → `analyze_ingame.py` | In-game test: build, feed and measure every blueprint (9 phases). |
| `run_tier_ingame.sh <tier>`, `final_pipeline.sh` | The above chained. |
| `calibrate.py` | Compares the simulator with in-game measurements. |
| `xcheck/xcheck.py` | Independent check with [tzwaan/factorio_balancers](https://github.com/tzwaan/factorio_balancers). |

## Oil refinery (`fluid/`)

| Script | Purpose |
|---|---|
| `fluidnet.py`, `label.py`, `gasgraph.py` | Fluid segments and pumps, fluid per segment, gas graph. |
| `make_full_test.py` → `run_fluid.sh` → `summarize.py` / `balance.py` | In-game test of the whole refinery (label suffix picks the regime: `-inlet`, `-surplus`, `-plasticonly`). |
| `crop_plastic.py` | Cuts a plastic block into an isolated test. |
| `patch_plastic_feed.py`, `patch_water_acid.py` | Historical one-off patches that produced refinery v2 and v3. |

## Iron/copper smelter (`blueprints/iron-copper-smelter/`)

| Script | Purpose |
|---|---|
| `run_iron_copper_shot.sh` | Scenario `iron-copper-shot` in the normal game: builds the smelter on a grass field, fulfils its module requests, powers it and feeds iron ore through a loader and an infinity chest, measures ore in, plates out and electric power for three non-stack inserter capacity bonuses (+0, +1, +2: research none, inserter capacity bonus 2 and 7), takes the photo once all the electric furnaces are working and writes `blueprints/iron-copper-smelter/images/overview.webp`. It exits with 1 and keeps the old image when a check does not hold (see the harness section below). |

## City block (`blueprints/city-block-100x100-partial-concrete/` and `-full-concrete/`)

| Script | Purpose |
|---|---|
| `export_city.py` | Writes `strings.lua` for the two scenarios below from the two blueprint files, with the entity, tile and wire counts the game must find (counted from the decoded JSON). It refuses a blueprint that is not mirror-symmetric (tiles and entities), because neighboring blocks only line up when each side mirrors the side facing it. Both runners call it. |
| `run_city_test.sh` | Headless scenario `city-test` (the server listens on 127.0.0.1 only). For both variants in 1 × 1, 2 × 1, 1 × 2, 2 × 2 and 3 × 3 arrangements, and for the two variants side by side in a checkerboard: imports the string, builds it away from the cell's center to prove the grid snapping, checks every entity, tile and wire against the blueprint, compares tile by tile the two faces of every seam between blocks (the street must be paved without gaps), plugs it into a power source, then checks the electric network, the roboports (status and energy), the lamps at night, the logistic network and the circuit networks, and lets the robots build ghosts in the middle of the first block and across a seam. Exit status 0 only when every check passed and at least one ran. |
| `run_city_shot.sh` | Scenario `city-shot` in the normal game (screenshots need the renderer): builds each variant on a grass field as one block and as a 2 × 2 city, powers them, waits for the roboports to fill their buffers, takes the photos (day, night, 2 × 2, where four blocks meet, the street between two blocks, details, robots in flight) and writes each variant's `images/*.webp`. |

## Stone brick smelter (`blueprints/stone-brick-smelter/`)

| Script | Purpose |
|---|---|
| `export_smelter.py` | Writes `strings.lua` for the scenario below from the blueprint file, with the entity and module counts the game must find (counted from the decoded JSON). It refuses a blueprint whose southernmost express belt (the stone input) does not face north, or whose northernmost express underground belt (the brick output) is not a north-facing exit: that is where the scenario feeds and drains it. It also refuses a tie at either end, anything but exactly one substation (the scenario wires a second one to it) and fewer than four electric furnaces (the scenario reads the fourth). The runner calls it. |
| `run_smelter_test.sh` | Headless scenario `smelter-test` (the server listens on 127.0.0.1 only). Imports the string, checks its entities, modules, single electric network and power, feeds it a full express belt of stone (infinity chest and express loader) and, after a 60 s warm-up, measures for 60 s (game time) the stone consumed, the bricks made and how long each furnace works, then reads the electric power drawn, once with every technology researched and once with none, on two surfaces in the same run. Only the run with every technology asserts the throughput (stone within 98 % to 101 % of a full express belt, 45/s, and bricks within 98 % to 101 % of what that stone yields, 45 / 2 × 1.2 = 27/s; every furnace working at least a quarter of the window); the run with none only gets the static and power checks, and its numbers are reported. Exit status 0 only when every check passed and at least one ran. |

## In-game harness (`ingame/`)

Factorio runs headless with an isolated write-data dir (`ingame/data`), vanilla only (`ingame/mods/mod-list.json`
enables just `base`). Scenarios live in `ingame/data/scenarios/`; their `control.lua` files are tracked; the rest is
generated and git-ignored: the test data they read (`tests*.lua`, `tier.lua`, `bp.lua`, `shots.lua`, `strings.lua`,
`book.lua`) and the `tests*.json` that `fluid/crop_plastic.py` writes next to `tests.lua`.

Scenario `bookimport` checks that a whole book imports in the game (sub-books, blueprints with entities). Write its
input, run it headless and stop the server once `ingame/data/script-output/bookimport.txt` appears (needs
`ingame/config.ini` from any `run_*.sh` and `FACTORIO_BIN` exported):

```
printf 'return "%s"\n' "$(cat ../blueprints/belt-balancers/blue-belt.txt)" > ingame/data/scenarios/bookimport/book.lua
"$FACTORIO_BIN" --config "$PWD/ingame/config.ini" --mod-directory "$PWD/ingame/mods" --start-server-load-scenario bookimport --server-settings "$PWD/ingame/server-settings.json"
```

Environment variables:

| Variable | Default | Used by |
|---|---|---|
| `FACTORIO_BIN` | Steam install under `~/Library/Application Support/Steam/...` | `run_*.sh` |
| `FBTIER` | `blue` | balancer scripts |
| `FBWARM` | depends on tier | `export_tests.py` (warm-up ticks) |
| `FBPHASES` | `ABCDEFGHI` | `export_tests.py` (measurement phases) |

`config.ini` is written on every run. Never commit anything else from `ingame/data`: `player-data.json` there holds
your Factorio account token. Every runner that starts the headless server passes `--bind 127.0.0.1`, so nothing outside
your machine can connect to the game while a test runs.

Screenshots of the refinery come from scenario `fluid-shot`, which needs the normal (non-headless) game
(`ingame/config.ini` is created by any `run_*.sh`):

```
printf 'return "%s"\n' "$(cat ../blueprints/oil-refinery/oil-refinery.txt)" > ingame/data/scenarios/fluid-shot/bp.lua
"$FACTORIO_BIN" --config "$PWD/ingame/config.ini" --mod-directory "$PWD/ingame/mods" --load-scenario fluid-shot
cwebp -q 82 ingame/data/script-output/refinaria_v3_full.png -o ../blueprints/oil-refinery/images/overview.webp
```

Photos of the belt balancers come from scenario `balancer-shot`, also with the normal game. `export_shots.py` copies
the same balancer (default `8 to 8`) from the three books into the scenario's `shots.lua`; the scenario feeds every
input and drains every output with loaders and infinity chests 8 tiles away (outside the frames), warms up 3600 ticks,
checks that every output belt is compressed and takes the photos. `run_balancer_shot.sh` runs the game, waits and writes
`blueprints/belt-balancers/images/{overview,yellow-8x8,red-8x8,blue-8x8}.webp`:

```
python3 export_shots.py
./run_balancer_shot.sh
```

If Steam is open but not logged in, the game asks to restart through Steam and loses the arguments; run
`SteamAppId=427520 ./run_balancer_shot.sh` instead.

Photos of the city block come from scenario `city-shot` the same way (`./run_city_shot.sh`, with the `SteamAppId=427520`
prefix when Steam is open but not logged in). Its shots are listed at the top of
`ingame/data/scenarios/city-shot/control.lua` (center, size in tiles, zoom, daytime); the power source sits 20 tiles west
of the block, outside every frame except its copper wire.

Photos of any blueprint or blueprint book come from scenario `blueprint-shot`, through `./run_blueprint_shot.sh <blueprint.txt>
<out-dir> [timeout-seconds]`. It needs the normal (non-headless) game, whose window opens for about half a minute, and `cwebp`
(`brew install webp`).

- **Input and exit status.** The file holds one bare blueprint string on one line. The script exits 2 for anything else, for a
  usage error, a missing file, a timeout that is not a whole number and a second run in the same checkout (which would share
  `ingame/data`). It exits 1 for every other failure: no `cwebp` or game binary, a folder or file it cannot create, or a
  failed run. It exits 0 only when every photo that the report announces was written and the report has no line that starts
  with `FAIL`. It sets `SteamAppId=427520` itself.
- **Output.** Each photo is converted into a staging folder first. Only a successful run moves the new `shot-<n>.webp` into
  `<out-dir>`, replacing the file of the same number, and removes the higher-numbered ones that an older run left; a failed run
  leaves the files there as they were (a new `<out-dir>` is still created, empty).
- **Report.** A `shots=<n> total=<m>` line (photos taken, blueprints found) and, for each blueprint, `<built> of <all> entities
  built` followed by the names of those not built, and one power note: `N of M pole groups without power (source <side>)`
  (M counts the groups that the build's poles form, and `, first at (x, y)` follows for the first three) or `no poles in the
  build`; when no side accepts the source, the note is `the power source could not be placed`, followed by a `FAIL:` line. A
  step that fails adds a `FAIL:` line: an import that fails or reports errors, a string without a blueprint, a build that is
  empty, that cannot place its power source or that reaches more than 1300 tiles from the origin of its coordinates (the limit
  bounds the chunks that the game must generate), an error while building, or a photo that could not be taken.
- **What the photo shows.** The game builds what can stand on grass and skips the rest without leaving a ghost, so a pumpjack
  (needs oil) or an offshore pump (needs water) is missing and named in the report. The power source, a big pole and an energy
  interface, stands 5 tiles outside the build (when it has poles), level with the build's pole nearest to that side. The
  scenario tries east, north, west and south, each on its own, and keeps the side where the source reaches the most pole
  groups, which the note names; a pole joins it only within its wire reach, so poles deeper inside can stay unpowered, and on
  the west and south sides a strip of the pole's shadow or its tower can enter the margin. No ingredients are fed to the
  machines (the modules and fuel that the blueprint requests are inserted), so a photo shows the build, not a running factory.
  The photos are taken without alt mode (`show_entity_info = false`), so they carry no status icon; a machine with a recipe and
  no ingredients showed none, with power and without it.

The iron/copper smelter is photographed and measured by its own scenario, `iron-copper-shot`, because `blueprint-shot`
feeds no ingredients and the machines in this photo must be working (`CONTRIBUTING.md`). Run it with
`./run_iron_copper_shot.sh`, with the `SteamAppId=427520` prefix when Steam is open but not logged in; it needs `cwebp` to
write the image. The runner writes the scenario's `bp.lua` from
`blueprints/iron-copper-smelter/iron-copper-smelter.txt`. Reviving the ghosts by script leaves the blueprint's module
requests as item-request proxies, so the scenario fulfils them itself. Each non-stack inserter capacity bonus (+0, +1,
+2) warms up 18000 ticks and is measured over 3600 ticks, counting ore and plates with the game's production statistics
and power by draining an energy interface; it also logs the plates and ore waiting in the furnaces so that a steady state
can be checked. The ore source, the drain and the power source sit outside the frame, except the copper wire that leaves
it at the bottom left. The photo waits until all the electric furnaces are working. The scenario writes a `FAIL:` line,
and the runner then exits with 1 and leaves `images/overview.webp` as it was, when the ghosts do not all revive or the
modules are missing, the big pole is not wired, the ore line is not full when a window starts, a window has no ore or no
plates, the furnace buffers moved by more than 2 % of the flow in a window, or the furnaces are still not all working 900
ticks after the last window (the photo is taken anyway, so that it can be looked at). The runner also stops when the
scenario raises a Lua error, and it only trusts result files newer than its start. It exits with 2, before starting the
game, when the blueprint file is unreadable or is not a blueprint string, or `cwebp` is missing. The measurements end up
in `ingame/data/script-output/iron_copper_shot_done.txt` and are the numbers in the entry's README.

## Setup after a fresh clone

```
cd scripts
cc -O3 -shared -fPIC -o csim.so csim.c
cc -O3 -shared -fPIC -o csim_dyn.so csim_dyn.c

# Inputs of the balancer generator (not redistributed here)
mkdir -p sources
curl -L -o sources/raynquist_github.txt https://raw.githubusercontent.com/raynquist/balancer/master/blueprints/balancer_book.txt
# sources/original-balancers.txt is the base book the project started from; it is not published.

# Third-party checker
git clone https://github.com/tzwaan/factorio_balancers xcheck/factorio_balancers
python3 -m venv xcheck/venv && xcheck/venv/bin/pip install py_factorio_blueprints==0.2.5 progress==1.6.1

# Readable blueprint diffs
git config diff.factorio-blueprint.textconv "python3 scripts/bp_textconv.py"
```
