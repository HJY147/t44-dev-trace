Agent-Role: backend
Prompt-Ref: ROLE-backend-DEPENDENCY-DELIVERED-REGRESSION-v1（AI本岗归档标识，实际root派工原文见 agents/backend/dependency-delivered-regression/actual-prompt.md）

从root f986782新分支codex/backend-dependency-delivered-regression；先设计536162c，再补root分配的tmp/backend/contracts/859_dependency_delivered.py。原986只有非空未交付拒绝，完整交付案无依赖；本轮补覆盖，不宣称修复应用bug。

新案通过真实SQLite/TestClient路由创建两个前驱+依赖两者的任务；0/2交付拒绝且task/version/边不变，第一条实际开发→代码评审→上线预案审核→经理发布后1/2仍拒绝，两条均state6后才允许developer开工200/state2/version+1并保留依赖。复用原986 helper，不set_state/改表或mock业务。新859+原986相邻依赖案仅2项实际passed/0fail/error/skip，保留现有TestClient弃用warning；不是全量CI/实库/性能或独立验收。

Ruff check通过；format首次仅一处列表换行失败原件保留，格式器修正后Ruff+format通过，前后AST（无位置属性）完全同，未重复2项pytest。应用字节仍精确C=b66fa36，不改代码/锁/冻结/原用例；没有触发CI、外部HTTP/MySQL/服务/负载或接触任何独立材料/860。

公开性能摘要performance-summary.md已先交root：静态升级列表10+3P、契约4/5/5查询及连接生命周期是线索；短池ABBA重建436/427对0支持有限候选，但不能归因正式P95/503。候选C只project谓词且EXPLAIN为估算，开发CI绿不等于性能。规模固定6307仍超1207，无法承诺无风险减完；大范围/架构或课程口径选择须人确认，不删功能/改统计凑数。

原件和范围：agents/backend/dependency-delivered-regression/{design.md,report.md,summary.json,targeted-command.json,targeted.log,targeted.xml,format-initial-failure.log,format-only-proof.json}。作者/执行者后端AI，不记学生亲改。本阶段交接后释放，后续正式测量另授权。
