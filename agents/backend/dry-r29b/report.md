# 后端 DRY r29b 模块交接

- 操作者：固定后端 AI；Prompt：ROLE-backend-DRY-R29B-v1；关联 Issue #3。
- 起点：`a92e5e73da93ba23748c3bab113103036c395d50`；产品提交：`41a111f270e949326202b8af5770db8aa7102e82`。
- 实际产品范围：仅 `backend/t44/services/reviews.py`。两处最新上线评估查询共用 `_latest_assessments(g, task_id)`。
- 输入/输出保持：同表、同 task_id、同 `-rollback_plan_version`、同 limit=1、原列表返回；创建处空列表仍起版本1，批准处原 `[0]` 保留。无新跨岗签名。
- 原调用位置、守卫、角色/错误优先级、版本/CAS、审计、事务、幂等与 MQ 未改。冻结契约/DDL和原测试/断言无改动。
- 新18场景比较准确基线和候选的输出/错误、查询顺序、写入和审计 diff，含创建/批准/驳回、空列表、角色、状态、责任人、评估基线及版本冲突。
- 原986/856 SQLite HTTP模块与新场景合计152项通过，0失败/错误/跳过，50.23秒；1条上游 Starlette 弃用警告保留。
- 差分验证隔离了序列化；原 HTTP 模块验证实际序列化、Runtime、幂等、审计和上线错误优先级。本地 SQLite 不证明 MySQL 锁或真实消息投递。
- `boundary-proof.json`：仅展开新 helper 后整个 Reviews 模块 AST 与基线一致；原 `tmp/backend` 测试 diff 为空。Ruff检查、格式和 `git diff --check` 通过。
- 固定原脚本、固定 cloc2.10、committed HEAD计量：应用 **5887 → 5884，净减3**；目标5100，仍超784，`--require-range` 退出 **1**。Reviews本文件代码行见原始计量JSON。
- 对服务模块作有限重复赋值/return AST扫描，未见值得实施的更大完全重复块。没有为了扩大差额改写职责或引入通用框架。
- 没有运行完整CI、MySQL、RabbitMQ、云、正式性能或独立验收；未读 PRIVATE/未发布独立用例，未联系独立测试岗。没有 merge。
- 原始执行命令/结果：`module-command.json`、`module-tests.log/xml`、`count-command.json`、`count-before.json`、`count-after.json/log`；早期探索命令失败见本岗 WORKLOG。
- 建议：交总协调按准确 SHA 审核后决定集成。该候选只贡献3行，不应把准备或模块通过记为总规模门通过。
- GitHub本岗候选留痕：https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6489275840；产品阶段分支已push，最终证据提交随后push，不代总协调merge。
