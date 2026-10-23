# 实际派工 ROLE-backend-INTEGRATION-v1

来源：总协调 /root；实际消息原文：

继续正式后端整合阶段 ROLE-backend-INTEGRATION-v1。你上次47c21f5已整合；当前root integration完整基点 fcaf509（已含FE bd13414、MQ首b5+二阶段9481 cherry-pick、DB1602+公平claim8b60）。scheduler完整SHA稍后发，请先merge fcaf509到自己worktree，勿碰root索引。优先修真实GHA现有失败 backend/tests/contracts/test_faults.py::test_missing_notification_dependency_returns_real_503：显式注入缺组件，保留真实503断言，另测默认正常200。随后修冻结字段字典禁止用枚举位置持久化：common.py ERROR_IDS目前enumerate(ErrorCode.enum,1)，application.py codes[reason_code-1]；应显式稳定双向映射并验证枚举显示重排不改数据库码。workflow.py tuple(TaskState)及magic-state也须显式稳定API适配而非顺序。复用规范不改冻结文件。DB已撤回“仅lease过期必拒绝旧owner”的误报，无接管不能凭新口径改行为。等sched接入后跑全38 HTTP/契约/错误分支、全t44 line>=80覆盖，不得用子目录局部覆盖冒充。DB生产seed稍后给SHA。完整API启动后要给FE通知/升级真链回归；旧18080仅旧分支进程需安全更新。先修问题并做可整合checkpoint，再验证扩大；保留失败。源代码规模已超限，需要真的删无调用/合并重复验证，不能minify/调统计分母/删除功能。每阶段自己commit/push、Issue/PR沟通、日志/模块报告/handoff/prompt记录；同账号COMMENT不self-approve。

改进依据：修复已复现GHA故障夹具与AI实现中的稳定码偏差；实际全模块整合、真实组件与全分母覆盖率另证，不通过缩小范围制造通过。
