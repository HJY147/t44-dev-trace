# R30 部署准备审计

操作者：deployment AI；root 派工；仅本地/公开免费标准 Actions，不操作云实例或读取 `.runtime`、独立 PRIVATE/case。

- 工作树以 root `7374b3637b06465d448fc2e81952ba18fc676315` 创建，产品仅 `0bffe0c535e5897890aebf30879fdd3839dc52d6`，不会用工作树 HEAD 冒充产品源。
- `cloud-image-bundle.yml` / `image-bundle.py` 拉五官方基底并构建 backend/web，打全部七角色。现有 v2 接收器也要求全七角色，不能拿 backend-only 包传入。
- `offline-backend-source.yml` 固定 f4；`resume-source-package.yml`→旧 derive 要求 935 的 frozen 全相等。真实 0b 的 53 backend 文件中旧 frozen 的 47 个只有 schema.py 不同，46 件完整 bytes/hash/mode 相等。schema.py：4999B/cd1465fc7560c0f13bb80216507b237e297e2177eccf280d8802651f0458e4bd → 4652B/fb79576cb70c2f6296dabe46e9e9f51bb95c0f731db1f7660e0e69b28ca80393。它是已发表产品实现差异，不能记成旧47件完全相等；DDL/contracts/lock/frontend/support仍相等。
- root 提供 CI40827655008 四 job 成功、796BE/89FE，应用5880超780，以及停机/旧短测/QA772边界均作为 root 上下文，部署岗本次没有把旧CI或旧cloud NP改成新验收。
- 历史双机镜像证明公开投影在 `agents/deployment/cloud-reuse-20261025/image-proof-root-summary-projection.json`；原 raw hash `30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0`。这证明历史内容身份，不证明停机后现在的缓存与liveness。完整 raw 未在本岗读取。

## 选择与传输量依据

1. source-only 增量：本次准确0b context共62件，Git tar 2263040B、gzip235707B。它比镜像小，但旧 source-only builder/generator 因 schema.py 必须拒绝；若另造支持这项产品差异的新 builder 及 binding 接口，会同时扩张源构建和部署身份两层。
2. backend-only 官方构建（选用）：新 `r30-backend-artifact.py` 从官方 pinned Python 和准确0b的62件上下文真实build，导出一个新backend，不build web、不搬五官方独立镜像。不使用旧backend改标签。镜像运输量以新 Actions artifact 实际 bytes 后补，不估算成实测。需要APP接收新backend；LOAD只需中性材料/工具和当前官方Python复核，不接收backend镜像。

新制品将分开证明：Git→源文件清单/bytes/hash/mode；官方 Python pin/拉取 RepoDigest/有序 DiffID prefix；backend新config、保存归档各层bytes/hash/DiffID和Docker29 descriptor；隔离非root真实container文件集合（含完整53 backend件，其他运行源7件）。只运行文件探针，不运行业务或SUT。

## 首次观察及失败保留

- 最初按不存在的 `deploy/Dockerfile.backend` / `deployment/Dockerfile.backend` 查询，真实 fatal/not-found；正确已核为 `deployment/api.Dockerfile`，属于发现命令路径错误，不是镜像构建失败。
- 系统python3没有pytest，真实 `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3: No module named pytest`；改用标准库 unittest，无安装/修改项目依赖。
- 首次 `.venv*` zsh glob 查询返回 `no matches found: .venv*`，未据此声称项目没有其他venv。
- 正确新 prepare 首次成功，13项离线边界首次全绿，日志 `local-boundaries-first.log`；尚无真实镜像build/云/完整Linux工具/跨机/TTL/SUT结论。

## boot 前仍须关闭的缺口

准确新镜像 artifact 尚待免费build/完整回收验证；新的backend-only接收/loaded identity探针与新generation必须接新manifest接口，旧v4 generator要求旧upgrade binding，不能直接接本包。新run/namespace/端口/硬绝对时间尚未由root选择，因此现在不发行任何带旧日期的可执行窗口包。旧grants/session expired，不复用。完整Linux v2.4执行器和实际Python3.12.15/8CPU适配仍需QA公开准入；不能以本地模拟或generic subset代替。
