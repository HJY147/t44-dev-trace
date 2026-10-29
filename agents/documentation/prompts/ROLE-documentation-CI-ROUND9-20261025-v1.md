# ROLE-documentation-CI-ROUND9-20261025-v1

实际执行者：AI `/root/ci_evidence_round9`；授权与派工来自总协调 `/root`。Refs: #9。

本轮实际派工：从准确 integration f4bd382d4668130793fc553df9ce6363c4656ea6 收集两对官方 Actions（产品40200930857/Docker40200930957，源a16238b9eb3b47473c0332989d6b3dcc1d95d1f4；产品40201584671/Docker40201584699，源f4bd382d4668130793fc553df9ce6363c4656ea6）。先封 E731 首次失败原件，再完整结果。优先 GitHub connector；如只返回远程引用，则以 gh API 原 ZIP bytes 落盘，验证服务端 digest/大小、ZIP CRC、路径及 symlink、run/head/job 绑定。保留失败，不取消、重跑或改 workflow，不评论 GitHub。解析真实 JUnit 测试及覆盖率分子分母，区分 push 和 pull_request merge ref。

范围：仅 records/ci、本岗日志/模块报告/handoff/prompt，以及统一 Round9 CI 报告。不改应用、测试、计数口径、学生研究正文、学号/账号/财务签名，不操作云或浏览器，不读取其他岗位工作树、.runtime、任何 tmp800/805/809/814/independent 私有或冷包/用例/keys。CI 与 Docker 不代表独立验收、正式性能、规模达标、账单完成；规模事实由总协调提供为5862/5100，超762，本岗不重算。

实际更正留痕：首次将“禁止 .agent-worktrees”理解为禁止所有工作树，已在根外建立 worktree。总协调明确更正：用户要求所有工作在项目根内，允许自己的 `.agent-worktrees/ci-evidence-round9`；使用 `git worktree move` 原样搬入，未删除数据。总协调同时更正“三轮”为口误，只有上述两对，不重复下载旧40195832268。本岗曾只读旧 archive-binding 格式参考，没有沿用旧结论。

改进理由：本次 prompt 对四个 run 与两个 SHA、原 ZIP 与解包文件、首次红与修正后绿、服务端摘要与本地摘要作显式区分，防止将后续结果回填首次失败。产物：records/ci/<runid>/ 与 reports/final/round9-ci-evidence.md。
