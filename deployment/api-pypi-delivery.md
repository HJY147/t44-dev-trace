# API-only 外置 PyPI delivery（待root审核/执行）

产品仍为 C `0dfb55c2191200d947c5423fd9ee74bb0812cc5a`。工具仅在新的root-owned0700 runtime排他写0600三文件：`api-pypi-C.Dockerfile`、同名`.dockerignore`、manifest.json；不改C、不build、不network。生成前核C HEAD/tracked clean和原Dockerfile/ignore/lock固定SHA。唯一Dockerfile差量是原pip install末追加 `--index-url https://mirrors.aliyun.com/pypi/simple/`，仍HTTPS默认验证、no-cache-dir/require-hashes/完整lock/原FROM摘要不变，无HTTP/trusted-host/extra-index。

这是**下载渠道改变后的外置Dockerfile构建，不能称原Dockerfile逐字构建**。`.dockerignore`逐字复制C sidecar并紧邻外置Dockerfile，不能漏掉，也不使用仅有根context但没有sidecar的命令。helper打印old/new/ignore/lock哈希及changed_channel_only=true/not_original_Dockerfile_bytes=true。镜像内容/功能等价仍需实际构建与运行取证；镜像站可达性和实际成功尚未知。

root先核helper SHA并relay至私有目录，再单独生成（runtime必须新目录，父目录0700；不覆盖旧attempt）：

```sh
python3 /run/t44-delivery/api-pypi-delivery.py \
  --source-root /opt/t44-c-0dfb55c \
  --runtime /run/t44-delivery/api-pypi-C-v1
```

## 独立API-only构建命令（不自动跟随生成）

以下仅供root全文审核后经云助手执行。外层云任务1320秒/进程树；距北京17:00必须至少1440秒。内层1200秒，TERM后15秒KILL仅该build客户端进程树；daemon可能另有任务，超时不能称其已经退出，仍先只读观察，不盲重跑。原已成功web不重建。policyv2必须是已核f910完整hash；不删除DENY。只有本次成功回执才可称API镜像build成功，不据此宣称infra/迁移/启动/TLS/正式性能通过。

```sh
set -euo pipefail
umask 077
src=/opt/t44-c-0dfb55c
delivery=/run/t44-delivery/api-pypi-C-v1
policy=/run/t44-delivery/source-policy-C-v2.json
deadline=$(date -u -d '2026-10-24T09:00:00Z' +%s)
test "$((deadline - $(date -u +%s)))" -ge 1440
test "$(git -C "$src" rev-parse HEAD)" = 0dfb55c2191200d947c5423fd9ee74bb0812cc5a
git -C "$src" diff --quiet HEAD --
python3 -I - <<'CHECK'
import hashlib, json, os, stat
from pathlib import Path
runtime = Path('/run/t44-delivery/api-pypi-C-v1')
source = Path('/opt/t44-c-0dfb55c')
policy = Path('/run/t44-delivery/source-policy-C-v2.json')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def private(p, directory=False):
    s = p.lstat()
    assert (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))
    assert s.st_uid == os.geteuid() == 0
    assert stat.S_IMODE(s.st_mode) == (0o700 if directory else 0o600)
private(runtime, True)
for name in ['manifest.json', 'api-pypi-C.Dockerfile', 'api-pypi-C.Dockerfile.dockerignore']:
    private(runtime / name)
private(policy)
m = json.loads((runtime / 'manifest.json').read_bytes())
assert m['product_source'] == '0dfb55c2191200d947c5423fd9ee74bb0812cc5a'
assert m['changed_channel_only'] is True and m['not_original_Dockerfile_bytes'] is True
assert digest(runtime / 'api-pypi-C.Dockerfile') == m['delivery_Dockerfile_sha256']
assert digest(source / 'deployment/api.Dockerfile') == m['original_Dockerfile_sha256']
assert digest(source / 'backend/requirements.lock') == m['requirements_lock_sha256']
assert digest(runtime / 'api-pypi-C.Dockerfile.dockerignore') == digest(source / 'deployment/api.Dockerfile.dockerignore') == m['dockerignore_sha256']
assert digest(policy) == m['source_policy_v2_sha256'] == 'f9101355c4bf7b9d51e9feda2d8e48361e0d3a9ff81cb5f71ccd49bbb775e1f8'
old = (source / 'deployment/api.Dockerfile').read_bytes()
needle = b'RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock'
assert (runtime / 'api-pypi-C.Dockerfile').read_bytes() == old.replace(needle, needle + b' --index-url https://mirrors.aliyun.com/pypi/simple/', 1)
CHECK
test "$(env -u DOCKER_HOST -u DOCKER_CONTEXT docker --context default context inspect default --format '{{.Endpoints.docker.Host}}')" = unix:///var/run/docker.sock
log=$(mktemp "$delivery/build-api-XXXXXX.log")
set +e
env -u DOCKER_HOST -u DOCKER_CONTEXT \
  EXPERIMENTAL_BUILDKIT_SOURCE_POLICY="$policy" \
  timeout --signal=TERM --kill-after=15s 1200s \
  docker --context default buildx build --platform linux/amd64 \
  --load --tag t44-backend:local --progress plain \
  --file "$delivery/api-pypi-C.Dockerfile" "$src" >"$log" 2>&1
rc=$?
set -e
printf 'T44_API_DELIVERY_BUILD_EXIT=%s\n' "$rc"
# 仅root私有UI查看最多4096字节/20行；完整stdout/stderr留0600日志，不公开上传。
tail -c 4096 "$log" | tail -n 20
exit "$rc"
```

没有自动续时/增预算/服务启动/删卷/重试，17:00释放与实际20元预算不变。最新完整C build v2北京15:13:15/601秒/exit124保持失败；web成功和API未完分别记录，不覆盖旧日志。

依据：[Dockerfile专用ignore及优先级](https://docs.docker.com/build/concepts/context/#filename-and-location)、[pip index-url](https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-index-url)、[require-hashes](https://pip.pypa.io/en/stable/topics/secure-installs/#hash-checking-mode)。
