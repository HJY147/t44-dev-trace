#!/bin/sh
# Public transport only. Invoke only after the authorized cloud window opens.
set -eu
if [ "$#" -ne 2 ]; then
  printf '%s\n' 'usage: stage_opaque.sh USER@ORIGINAL_LOAD /absolute/staging/path' >&2
  exit 2
fi
remote=$1
destination=$2
case "$remote" in
  ''|-*|*[!A-Za-z0-9_.@:-]*) printf '%s\n' 'invalid SSH destination' >&2; exit 2 ;;
esac
case "$destination" in
  /*) ;;
  *) printf '%s\n' 'absolute staging path required' >&2; exit 2 ;;
esac
case "$destination" in
  *[!A-Za-z0-9_./-]*|*/../*|*/..|*/./*|*/.) printf '%s\n' 'invalid staging path' >&2; exit 2 ;;
esac
case "$destination" in
  */independent772) ;;
  *) printf '%s\n' 'staging directory basename must be independent772' >&2; exit 2 ;;
esac
script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for filename in runtime.772seal bootstrap.py launch.py manifest.json; do
  if [ ! -f "$script_directory/$filename" ]; then
    printf '%s\n' "missing public artifact: $filename" >&2
    exit 2
  fi
done
ssh -o BatchMode=yes "$remote" sh -s -- "$destination" <<'REMOTE'
umask 077
for directory in "$1" "$1/public" "$1/results"; do
  if [ -L "$directory" ]; then
    printf '%s\n' 'staging directory must not be a symlink' >&2
    exit 2
  fi
done
mkdir -p "$1/public" "$1/results"
chmod 700 "$1" "$1/public" "$1/results"
REMOTE
scp -o BatchMode=yes -- \
  "$script_directory/runtime.772seal" \
  "$script_directory/bootstrap.py" \
  "$script_directory/launch.py" \
  "$script_directory/manifest.json" \
  "$remote:$destination/public/"
printf '%s\n' 'Staged opaque runtime and public bootstrap/launcher/manifest.'
