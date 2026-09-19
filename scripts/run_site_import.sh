#!/bin/zsh
# usage: run_site_import.sh [timeout-seconds]  -- runs scenario site-import headless (see site_import_test.py)
HERE=${0:A:h}
source "$HERE/factorio_env.sh"
rm -f data/script-output/site_import.txt data/script-output/site_import_done.txt
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --start-server-load-scenario site-import --server-settings "$PWD/server-settings.json" --bind 127.0.0.1 --port 34991 > site_import.log 2>&1 &)
T=${1:-600}; S=$(date +%s)
while [ ! -f data/script-output/site_import_done.txt ]; do
  sleep 2
  if ! pgrep -f "start-server-load-scenario site-import" > /dev/null; then echo "factorio exited early (see ingame/site_import.log)"; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
pkill -f "start-server-load-scenario site-import"; sleep 1
echo "elapsed $(( $(date +%s) - S ))s"
cat data/script-output/site_import.txt 2>/dev/null | tail -n 200
grep -q '^checked=.* failed=0$' data/script-output/site_import.txt
