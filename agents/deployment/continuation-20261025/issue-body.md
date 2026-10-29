部署岗新轮次准备（2026-10-25，未执行云操作）

基线 ade5e4c1998b4c2f014afde8c011645c6c5a7412；设计17c1f8e先于实现；最新工具源 a4055d1f01883c6e969f746ebe6b432f248c9942，阶段证据6e05d7a04ba56729baf1ea7a232c2f1c90ecc5e7。分支 codex/deployment-continuation-20261025 已推送。

新增 deployment/round-prepare.py / .md：从固定7个公开模板blob仅物化新副本，原10月24日期限和失败均保留。新source、唯一project/DB/私有目录、UTC操作/采样/回收/释放、worker/maxconn/预算显式写入差量和SHA清单。新源engine/settings/compose须与ade5逐字相同，否则拒绝旧15连接假设；严格CA+私网IP、镜像摘要、require-hashes及原安全约束保留。生产默认未改。

W32最低540、可选640；W64最低1020、可选1280（15*(W+2)+30）。仅预算，实际进程/pool/连接峰值/内存/镜像身份需root观察；硬件扩容不是软件收益，也不推断旧502原因。UTC/perf/monotonic anchor非原子，跨机时钟和请求对齐仍待验证；资源显式路径+完成SHA单文件官方回收，释放与账单另核。

本源22个唯一合成guard通过0.16s、Ruff/format/diff-check通过；本地CLI另成功物化7件，私有0700/0600，未执行任何生成main。初版B023及工具环境缺模块的失败/修正如实保留。证据、提示词和报告见 agents/deployment/continuation-20261025 与 ROLE-deployment-CONTINUATION-20261025-v1；操作者为部署AI，未冒充学生本人。

对接需要：旧fixture绑定旧receiver/worker/source/expiry，本包不生成它们。请root从fresh独立实例仅取公开recipient材料，再由后端岗绑定准确源worker/admin并审核；开发岗不接触独立私有用例。本岗未访问云/账号/SUT或tmp829/839/841/852独立私有材料，未启动hostedCI。正式400客户端/600秒/P95≤270ms/≥1000每分钟、代码规模、实际部署与费用均未由本阶段判通过。
