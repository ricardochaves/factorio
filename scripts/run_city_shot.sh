#!/bin/zsh
# usage: run_city_shot.sh [timeout-seconds]  -- runs scenario city-shot in the GUI game (screenshots need the renderer, so
# not headless) and converts the photos to blueprints/city-block-100x100-<variant>/images/*.webp.
# Photo names: script-output/city_<variant>__<shot>.png -> that variant's images/<shot, underscores turned into hyphens>.webp
# If Steam is open but not logged in, the game restarts through Steam and loses the arguments: SteamAppId=427520 ./run_city_shot.sh
HERE=${0:A:h}
python3 "$HERE/export_city.py" > /dev/null || exit 1
source "$HERE/factorio_env.sh"
rm -f data/script-output/city_shot_done.txt data/script-output/city_*.png(N)
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --load-scenario city-shot > city_shot.log 2>&1 &)
T=${1:-300}; S=$(date +%s)
while [ ! -f data/script-output/city_shot_done.txt ]; do
  sleep 2
  if ! pgrep -f "load-scenario city-shot" > /dev/null; then echo "factorio exited early (see ingame/city_shot.log)"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
sleep 2; pkill -f "load-scenario city-shot"; sleep 1
echo "elapsed $(( $(date +%s) - S ))s"
cat data/script-output/city_shot_done.txt 2>/dev/null
grep -iE "error|exception|traceback" city_shot.log | head -10
for f in data/script-output/city_*__*.png(N); do
  rest=${${f:t:r}#city_}                  # <variant>__<shot>
  variant=${rest%%__*}
  [[ $variant == (partial-concrete|full-concrete) ]] || { echo "skipping $f (unknown variant)"; continue; }
  OUT="$HERE/../blueprints/city-block-100x100-$variant/images"
  name=${${rest#*__}//_/-}
  mkdir -p "$OUT"
  cwebp -quiet -q ${WEBP_Q:-82} "$f" -o "$OUT/$name.webp" && echo "wrote ${OUT:h:t}/images/$name.webp"
done
