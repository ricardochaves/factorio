#!/bin/zsh
# usage: catalog/dump_prototypes.sh [timeout-seconds]
# Runs scenario dump-prototypes headless with the base game only and refreshes catalog/vanilla-prototypes.json,
# the list of prototype names validate.py accepts. Re-run it after a Factorio update.
CAT=${0:A:h}
HERE=${CAT:h}
source "$HERE/factorio_env.sh"
rm -f data/script-output/vanilla-prototypes.json data/script-output/dump_done.txt
("$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --start-server-load-scenario dump-prototypes --server-settings "$PWD/server-settings.json" --port 34989 > dump.log 2>&1 &)
T=${1:-120}; S=$(date +%s)
while [ ! -f data/script-output/dump_done.txt ]; do
  sleep 1
  if ! pgrep -f "start-server-load-scenario dump-prototypes" > /dev/null; then echo "factorio exited early (see ingame/dump.log)"; exit 1; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; pkill -f "start-server-load-scenario dump-prototypes"; exit 1; fi
done
pkill -f "start-server-load-scenario dump-prototypes"; sleep 1
python3 - data/script-output/vanilla-prototypes.json "$CAT/vanilla-prototypes.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
mods = d.get('active_mods', {})
if set(mods) != {'base'}:
    sys.exit(f'refusing to save: active mods are {sorted(mods)}, expected only base')
d['factorio_version'] = mods['base']
for k, v in d.items():
    if isinstance(v, list):
        d[k] = sorted(v)
    elif v == []:           # Lua empty tables serialize as []
        d[k] = {}
json.dump(d, open(sys.argv[2], 'w'), indent=1, sort_keys=True, ensure_ascii=False)
open(sys.argv[2], 'a').write('\n')
counts = {k: len(v) for k, v in d.items() if isinstance(v, (list, dict)) and k != 'active_mods'}
print('active mods:', mods)
print('saved', sys.argv[2], counts)
PY
