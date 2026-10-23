本阶段评估SQLGlot能否替换重复DDL/CHECK语法处理，结论是**未证明整对生产替换必要性/净删，不准入生产**。只增加隔离952原型及数据库岗记录；生产模块、DDL/API、freeze和backend依赖锁不变。原有持久层阶段和真实MySQL证据保留在历史提交，不以本次解析替代。

952显式CLI对权威18表226列59CHECK做静态差分，预期来自权威DDL及旧独立parser，不来自实际反射。最终46通过/1保留失败（exit1）：13个CHECK由SQLGlot生成`NOT x IS NULL`，旧checker不接受；新AST内部59roundtrip一致不等于执行等价。初次NULL adapter误读与Ruff失败、修正后结果均保留。

源码/证据：`tmp/backend/persistence/952_ddl_ast_poc.py`、`agents/database/ddl-ast-poc/{research.md,run1..run4.json,run1..run4.log,line-estimate.json,summary.json}`。SQLGlot30.24.0 pure wheel仅在ignored runtime按官方SHA解包，未改backend环境。官方宽松解析器不是SQL validator，完整Core assembler与原生反射验证均未实现。

同口径cloc实测旧可替换上界171、新AST114；尚需assembler/type/严格接入保护估60–110，联合可能增加3–53行。CHECK-only潜在39–46仍需单独设计。当前生产节省0，不宣称整体代码规模通过。不改生产旧checker来迁就渲染、不删除失败、不从反射生成预期。

验证限纯解析与952针对性Ruff；无数据库/seed/HTTP/重负载/产品全套/coverage/独立验收/性能结果。本PR保持draft，后续生产替换须另行准入。

Agent-Role: database
Prompt-Ref: ROLE-database-DDL-AST-POC-v1
Refs: #4
