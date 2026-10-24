# 本轮实际派工（AI总协调原文）

> 用户醒来，问性能/规模具体问题和需要人决定的大问题，同时授权其他可自主事项继续。请在自己worktree新codex分支基root最新（先读AGENTS/git；不改root索引），先设计短任务再执行：1）核你现有公开静态查询成本/池短ABBA/最新C，写明已知瓶颈线索vs未证实，不读任何独立private/cases/raw/860，也不contact tester。2）继续一个明确、可逆、非需求变更的质量小项：专审已披露986没有‘非空前驱全部已交付后依赖任务成功开始’场景，请基冻结业务设计一个有意义HTTP回归，用既有测试风格验证该合法场景及未满足阻止（先检查现有覆盖避免重复）；新测试必须tmp/backend，编号向root申请，我暂时分配859并会登记，勿占其他号。应用代码不因测试修改，若发现缺陷先记录通知root，不降低断言。只SQLite/TestClient本机内存回归、ruff；不本机MySQL/HTTP外部/任何负载/CI或服务动作。3）实际role日志/module/handoff/prompt、GitHub Issue3对接并全文GET、commit/push。先5min内发性能中文摘要，最多15min完成小项。不能声称新formal性能已过/旧FAIL取消。

作者/后续测试操作者：后端AI。ROLE-backend-DEPENDENCY-DELIVERED-REGRESSION-v1为本岗归档标识，原派工未自带该ID。
