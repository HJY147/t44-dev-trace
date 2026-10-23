# 数据库模块报告：DDL AST隔离POC未准入生产

- ROLE-database-DDL-AST-POC-v1，基线正式freeze189dc4a3196be0fb84b753f23284f2566d823ea0；仅952隔离原型及本岗记录，生产模块/DDL/API/freeze/backend依赖锁/975未改。操作者AI，非学生亲改。
- 官方SQLGlot30.24.0、Python>=3.9、MIT已核；pure wheel官方hash948882...核验后仅解包ignored runtime，不进入backend环境。官方明确宽松parser非validator，MINOR也可破坏兼容，来源链接及固定发布见agents/database/ddl-ast-poc/research.md。
- 权威DDL纯解析18 CREATE/2 ALTER、18表226列59CHECK；预期来自权威DDL，旧parser Core元数据作静态差分，无实际Inspector/数据库输入，不读957或独立私有材料（仅root公开要点）。
- 首轮29/2保留：本岗adapter误读显式NULL allow_null；改适配后run2为36/1。最终必要矩阵run4为46通过/1保留失败，原全部日志/报告保留，不凑绿。
- 余下13处SQLGlot生成NOT x IS NULL，旧checker语法不支持；候选AST自身59roundtrip一致，不等于实库等价证明，也不能直接混用旧parser。生产旧checker保持原样。
- C-P4同名索引列序/unique/前缀/类型/排序、FK源目标列/库表/动作、CHECK常量/IN/OR/字符串/引导符/优先级/函数参数、列类型/NULL/default等观察均在952，严格拒绝多语句/尾别名/查询根/不支持DDL；非一般SQL validator。
- cloc2.10实测现117+321，真正可替换函数上界171、新AST函数114；仍需Core assembler/type/接入保护估60–110，联合可能增加3–53行，尚未实现。CHECK-only潜在39–46也需另行准入。当前生产节省0，不能解决整体840行缺口或声称规模通过。
- 结论：不准入整对生产替换、不改锁；若后续批准须完整assembler、独立差分及root调度新隔离MySQL验证。当前没有数据库/seed/重负载/HTTP/产品全套/覆盖率/独立验收/性能结果。
- BE短profile窗口期间已明确停止安装/批解析/测试，根宣布结束后才恢复。Ruff原F401/I001保留，952整理imports后通过；仅此必要源静态检查，不刷产品测试。
- 产物tmp/backend/persistence/952_ddl_ast_poc.py；agents/database/ddl-ast-poc/{research.md,run1..run4.json,run1..run4.log,line-estimate.json,package-metadata.json}；WORKLOG/handoff/实际prompt均保留。旧capacity与live证据在历史提交，不被POC重写。
- 发布：Issue4阶段评论https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6365574045；PR17已更新并attach，保持draft。完整阶段SHA以本轮提交及最终交接为准。
