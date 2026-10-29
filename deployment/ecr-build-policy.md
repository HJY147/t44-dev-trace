> 历史v1：2026-10-24北京14:52:56实际build已因EXACT formatter无转换而失败。请勿重新使用本页v1命令；执行改见ecr-build-policy-v2.md。下文原说明保留追溯。

# 准确C经官方ECR取相同摘要：待审查构建步骤

产品仍为`0dfb55c2191200d947c5423fd9ee74bb0812cc5a`，原Dockerfiles/compose/.env/daemon/DNS不改。helper只读源HEAD/tracked和两份Dockerfile，生成3条EXACT CONVERT＋末条DENY docker.io/*；仅改变获取位置，所有tag和sha256保持。`match_type`为snake_case。输出必须指定绝对路径、已存在且本人持有的0700父目录；0600/O_EXCL拒绝覆盖。helper不执行Docker或网络、不启动服务、不读取.env或打印凭据。

root已核官方ECR五个精确摘要metadata（14:45:29，13秒exit0）；此为root转述，本岗未云验证。原本地云构建14:38:26/61秒/exit1，DockerHub三个base metadata超时，历史不改。ECR metadata可达不证明layers下载、pip/pnpm依赖或构建完成。

官方变量是`EXPERIMENTAL_BUILDKIT_SOURCE_POLICY`，不是BUILDX_SOURCE_POLICY。已核Docker Compose v2.40.3默认Bake，并保留进程环境；Buildx v0.30.1 Bake在bake.go:1486调用ReadSourcePolicy读取该变量。ops.py也保留这两个外部工具变量。CONVERT成功立即重新匹配ECR新identifier，尾部DockerHub DENY不误伤已转换项；未知Hub来源则失败，不回退。

root审查/全文比对helper后，经已授权云助手root依次执行（本岗没有执行权限）：

```sh
install -d -m 0700 /run/t44-delivery
python3.12 /run/t44-delivery/ecr-build-policy.py \
  --source-root /opt/t44-c-0dfb55c \
  --output /run/t44-delivery/source-policy-C.json
```

helper文件由root在上述目录保存并全文核对；它来自本次工具提交，产品目录仍保持C，不能把工具提交当SUT。核policy输出hash、JSON四条规则后再单独构建：

```sh
set -eu
cd /opt/t44-c-0dfb55c
[ "$(git rev-parse HEAD)" = 0dfb55c2191200d947c5423fd9ee74bb0812cc5a ]
git diff --quiet HEAD --
[ $(( $(date -u -d '2026-10-24T09:00:00Z' +%s) - $(date -u +%s) )) -ge 840 ]
python3.12 deployment/ops.py config-check
timeout --foreground --kill-after=10s 600s env \
  COMPOSE_BAKE=true \
  EXPERIMENTAL_BUILDKIT_SOURCE_POLICY=/run/t44-delivery/source-policy-C.json \
  BUILDKIT_PROGRESS=plain \
  python3.12 deployment/ops.py build
```

云助手外层720秒/进程树，保留17:00前120秒；20元预算不变。失败/timeout立即停、不去掉DENY或换摘要重试；client退出不能推定daemon后台已清理。成功也仅为build，不启动infra、迁移、seed、账号或正式压力。下一阶段MySQL/RabbitMQ须另行审查官方ECR相同digest显式pull及独立delivery overlay，当前不改原compose或启动。

官方主源：[变量与CONVERT JSON](https://docs.docker.com/build/building/variables/#experimental_buildkit_source_policy)、[Compose2.40.3默认Bake/环境传递](https://raw.githubusercontent.com/docker/compose/v2.40.3/pkg/compose/build_bake.go)、[Buildx0.30.1 Bake读取policy](https://raw.githubusercontent.com/docker/buildx/v0.30.1/bake/bake.go)、[ReadSourcePolicy实际变量](https://raw.githubusercontent.com/docker/buildx/v0.30.1/build/build.go)、[BuildKit匹配schema](https://raw.githubusercontent.com/moby/buildkit/v0.25.1/sourcepolicy/pb/policy.proto)、[CONVERT重评估/短路](https://raw.githubusercontent.com/moby/buildkit/v0.25.1/sourcepolicy/engine.go)。此处为官方源静态兼容性判断，实际构建待root回执。
