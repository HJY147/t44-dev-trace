#!/usr/bin/env bash
# One explicit package preparation stage; no product, credentials, firewall or ECS lifecycle actions.
set -euo pipefail
umask 077
fail() { printf '%s\n' "$1" >&2; exit 1; }
readonly NODE_ROLE="${1:-${T44_NODE_ROLE:-}}"
readonly DEADLINE="${2:-${T44_OPERATION_DEADLINE_UTC:-}}"
case "$NODE_ROLE" in app|load) ;; *) fail 'Explicit app or load role required.' ;; esac
[[ $(id -u) == 0 ]] || fail 'Root Cloud Assistant execution required.'
[[ $DEADLINE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] || fail 'Explicit UTC operation deadline required.'
. /etc/os-release
[[ $ID == ubuntu && $VERSION_ID == 22.04 && $(dpkg --print-architecture) == amd64 ]] || fail 'Only Ubuntu22.04 amd64 is approved.'
readonly END=$(date -u -d "$DEADLINE" +%s)
[[ $((END - $(date -u +%s))) -gt 900 && $((END - $(date -u +%s))) -le 43200 ]] || fail 'Deadline must be 15minutes..12hours in the future.'
remaining() { echo $((END - $(date -u +%s) - 120)); }
bounded() {
  local seconds=$1 left
  shift
  left=$(remaining)
  ((left > 0)) || fail 'Operation deadline reserve reached.'
  ((seconds <= left)) || seconds=$left
  timeout --foreground --signal=TERM --kill-after=10s "${seconds}s" "$@"
}
[[ -z $(dpkg --audit) ]] || fail 'Preexisting dpkg incomplete state; inspect instead of automatic repair.'
[[ -f /usr/share/keyrings/ubuntu-archive-keyring.gpg ]] || fail 'Existing Ubuntu archive keyring required; no key imports.'
if command -v docker >/dev/null; then
  dpkg-query -W -f='${db:Status-Status}' docker.io 2>/dev/null | grep -qx installed || fail 'Existing non-Ubuntu Docker stack; do not mix or replace.'
fi
readonly WORK=$(mktemp -d /run/t44-ubuntu22-packages.XXXXXXXX)
readonly SOURCES="$WORK/ubuntu-jammy.list"
cat > "$SOURCES" <<'UBUNTU_SIGNED_SOURCES'
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu jammy main universe restricted multiverse
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://archive.ubuntu.com/ubuntu jammy-updates main universe restricted multiverse
deb [signed-by=/usr/share/keyrings/ubuntu-archive-keyring.gpg] https://security.ubuntu.com/ubuntu jammy-security main universe restricted multiverse
UBUNTU_SIGNED_SOURCES
# This list applies only to these apt commands; no global source, mirror or trust configuration is replaced.
apt_options=(-o "Dir::Etc::sourcelist=$SOURCES" -o 'Dir::Etc::sourceparts=-'
  -o APT::Get::List-Cleanup=0 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30
  -o Acquire::Retries=1 -o DPkg::Lock::Timeout=60 -o APT::Get::AllowUnauthenticated=false
  -o Acquire::AllowInsecureRepositories=false -o Acquire::AllowDowngradeToInsecureRepositories=false)
packages=(ca-certificates curl openssl python3 git gzip tar docker.io docker-compose-v2 docker-buildx)
bounded 240 apt-get "${apt_options[@]}" -o APT::Update::Error-Mode=any update
for package in "${packages[@]}"; do
  candidate=$(apt-cache "${apt_options[@]}" policy "$package" | awk '/Candidate:/ {print $2;exit}')
  [[ -n $candidate && $candidate != '(none)' ]] || fail "No Ubuntu candidate:$package"
  printf 'T44_PACKAGE_CANDIDATE %s %s\n' "$package" "$candidate"
done
bounded 600 env DEBIAN_FRONTEND=noninteractive apt-get "${apt_options[@]}" --download-only --no-install-recommends --no-upgrade --no-remove -y install "${packages[@]}"
bounded 480 env DEBIAN_FRONTEND=noninteractive apt-get "${apt_options[@]}" --no-download --no-install-recommends --no-upgrade --no-remove -y install "${packages[@]}"
bounded 30 systemctl start docker.service
[[ $(docker context inspect default --format '{{(index .Endpoints "docker").Host}}') == unix:///var/run/docker.sock ]] || fail 'Unexpected Docker context endpoint.'
unset DOCKER_HOST DOCKER_CONTEXT
bounded 15 docker --context default info --format 'T44_DOCKER_SERVER {{.ServerVersion}} {{.OSType}} {{.Architecture}}'
v=$(docker --context default compose version --short); v=${v#v}
[[ $v == 2.* ]] && dpkg --compare-versions "$v" ge 2.24 || fail 'Compose v2>=2.24 is required; do not silently use v1.'
docker --context default --version
docker --context default compose version --short
docker --context default buildx version
dpkg-query -W -f='T44_INSTALLED ${Package} ${Version} ${db:Status-Status}\n' "${packages[@]}"
printf 'T44_PACKAGES_COMPLETE role=%s utc=%s deadline=%s source_list=%s app_started=false images_pulled=false\n' "$NODE_ROLE" "$(date -u +%FT%TZ)" "$DEADLINE" "$SOURCES"
