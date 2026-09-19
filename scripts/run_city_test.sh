#!/bin/zsh
# usage: run_city_test.sh [timeout-seconds]  -- runs scenario city-test headless (see export_city.py): imports both city
# block blueprints, builds one block and a 2 x 2 city of each, and checks entities, tiles, wires, power and logistic
# networks. Exit status is 0 only when every check passed and at least one check ran.
HERE=${0:A:h}
python3 "$HERE/export_city.py" > /dev/null || exit 1
source "$HERE/factorio_env.sh"
rm -f data/script-output/city_test.txt data/script-output/city_done.txt
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --start-server-load-scenario city-test --server-settings "$PWD/server-settings.json" --bind 127.0.0.1 --port 34992 > city_test.log 2>&1 &)
T=${1:-300}; S=$(date +%s)
while [ ! -f data/script-output/city_done.txt ]; do
  sleep 2
  if ! pgrep -f "start-server-load-scenario city-test" > /dev/null; then echo "factorio exited early (see ingame/city_test.log)"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
pkill -f "start-server-load-scenario city-test"; sleep 1
echo "elapsed $(( $(date +%s) - S ))s"
cat data/script-output/city_test.txt 2>/dev/null
grep -iE "error|exception|traceback" city_test.log | head -10
grep -q '^checked failed=0 ran=[1-9][0-9]*$' data/script-output/city_test.txt
