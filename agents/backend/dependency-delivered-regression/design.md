# 有界质量回归：全部前驱交付后开工

基根f986782311f227082b4445bf7508522aa49c043d，新分支codex/backend-dependency-delivered-regression；自有原干净worktree，根索引不动。实际应用与固定C=b66fa36逐字相同（仅Workflow项目谓词，相对bc5一行），不改应用/锁/规范/资源。

冻结业务依据specs/business-rules.md“待受理：依赖全部已交付才可开始开发”。静态检查既有986.test_dependencies_cycle_guard_and_edit_lock只验证一条未交付前驱拒绝，完整delivery用例没有依赖；原985无完整非空前驱交付→下游开工场景。新859不是重复常量/谓词镜像，也不要求制造缺陷红绿。

root正式分配tmp/backend/contracts/859_dependency_delivered.py。复用986的request/setup_project/create_task/transition/review_payload/assessment_payload，沿真实TestClient路由和SQLite RowsGateway。只HTTP写建两个前驱与一个依赖两者的下游：0/2交付拒绝且下游状态/版本不变；经真实开发→代码评审→预案评审→经理发布交付第一条后，1/2仍拒绝；两条全部实际交付才成功开工且版本加一，依赖关系保留。每次响应按原request校验冻结Schema，原测试不改，不直接set_state/改表制造交付。

仅跑859与原986依赖拒绝案两项，再Ruff/format新文件。无MySQL/外部HTTP/服务/负载/全量CI；提交均skip-ci。失败原件保留，若暴露应用缺陷先报root，不修应用/降断言。结果只开发内存HTTP覆盖新增，不是独立验收或性能。证据、角色日志/模块报告/handoff及Issue3全文GET归档。
