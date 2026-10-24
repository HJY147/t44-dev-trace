#!/usr/bin/env bash
# Review first. Run ONE stage manually; this script never starts T44 application services.
set -euo pipefail
umask 077
readonly PRODUCT_SHA=0dfb55c2191200d947c5423fd9ee74bb0812cc5a
readonly SOURCE_DIR=/opt/t44-c-0dfb55c
readonly PUBLIC_REPO=https://github.com/HJY147/t44-dev-trace.git
readonly DEADLINE_UTC=2026-10-24T09:00:00Z
fail() { printf '%s\n' "$1" >&2; exit 1; }
[[ $# == 1 ]] || fail 'Choose exactly one stage: inspect, packages, source.'
case "$1" in inspect|packages|source) ;; *) fail 'Unknown stage.' ;; esac
[[ $(id -u) == 0 ]] || fail 'Requires an administrator root shell on the designated new application host.'
. /etc/os-release
[[ $ID == ubuntu && $VERSION_ID == 24.04 && $(dpkg --print-architecture) == amd64 ]] || fail 'Requires Ubuntu24.04 amd64.'
remaining() { echo $(( $(date -u -d "$DEADLINE_UTC" +%s) - $(date -u +%s) - 120 )); }
[[ $(remaining) -gt 0 ]] || fail 'Original17:00 Beijing deadline is near/past; do not extend it.'
bounded() {
  local cap=$1 left
  shift; left=$(remaining)
  (( left > 0 )) || fail 'Deadline reserve reached.'
  (( cap <= left )) || cap=$left
  timeout --foreground --signal=TERM --kill-after=10s "${cap}s" "$@"
}
installed() { [[ $(dpkg-query -W -f='${db:Status-Status}' "$1" 2>/dev/null || true) == installed ]]; }
versions() {
  python3.12 --version
  git --version
  docker --version
  docker buildx version
  docker compose version --short
  local v
  v=$(docker compose version --short); v=${v#v}
  [[ $v == 2.* ]] && dpkg --compare-versions "$v" ge 2.24 || fail 'Compose v2>=2.24 is required.'
}
case "$1" in
  inspect)
    date -u '+%Y-%m-%dT%H:%M:%SZ'
    printf 'Ubuntu24.04 amd64;deadline=%s;source=%s\n' "$DEADLINE_UTC" "$PRODUCT_SHA"
    for p in python3.12 git ca-certificates docker.io docker-compose-v2 docker-buildx; do
      if installed "$p"; then printf '%s installed\n' "$p"; else printf '%s not installed\n' "$p"; fi
    done
    # Missing tools are reported; no installation, network, daemon or credentials are touched.
    ;;
  packages)
    # Use the new host's Ubuntu-signed archive/universe sources; never disable authentication.
    missing=()
    for p in python3.12 git ca-certificates; do installed "$p" || missing+=("$p"); done
    if ! command -v docker >/dev/null 2>&1; then
      missing+=(docker.io docker-compose-v2 docker-buildx)
    elif ! docker compose version >/dev/null 2>&1; then
      installed docker.io || fail 'Existing non-Ubuntu/partial Docker stack:review instead of replacing it.'
      missing+=(docker-compose-v2)
    fi
    if command -v docker >/dev/null 2>&1 && ! docker buildx version >/dev/null 2>&1; then
      installed docker.io || fail 'Existing Docker without buildx:review compatible vendor plugin instead of mixing packages.'
      missing+=(docker-buildx)
    fi
    if (( ${#missing[@]} )); then
      apt_options=(-o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 -o Acquire::Retries=1 -o DPkg::Lock::Timeout=60 -o APT::Get::AllowUnauthenticated=false)
      bounded 180 apt-get "${apt_options[@]}" -o APT::Update::Error-Mode=any update
      # Separate bounded download from installation; no upgrade, repository rewrite, curl|sh or key import.
      bounded 300 env DEBIAN_FRONTEND=noninteractive apt-get "${apt_options[@]}" --download-only --no-install-recommends -y install "${missing[@]}"
      bounded 240 env DEBIAN_FRONTEND=noninteractive apt-get "${apt_options[@]}" --no-download --no-install-recommends -y install "${missing[@]}"
    fi
    versions
    ;;
  source)
    versions
    if [[ -e $SOURCE_DIR ]]; then
      [[ -d $SOURCE_DIR/.git && ! -L $SOURCE_DIR ]] || fail 'Source target already exists and is not the designated checkout.'
      [[ $(git -C "$SOURCE_DIR" remote get-url origin) == "$PUBLIC_REPO" ]] || fail 'Existing source origin differs.'
    else
      mkdir -m 0750 "$SOURCE_DIR"
      git -C "$SOURCE_DIR" init --quiet
      git -C "$SOURCE_DIR" remote add origin "$PUBLIC_REPO"
      bounded 360 env GIT_TERMINAL_PROMPT=0 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null git -c credential.helper= -c core.askPass= -c http.lowSpeedLimit=1024 -c http.lowSpeedTime=30 -C "$SOURCE_DIR" fetch --no-tags --depth=1 origin "$PRODUCT_SHA"
      git -C "$SOURCE_DIR" checkout --quiet --detach "$PRODUCT_SHA"
    fi
    [[ $(git -C "$SOURCE_DIR" rev-parse HEAD) == "$PRODUCT_SHA" ]] || fail 'HEAD differs from exact approved C.'
    git -C "$SOURCE_DIR" diff --quiet HEAD -- || fail 'Tracked source differs from approved C.'
    printf 'Exact source verified:%s\nDirectory:%s\n' "$PRODUCT_SHA" "$SOURCE_DIR"
    ;;
esac
