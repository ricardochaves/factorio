#!/bin/zsh
# usage: run_iron_copper_shot.sh [timeout-seconds]  -- runs scenario iron-copper-shot (the iron/copper smelter) in the GUI game
# (screenshots need the renderer, so not headless): measures ore in, plates out and power for three non-stack inserter
# capacity bonuses, takes the photo once every electric furnace is working and converts it to
# blueprints/iron-copper-smelter/images/overview.webp. When the scenario writes a line starting with FAIL: (some check did
# not hold, for example the furnaces were not all working 900 ticks after the last window) this script exits 1 without
# rewriting the image. The measurements are printed and kept in ingame/data/script-output/iron_copper_shot_done.txt.
# Exit status: 0 image rewritten; 1 the run failed (the Factorio binary was not found, the game exited or the scenario raised
# an error early, timeout, no result, a FAIL: line, no new photo); 2 pre-flight refused it (blueprint unreadable or not a
# blueprint string, cwebp missing).
# If Steam is open but not logged in, the game restarts through Steam and loses the arguments: SteamAppId=427520 ./run_iron_copper_shot.sh
HERE=${0:A:h}
BP="$HERE/../blueprints/iron-copper-smelter/iron-copper-smelter.txt"
[ -r "$BP" ] || { echo "cannot read $BP"; exit 2; }
command -v cwebp > /dev/null || { echo "cwebp is needed to write the image (brew install webp)"; exit 2; }
# a blueprint string is a version digit plus base64: anything else must not be written into a Lua string
[[ "$(cat "$BP")" =~ '^[0-9A-Za-z+/=]+$' ]] || { echo "$BP does not look like a blueprint string"; exit 2; }
source "$HERE/factorio_env.sh"
printf 'return "%s"\n' "$(cat "$BP")" > data/scenarios/iron-copper-shot/bp.lua
# a result of an earlier run is never taken for this one: only files newer than this marker count
MARK=data/script-output/.iron_copper_shot_start
touch "$MARK"
T=${1:-600}; S=$(date +%s)
# the game is tracked by its process id, so nothing else is ever stopped and a leftover game is never mistaken for this one
"$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --load-scenario iron-copper-shot > iron_copper_shot.log 2>&1 &!
GAME=$!
trap 'kill $GAME 2>/dev/null; exit 130' INT TERM HUP
ABORT=""
sleep 5
while ! [ data/script-output/iron_copper_shot_done.txt -nt "$MARK" ]; do
  sleep 3
  if ! kill -0 $GAME 2>/dev/null; then ABORT="factorio exited early (see ingame/iron_copper_shot.log)"; break; fi
  if grep -q "Error while running" iron_copper_shot.log; then ABORT="the scenario raised an error"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then ABORT="timeout"; break; fi
done
# a result that appeared while this run's game was not running is a leftover of another run, never this one's
kill -0 $GAME 2>/dev/null || ABORT=${ABORT:-"factorio was not running when the result appeared"}
# stop the game and wait until it is gone, so that a run started right afterwards can take the write-data lock
kill $GAME 2>/dev/null
for i in {1..20}; do kill -0 $GAME 2>/dev/null || break; sleep 1; done
kill -0 $GAME 2>/dev/null && kill -KILL $GAME 2>/dev/null
echo "elapsed $(( $(date +%s) - S ))s"
grep -iE "error|exception|traceback" iron_copper_shot.log | head -10
if [ -n "$ABORT" ]; then echo "$ABORT: images/overview.webp was NOT rewritten"; exit 1; fi
if ! [ data/script-output/iron_copper_shot_done.txt -nt "$MARK" ]; then echo "no result: the scenario did not finish"; exit 1; fi
cat data/script-output/iron_copper_shot_done.txt
if grep -q '^FAIL:' data/script-output/iron_copper_shot_done.txt; then echo "images/overview.webp was NOT rewritten (see the FAIL lines)"; exit 1; fi
if ! [ data/script-output/iron_copper_overview.png -nt "$MARK" ]; then echo "no new photo was written: images/overview.webp was NOT rewritten"; exit 1; fi
OUT="$HERE/../blueprints/iron-copper-smelter/images"
mkdir -p "$OUT"
cwebp -quiet -q ${WEBP_Q:-82} data/script-output/iron_copper_overview.png -o "$OUT/overview.webp" && echo "wrote ${OUT:h:t}/images/overview.webp"
