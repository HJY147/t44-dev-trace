# 同批实例离线增量镜像：935 → f4（build-only）

部署岗只准备本地工具，不操作云。产品目标精确 f4bd382d4668130793fc553df9ce6363c4656ea6；root 转述两个官方 CI success，不以此冒充本工具云构建、400/600 或最终验收。

## 已实际完成的本地准备

helper `backend-upgrade.py` 23175 bytes / SHA256 `6609f859c0ff02249455b67684eff49c7d77996a0cc7937b394319acdc6570c8`。固定目标，不接受任意 source/image/base；21 项离线负例/边界检查和 Ruff 通过。

同一源码仓库的 git cat-file bytes＋mode 逐项比对：依赖 lock/pyproject、两份 REST、schema.py/schema_v1.sql、specs/database 与 contracts、完整 frontend、原 runtime_probe/credential_admin/API 与 web Dockerfile/dockerignore/nginx，47 文件全部同字节/同模式。原 web935 仅以原标签复用，记录其同字节前端来源；不重贴 f4 标签，不下载旧537MB包。迁移 Python 实现可能变化，DDL 文件同字节不代表迁移运行已验证。

新 git archive 真正打包 backend/t44 全集＋requirements.lock/pyproject（53 文件），对照同 commit 的 ls-tree/cat-file 清单校全，不靠 treeOID 冒充归档 hash。实际 tar1259520 bytes / SHA `c74c25b719f4e05e5d2f6b3295f388819c01a2e5de9d2f6261ba4d9d3ab92861`，gzip152941 bytes / SHA `6fda49743a285aecde4f6250844d13cf1ac452e7577df519db432864de6b6a06`。source-v2 的 manifest SHA `6c211bc572c731ef9eae9d91161e411e412471900e7e4c33ae390ab095a63337`；早期 source 目录75fc...保留为初步47项范围扩充前记录，不用于本次 build。

本机可传原件位于忽略目录：`.agent-worktrees/.runtime/continuation-20261025/backend-upgrade-f4/source-v2/`。PUBLIC 审核副本的完整清单在 `agents/deployment/cloud-reuse-20261025/upgrade-source-manifest.json` 和 `upgrade-frozen-equality.json`。私有源码目录不含数据库环境、账号或测试材料。

## 官方 CI 小工件（已准备，等待 root dispatch）

`.github/workflows/offline-backend-source.yml` 仅有 workflow_dispatch，无自动 push/PR、无输入；明确公开 fetch 固定935/f4 Git objects，checkout工具分支且 persist-credentials=false。共享的 prepare-source-artifact.sh 只跑 stdlib prepare 和等字节核，不Docker/不导入SUT/不读private；artifact显式只有四原件＋helper共五文件，单个工件小于1MiB，禁止额外文件/符号链接，不上传课堂文档、runtime或日志。Linux实际生成的archive/manifest/gzip/ZIP摘要在正式工件下载后核，以该真实摘要为准，Mac source-v2不改标签。

GitHub说明新 workflow 需默认分支注册才可手动触发，见[官方事件说明](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch)。实际API列表已查 main默认分支，尚无此新file，故同时在原已注册 docker-integration.yml 添加**仅手动分支** source_upgrade_only 输入桥接；true时原Docker联调/大镜像bundle都跳过，只跑同一固定源脚本。原push/PR路径保持原job条件。root可立即运行：

```sh
gh workflow run docker-integration.yml --repo HJY147/t44-dev-trace \
  --ref codex/deployment-continuation-20261025 -f source_upgrade_only=true
```

新file默认分支注册后可以直接 `gh workflow run offline-backend-source.yml --repo HJY147/t44-dev-trace --ref codex/deployment-continuation-20261025`，无source输入可漂移。不创建Release/Tag/合格声明，本岗不自行dispatch。

## root 官方云助手分段传输后执行

