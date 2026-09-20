#!/bin/zsh
# usage: run_fluid.sh [timeout-seconds]  -- runs scenario fluid-test headless, writes data/script-output/fluid_results.json
HERE=${0:A:h}
source "$HERE/factorio_env.sh"
rm -f data/script-output/fluid_results.json data/script-output/fluid_done.txt
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --start-server-load-scenario fluid-test --server-settings "$PWD/server-settings.json" --bind 127.0.0.1 --port 34988 > fluid_run.log 2>&1 &)
T=${1:-600}; S=$(date +%s)
while [ ! -f data/script-output/fluid_done.txt ]; do
  sleep 2
  if ! pgrep -f "start-server-load-scenario fluid-test" > /dev/null; then echo "factorio exited early"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
pkill -f "start-server-load-scenario fluid-test"; sleep 1
echo "elapsed $(( $(date +%s) - S ))s"
grep -iE "error|exception" fluid_run.log | head -10
