#!/bin/zsh
# usage: run_balancer_shot.sh [timeout-seconds]  -- runs scenario balancer-shot in the GUI game (screenshots need the
# renderer, so not headless) and converts the photos to blueprints/belt-balancers/images/*.webp.
# Run scripts/export_shots.py first (it writes the scenario's shots.lua).
HERE=${0:A:h}
source "$HERE/factorio_env.sh"
OUT="$HERE/../blueprints/belt-balancers/images"
rm -f data/script-output/balancer_shot_done.txt data/script-output/balancer_*.png(N)
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --load-scenario balancer-shot > balancer_shot.log 2>&1 &)
T=${1:-300}; S=$(date +%s)
while [ ! -f data/script-output/balancer_shot_done.txt ]; do
  sleep 2
  if ! pgrep -f "load-scenario balancer-shot" > /dev/null; then echo "factorio exited early"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
sleep 2; pkill -f "load-scenario balancer-shot"; sleep 1
echo "elapsed $(( $(date +%s) - S ))s"
cat data/script-output/balancer_shot_done.txt 2>/dev/null
grep -iE "error|exception" balancer_shot.log | head -10
mkdir -p "$OUT"
for f in data/script-output/balancer_*.png(N); do
  name=${${f:t:r}#balancer_}
  [[ $name == overview ]] || name=$name-8x8
  cwebp -quiet -q ${WEBP_Q:-82} "$f" -o "$OUT/$name.webp" && echo "wrote $OUT:t/$name.webp"
done