仅向 app 角色节点传四件原文件及 helper：`source-backend.tar.gz`、`source-manifest.json`、`frozen-equality.json`、`Dockerfile`；原 tar 可留本机，服务器由 gzip 校实际解压 hash。文件0600/新父目录0700，O_EXCL 写入并按上述 hash 核验，不覆盖已有轮次。helper23KB小于单命令32KiB，但 base64 会放大；root 若打包命令，请压缩 helper 或分段，不把大包误传一次 SendFile。

服务器原 proof 文件保持 `/root/t44-r9/image-proof.py`（47b50...）、`/root/t44-r9/proof-v2-01/proof.jsonl`（30b1...）；不改 daemon、不重新 docker load、不 retag 原935。

```sh
python3 /root/t44-r9/backend-upgrade.py build \
  --package /root/t44-r9/upgrade-f4-source-01 \
  --manifest-sha256 6c211bc572c731ef9eae9d91161e411e412471900e7e4c33ae390ab095a63337 \
  --image-proof /root/t44-r9/image-proof.py \
  --proof-raw /root/t44-r9/proof-v2-01/proof.jsonl \
  --output /root/t44-r9/upgrade-f4-build-01 --run-id r10f4build01
```

预检 source/frozen/requirements/工具身份，重新核原 backend 与 web 的实际 Id/Descriptor/RootFS/Labels，要求新 alias 未存在且 Docker 明确返回 No such image，否则拒绝。FROM 固定已证明935，`USER 0:0` 后真正 `RUN rm -rf /app/backend/t44`，完整 COPY 新目录和同字节依赖描述，恢复10001；无 pip/apt/外部下载，pull=false/network=none。原 entry、Env、User、工作目录、ports 等配置不变。新标签为 `t44-backend-upgrade:src-f4bd382d4668130793fc553df9ce6363c4656ea6-r10f4build01`；revision/archive/baseconfig/actualdescriptor/source-manifest/Dockerfile/run 各身份明确，旧935别名不变。

构建后保留新 buildmetadata、完整本地 derived-backend.tar，重算 config 与所有 layer/OCI descriptor SHA/size/DiffID。临时一次 `--rm --network none --read-only --user10001 --cap-drop ALL` 容器只执行文件 hash 检查、不导入业务模块、不挂任何目录或环境；实际全部 t44 文件名/bytes/hash/mode 必须等于 manifest，额外旧 commands.py、缺文件、内容/模式不同均拒绝。最后再次核原 backend/web 身份，写独立 upgrade-binding.json，stdout 只摘要。

成功回执必须包含真实新 Id/configId、binding SHA、53项源集中的实际 t44 文件检查数量；当前这些字段尚未由云实际生成，不预填。失败原件独占新文件保留，不能用旧成功覆盖。此命令不启动业务服务、不建 schema、不改 DB/MQ/卷、不给新镜像套旧935成绩。

## 后续新应用控制器设计（尚未实现/启动）

原 app-campaign.py 固定935，不能把 f4 塞入旧770d binding；须独立新版本读取 root 明确 pin 的 upgrade-binding，重新核新 image/归档/完整文件集，并将新 source/archive/actualId 和同字节旧 web935 来源写进新 generation。F/P 各新 schema、账号、vhost、volume、CA、端口、项目名、controller 与持久 stop timer，原 production entry 和实际 workers 明写。原诊断935 profile、DB、env、CA及停止锚不改，也不删除。

此设计有明确源/依赖/镜像边界，尚无新 F/P prepare/start/seed/性能许可。root 先结束935诊断并决定新 generation 和时限，再为新控制器安排独立实现与准入；不为迁移争取时间而延长旧 timer/grant，不新开或重买 VM。

新增真实教训（root回执，非本岗云探测）：935工厂API running身份核验成功之后，后续host严格CA+IP的HTTPS仍ConnectionRefusedError，data-only admin另有Network unreachable；两者分别保留，不能把API进程running或Compose wait当TLS可用。root正在收限定TLS/web日志，尚无根因。本岗不猜整改；下一代up必须增加host实际HTTPS CA+IP验证（无token，401预期另显式记录），失败原stdout/stderr保新私有原件，API身份/TLS门禁各记，不能关闭验证或覆盖原770d锚。
