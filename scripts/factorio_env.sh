# Sourced by the run_*.sh scripts (after they set HERE to the scripts dir).
# Locates the Factorio binary and prepares the isolated write-data dir under ingame/.
FACTORIO_BIN=${FACTORIO_BIN:-"$HOME/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/MacOS/factorio"}
if [ ! -x "$FACTORIO_BIN" ]; then echo "Factorio binary not found: $FACTORIO_BIN (set FACTORIO_BIN)" >&2; exit 1; fi
cd "$HERE/ingame" || exit 1
mkdir -p data/script-output mods
# config.ini holds an absolute path, so it is generated on every run and never committed.
printf '[path]\nread-data=__PATH__system-read-data__\nwrite-data=%s\n[other]\ncheck-updates=false\n' "$PWD/data" > config.ini
F="$FACTORIO_BIN"
