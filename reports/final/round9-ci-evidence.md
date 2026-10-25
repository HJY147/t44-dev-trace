# Round9 官方 CI 原件证据

Agent-Role: documentation；操作者：AI `/root/ci_evidence_round9`；Prompt-Ref: ROLE-documentation-CI-ROUND9-20261025-v1；Refs: #9。

阶段1已封存首次 E731。产品 run [40200930857](https://github.com/HJY147/t44-dev-trace/actions/runs/40200930857) 绑定源 `a16238b9eb3b47473c0332989d6b3dcc1d95d1f4`、attempt1、push/codex/integration。overall CANCELLED；static job121191761720 FAILURE，coverage CANCELLED，contracts/frontend SUCCESS。`static-3.log` 与 `static-console.log` 原件记录 `tmp/backend/messaging/806_newscope.py:34` 的 E731，`static.json` 记录 Ruff exit1。

原ZIP4157bytes，sha256 `911b65a4a440754eff73ced53c727415ce203bd50c6e831b5d229c733c5f7fd6`；两者与官方artifact12601838817元数据完全一致。10成员ZIP CRC全通过、无绝对或父级路径、无symlink。证据为 [phase1 binding](../../records/ci/40200930857/archive-binding.phase1.json) 及同目录原ZIP/run/artifact/job JSON。不是由解包后文件推定原ZIP正确。

GitHub connector先用于官方元数据和下载能力检查。下载只提供远程复用文件引用、没有本地文件路径；本岗再用 `gh api repos/HJY147/t44-dev-trace/actions/artifacts/12601838817/zip` 流式保存原始 bytes，没有重打包，签名下载URL不留存。元数据为API JSON表示，不称HTTP传输原字节。

其余三run已取官方元数据，原ZIP及JUnit/覆盖率分子分母仍待后续阶段；本阶段不将后续结果回填首次失败。两对run是总协调更正后的范围，“三轮”为派工口误，旧40195832268未重复下载。worktree误建根外后已遵照更正原样搬至项目内专属目录。

本岗只收集/分析CI证据，没有取消/重跑或修改workflow，没有改应用、测试或计数口径、没有发GitHub评论。CI/Docker不代表独立验收、正式性能、规模达标或账单完成。总协调提供的当前应用物理5862行，上限5100，超762，规模门禁仍FAIL；本岗未重算。
