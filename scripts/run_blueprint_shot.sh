#!/bin/zsh
# usage: run_blueprint_shot.sh <blueprint.txt> <out-dir> [timeout-seconds]  -- photographs a blueprint or a blueprint book with
# scenario blueprint-shot in the GUI game (screenshots need the renderer, so not headless) and writes <out-dir>/shot-<n>.webp:
# one photo of the whole build per blueprint, the first 4 of a book. Only a successful run touches <out-dir>: it moves the new
# photos in, replacing the files of the same number, and removes the higher-numbered shot-<n>.webp that an older run left; a
# failed run leaves the files there as they were (it may have created the folder, and a run killed with SIGKILL leaves its
# hidden .stage.* folder behind). The exit status is 0 only when every photo that the game's report announces
# (`shots=<n>`) was converted and the report has no line that starts with `FAIL`. The timeout (default 240 seconds) is how long
# the game gets to write its report. The game window opens for about half a minute and closes by itself. The game runs without
# Steam (SteamAppId=427520), which would otherwise restart it and lose the arguments when Steam is open but not logged in. Only
# the process started here is stopped. Two runs cannot share a checkout (they share ingame/data): the second exits 2.
HERE=${0:A:h}
[[ $# -ge 2 ]] || { echo "usage: run_blueprint_shot.sh <blueprint.txt> <out-dir> [timeout-seconds]" >&2; exit 2; }
[[ -f $1 ]] || { echo "no such file: $1" >&2; exit 2; }
T=${3:-240}
[[ $T == <-> ]] || { echo "the timeout is a whole number of seconds, not '$T'" >&2; exit 2; }
BP=${1:A}; OUT=${2:A}
STR=$(<"$BP")
# The string goes into a Lua source file between quotes: only the characters of a blueprint string may reach it. A glob compares
# every byte, where a regular expression would stop at a NUL byte and let the rest through.
setopt extendedglob
[[ $STR == 0[A-Za-z0-9+/]##=# ]] || { echo "$BP is not a bare blueprint string (only its characters, no spaces or line breaks inside)" >&2; exit 2; }
command -v cwebp > /dev/null || { echo "cwebp not found (brew install webp)" >&2; exit 1; }
source "$HERE/factorio_env.sh"
mkdir -p "$OUT" || exit 1
# The lock keeps two runs from sharing ingame/data. With the module loaded and the file created, a refusal can only mean that
# another run holds it.
zmodload zsh/system || exit 1
: >> data/.blueprint_shot.lock || exit 1
zsystem flock -t 0 -f lockfd data/.blueprint_shot.lock 2> /dev/null || { echo "another run of this script is using $PWD; wait for it" >&2; exit 2; }
export SteamAppId=${SteamAppId:-427520}
printf 'return "%s"\n' "$STR" > data/scenarios/blueprint-shot/bp.lua || exit 1
rm -f data/script-output/blueprint_shot_done.txt data/script-output/blueprint_*.png(N)
"$F" --config "$PWD/config.ini" --mod-directory "$PWD/mods" --load-scenario blueprint-shot > blueprint_shot.log 2>&1 &
PID=$!
STAGE=
# Stops the game (SIGTERM, then SIGKILL after 5 s) and forgets its PID, so that a later call never signals a reused number.
stop_game() {
  [[ -n $PID ]] || return 0
  kill -0 $PID 2> /dev/null || { PID=; return 0; }
  kill $PID 2> /dev/null
  for (( k = 0; k < 5; k++ )); do kill -0 $PID 2> /dev/null || break; sleep 1; done
  kill -0 $PID 2> /dev/null && kill -9 $PID 2> /dev/null
  wait $PID 2> /dev/null
  PID=
}
cleanup() {
  stop_game
  if [[ -n $STAGE ]]; then rm -f "$STAGE"/shot-<->.webp(N); rmdir "$STAGE" 2> /dev/null; fi
  return 0
}
trap cleanup EXIT
trap 'exit 1' INT TERM HUP
S=$(date +%s)
while [ ! -f data/script-output/blueprint_shot_done.txt ]; do
  sleep 2
  if ! kill -0 $PID 2> /dev/null; then echo "factorio exited early (see ingame/blueprint_shot.log)"; PID=; break; fi
  if [ $(( $(date +%s) - S )) -gt $T ]; then echo "timeout"; break; fi
done
echo "elapsed $(( $(date +%s) - S ))s"
cat data/script-output/blueprint_shot_done.txt 2> /dev/null
grep -iE "error|exception|traceback" blueprint_shot.log | LC_ALL=C cut -c1-200 | head -10
want=$(sed -n 's/^shots=\([0-9][0-9]*\) total=.*/\1/p' data/script-output/blueprint_shot_done.txt 2> /dev/null)
# The game writes the photos after the report: wait until they all exist and stop growing, then stop the game.
for (( k = 0; k < 30; k++ )); do
  photos=(data/script-output/blueprint_<->.png(N))
  (( ${#photos} >= ${want:-0} )) && break
  sleep 1
done
for f in $photos; do
  size=-1
  for (( k = 0; k < 30; k++ )); do
    now=$(stat -f %z "$f" 2> /dev/null || echo 0)
    [[ $now -gt 0 && $now == $size ]] && break
    size=$now; sleep 1
  done
done
stop_game
# The photos are converted into a staging folder inside <out-dir> first, so that a run that fails leaves the files there as they were.
STAGE=$(mktemp -d "$OUT/.stage.XXXXXX") || exit 1
n=0
for f in $photos; do
  name=shot-${${f:t:r}#blueprint_}
  if cwebp -quiet -q ${WEBP_Q:-82} "$f" -o "$STAGE/$name.webp"; then echo "converted $name.webp"; n=$(( n + 1 )); else echo "could not convert $f" >&2; fi
done
failures=$(grep -c '^FAIL' data/script-output/blueprint_shot_done.txt 2> /dev/null)
[[ -n $want && $want -gt 0 && $n -eq $want && ${failures:-0} -eq 0 ]] || {
  echo "expected ${want:-no} photos, converted $n, ${failures:-0} FAIL lines in the report (see ingame/blueprint_shot.log)" >&2; exit 1; }
mv -f "$STAGE"/shot-<->.webp "$OUT"/ || exit 1
for f in $photos; do echo "wrote $OUT/shot-${${f:t:r}#blueprint_}.webp"; done
# Only a successful run removes the higher-numbered photos that an older run left in <out-dir>.
for old in "$OUT"/shot-<->.webp(N); do
  if (( ${${old:t:r}#shot-} > want )); then rm -f "$old"; fi
done
exit 0
