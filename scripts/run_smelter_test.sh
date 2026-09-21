#!/bin/zsh
# usage: run_smelter_test.sh [timeout-seconds]  -- runs scenario smelter-test headless (see export_smelter.py):
# imports the stone brick smelter, checks its entities, modules and power, feeds it a full express belt of stone for
# 60 s after a 60 s warm-up and measures the stone consumed, the bricks made and how long each furnace works, once
# with every technology researched and once with none, both in the same run. Exit status is 0 only when every check
# passed and at least one check ran. The timeout argument is in real seconds (default 300); the run itself took about
# ten seconds on the author's machine.
HERE=${0:A:h}
python3 "$HERE/export_smelter.py" > /dev/null || exit 1
source "$HERE/factorio_env.sh"
rm -f data/script-output/smelter_test.txt data/script-output/smelter_done.txt
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --start-server-load-scenario smelter-test --server-settings "$PWD/server-settings.json" --bind 127.0.0.1 --port 34993 > smelter_test.log 2>&1 &)
T=${1:-300}; S=$(date +%s)
while [ ! -f data/script-output/smelter_done.txt ]; do
  sleep 2
  if ! pgrep -f "start-server-load-scenario smelter-test" > /dev/null; then echo "factorio exited early (see ingame/smelter_test.log)"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
pkill -f "start-server-load-scenario smelter-test"; sleep 1
echo "elapsed $(( $(date +%s) - S ))s"
cat data/script-output/smelter_test.txt 2>/dev/null
grep -iE "error|exception|traceback" smelter_test.log | grep -v InterruptibleStdioStream | head -10   # that one is the server seeing EOF on its stdin
grep -q '^checked failed=0 ran=[1-9][0-9]*$' data/script-output/smelter_test.txt
