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

## City block (`blueprints/city-block-100x100/`)

| Script | Purpose |
|---|---|
| `export_city.py` | Writes `strings.lua` for the two scenarios below from the blueprint files, with the entity, tile and wire counts the game must find (counted from the decoded JSON). Both runners call it. |
| `run_city_test.sh` | Headless scenario `city-test` (the server listens on 127.0.0.1 only). For both variants, with one block and with a 2 × 2 city: imports the string, builds it away from the cell's center to prove the grid snapping, checks every entity, tile and wire against the blueprint, plugs it into a power source, then checks the electric network, the roboports (status and energy), the lamps at night, the logistic network and the circuit networks, and lets the robots build four ghosts from a storage chest. Exit status 0 only when every check passed and at least one ran. |
| `run_city_shot.sh` | Scenario `city-shot` in the normal game (screenshots need the renderer): builds the variants on a grass field, powers them, waits for the roboports to fill their buffers, takes the photos (day, night, 2 × 2, details, robots in flight) and writes `images/*.webp`. |

## In-game harness (`ingame/`)

Factorio runs headless with an isolated write-data dir (`ingame/data`), vanilla only (`ingame/mods/mod-list.json`
enables just `base`). Scenarios live in `ingame/data/scenarios/`; their `control.lua` files are tracked, the test data
they read (`tests*.lua`, `tier.lua`, `bp.lua`, `strings.lua`) is generated.

Environment variables:

| Variable | Default | Used by |
|---|---|---|
| `FACTORIO_BIN` | Steam install under `~/Library/Application Support/Steam/...` | `run_*.sh` |
| `FBTIER` | `blue` | balancer scripts |
| `FBWARM` | depends on tier | `export_tests.py` (warm-up ticks) |
| `FBPHASES` | `ABCDEFGHI` | `export_tests.py` (measurement phases) |

`config.ini` is written on every run. Never commit anything else from `ingame/data`: `player-data.json` there holds
your Factorio account token.

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
