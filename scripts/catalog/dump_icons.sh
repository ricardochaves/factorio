#!/bin/zsh
# usage: catalog/dump_icons.sh
# Runs the game headless with the base mod only and --dump-icon-sprites, then packs the icons of items, fluids and
# recipes into catalog/vanilla-icons/ and catalog/vanilla-icons.json (see dump_icons.py). Needs Pillow: it uses the
# .venv at the repository root when there is one. Re-run after a Factorio update.
CAT=${0:A:h}
HERE=${CAT:h}
source "$HERE/factorio_env.sh"
# An open Steam client that is not logged in restarts the game and drops its arguments; SteamAppId avoids that.
export SteamAppId=427520
rm -rf data/script-output/item data/script-output/fluid data/script-output/recipe
"$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --dump-icon-sprites > icons-dump.log 2>&1 \
  || { echo "factorio failed (see ingame/icons-dump.log)"; exit 1; }
mods=$(grep -o 'Loading mod [A-Za-z0-9_-]*' icons-dump.log | awk '{print $3}' | sort -u | tr '\n' ' ')
if [ "$mods" != "base core " ]; then
  echo "refusing to save: mods loaded are $mods, expected only base"
  exit 1
fi
PY=${HERE:h}/.venv/bin/python
[ -x "$PY" ] || PY=python3
"$PY" "$CAT/dump_icons.py" "$PWD/data/script-output" "$CAT"
