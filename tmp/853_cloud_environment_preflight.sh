#!/usr/bin/env bash
# Host preparation probe only; not an application or independent acceptance test.
set -eu
date -Is
printf 'execution_user='
id -un
printf 'architecture='
uname -m
if [ -r /etc/os-release ]; then
    . /etc/os-release
    printf 'operating_system=%s %s\n' "$ID" "$VERSION_ID"
fi
for binary in python3 git docker curl; do
    if command -v "$binary" >/dev/null 2>&1; then
        command -v "$binary"
    else
        printf 'missing=%s\n' "$binary"
    fi
done
if command -v python3 >/dev/null 2>&1; then python3 --version; fi
if command -v docker >/dev/null 2>&1; then
    docker --version
    if docker compose version; then :; else printf 'compose_v2_unavailable\n'; fi
fi
getent passwd root ecs-user | cut -d: -f1,3,6,7
