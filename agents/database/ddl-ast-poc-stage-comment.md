数据库岗本阶段仅完成隔离POC，**不准入生产替换**。Agent-Role: database；Prompt-Ref: ROLE-database-DDL-AST-POC-v1；基线189dc4a3196be0fb84b753f23284f2566d823ea0。操作者为AI，不是学生亲改。

- 原型：`tmp/backend/persistence/952_ddl_ast_poc.py`；证据与可重复命令：`agents/database/ddl-ast-poc/`。仅纯解析权威DDL（18表/226列/59CHECK），预期未由实际反射倒造。
- 官方SQLGlot30.24.0/Python>=3.9/MIT已核，wheel按官方SHA核验后只解包ignored runtime。官方FAQ明确宽松parser不是validator：https://sqlglot.com/sqlglot.html#faq 。生产模块、DDL/API、freeze、backend环境/依赖锁均未改。
- 首次29通过/2差异来自本岗adapter误读显式NULL的allow_null，原日志保留。修正后最终46通过/1失败（exit1）保留：13个CHECK生成`NOT x IS NULL`，旧checker不接受该文本；新AST自身59次roundtrip稳定只说明内部正常形稳定，不证明MySQL执行等价。未改旧checker迁就库，也未删失败凑绿。
- 覆盖列类型/NULL/default、同名索引列序/unique/前缀/类型、FK目标库表列/动作、CHECK字符串/引导符/优先级/函数及严格拒绝观察。完整SQLAlchemy Core assembler和原生反射接入未实现；952正常pytest收集不导入新库、运行矩阵或skip。
- 固定cloc2.10按原口径：旧最大可替换函数171行，新AST函数114行；仍需assembler/type/接入保护估60–110行，联合可能增加3–53行。CHECK-only潜在39–46行仍是未准入估算。**本轮生产实际节省0**，不声称总规模达标。
- 没有数据库/seed/HTTP/重负载/产品全套/coverage/独立验收或性能运行。952首次Ruff F401/I001保留，imports整理后针对性Ruff通过；没有因样式重复跑矩阵。

研究结论、行数拆分、原始失败和文件摘要见`research.md`/`line-estimate.json`/`summary.json`。后续是否单独设计CHECK-only或完整adapter由总协调/reviewer另行派工；本阶段不改锁、不申请新库、不代设审核通过。Refs: #4。
