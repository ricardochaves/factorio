#!/bin/zsh
# usage: run_ingame.sh [timeout-seconds]  -- runs scenario balancer-test headless (env FACTORIO_BIN overrides the binary)
HERE=${0:A:h}
source "$HERE/factorio_env.sh"
rm -f data/script-output/balancer_results_*.json(N) data/script-output/balancer_done.txt
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --start-server-load-scenario balancer-test --server-settings "$PWD/server-settings.json" --port 34987 > run.log 2>&1 &)
T=${1:-1800}; S=$(date +%s)
while [ ! -f data/script-output/balancer_done.txt ]; do
  sleep 3
  if ! pgrep -f "start-server-load-scenario balancer-test" > /dev/null; then echo "factorio exited early"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
pkill -f "start-server-load-scenario balancer-test"; sleep 2
echo "elapsed $(( $(date +%s) - S ))s"; ls data/script-output/
grep -iE "error|script" run.log | head -10
