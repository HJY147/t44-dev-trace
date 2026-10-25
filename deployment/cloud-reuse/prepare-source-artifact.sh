#!/usr/bin/env bash
# Fixed public Git objects only; no Docker, SUT execution, private inputs or credentials.
set -euo pipefail
umask 077
: "${GITHUB_REPOSITORY:?GitHub Actions repository required}"
: "${GITHUB_WORKSPACE:?GitHub Actions workspace required}"
: "${RUNNER_TEMP:?GitHub Actions temp required}"
test "$GITHUB_REPOSITORY" = HJY147/t44-dev-trace
test "${T44_BUNDLE_SOURCE_INPUT:-}" = ""
task_root="$RUNNER_TEMP/t44-f4-source-context"
task_artifact="$RUNNER_TEMP/t44-f4-source-artifact"
mkdir -m 0700 "$task_root" "$task_artifact"
task_helper="$GITHUB_WORKSPACE/deployment/cloud-reuse/backend-upgrade.py"
test "$(sha256sum "$task_helper" | cut -d ' ' -f 1)" = 6609f859c0ff02249455b67684eff49c7d77996a0cc7937b394319acdc6570c8
git init --quiet "$task_root/product"
timeout --signal=TERM --kill-after=10s 120s git -C "$task_root/product" fetch \
  --quiet --no-tags --depth=1 https://github.com/HJY147/t44-dev-trace.git \
  935ab5b93bea788672c2b4a088c79cfeed848954 \
  f4bd382d4668130793fc553df9ce6363c4656ea6
python3 "$task_helper" prepare --repository "$task_root/product" --output "$task_root/source"
for task_name in source-backend.tar.gz source-manifest.json frozen-equality.json Dockerfile; do
  install -m 0600 "$task_root/source/$task_name" "$task_artifact/$task_name"
done
install -m 0600 "$task_helper" "$task_artifact/backend-upgrade.py"
python3 - "$task_artifact" <<'PY'
import importlib.util, json, pathlib, sys
sys.dont_write_bytecode = True
p = pathlib.Path(sys.argv[1])
expected = {'source-backend.tar.gz', 'source-manifest.json', 'frozen-equality.json', 'Dockerfile', 'backend-upgrade.py'}
assert {f.name for f in p.iterdir()} == expected
assert all(f.is_file() and not f.is_symlink() and f.stat().st_mode & 0o777 == 0o600 for f in p.iterdir())
assert sum(f.stat().st_size for f in p.iterdir()) < 1024 * 1024
spec = importlib.util.spec_from_file_location('approved_upgrade', p/'backend-upgrade.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
h = m.sha(p/'source-manifest.json')
m.source_package(p, h)
assert {f.name for f in p.iterdir()} == expected
print(json.dumps({'kind':'public-source-artifact-only','source_sha':m.TARGET,'base_sha':m.BASE,'manifest_sha256':h,'actual_files':[{'path':f.name,'bytes':f.stat().st_size,'sha256':m.sha(f)} for f in sorted(p.iterdir()) if f.name in expected], 'docker_or_SUT_executed':False}))
PY
