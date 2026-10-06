#!/bin/zsh
# usage: catalog/dump_icons.sh
# Starts the game once with the base mod only and --dump-icon-sprites (it opens the game's window and exits by itself),
# then packs the icons of items, fluids and recipes into catalog/vanilla-icons/ and catalog/vanilla-icons.json (see
# dump_icons.py). Needs Pillow, so it stops before it starts the game when the repository's .venv (python3 -m venv
# .venv && .venv/bin/pip install -r site/requirements.txt) is missing or has no Pillow. Re-run after a Factorio update.
CAT=${0:A:h}
HERE=${CAT:h}
PY=${HERE:h}/.venv/bin/python
"$PY" -c 'import PIL' 2>/dev/null || {
  echo "no Pillow in ${HERE:h}/.venv: create it with python3 -m venv .venv and install site/requirements.txt"
  exit 1
}
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
"$PY" "$CAT/dump_icons.py" "$PWD/data/script-output" "$CAT"
