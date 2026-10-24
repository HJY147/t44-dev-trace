# M5 需求到设计 实现及本模块测试追踪

生产基线6ba9f94；规格1.1.0/14文件。此矩阵由文档AI据已发布实现和结果补充，不倒填开发前已完成；既有[M2矩阵](M2-traceability.md)和旧命令/日志保留。本轮未执行产品/测试/负载。

| FR / AC | 概设与详设 | 真实实现入口 | 本模块用例/已发布证据 | 剩余系统验收 |
| --- | --- | --- | --- | --- |
| FR01 / AC01 | API门面、冻结输入输出/错误/版本；单读UoW | api.create_app、Runtime.execute、Business.validateContractPayload | tmp/backend/contracts/986_http.py、985_mysql_http.py；5dcb11HTTP+7真MySQL并入412 | 独立4c149错误仅Schema观测，不是全551语义/拒绝审计 |
| FR02 / AC02 | 18表226列、参数化Rows、显式迁移及语义检查 | persistence/schema/rows/migrations；UoW/Engine | tmp/backend/persistence/993、989、988、956、975；旧live漂移/恢复和seed摘要，C-P4限定复审 | 全DDL/应用连接/存储副作用白盒与新头审核，不能由独立列结构核对代替 |
| FR03 / AC03 | 八段十项/对象SHA/轮次/不可变证据 | Reviews、Workflow、domain及前端评审表单 | 994_transitions、986/985、tmp/frontend/983；模块/真HTTP及独立REV子集分层 | 全模板/轮次/角色/证据真实性，synthetic不作真人记录 |
| FR04 / AC04 | 项目依赖图锁、1.1容量生命周期、计划diff | Tasks.createTask/changeTaskAssignment；Projects.changeIteration；Workflow返工 | 986/985容量专项及4c CI394；独立STAFF创建/转派/返工各30竞争；schema版本夹具失败保留 | 全依赖并发/已交付前驱正例/完整角色与拒绝副作用 |
| FR05 / AC03/05 | 当前评估/批准、改期失效、回滚/返工新轮 | Reviews、Workflow、decide与TaskDrawer | 994/986/985、FE983；IAT01–05开发原红绿/CI362历史、v2 REL/LIFE子集 | 全非法组合/持久证据/完整独立矩阵 |
| FR06 / AC05/06 | typed命令、task CAS、幂等claim/complete、独立拒绝审计 | Runtime、Call、domain、Rows | tmp/backend/contracts/987_faults.py、985；v2 CAS30双请求；开发完整412包含原断言 | 提交ACK丢失、同键竞态/租约接管、audit-only真实故障及精确计数 |
| FR07 / AC07 | Scanner持久run/游标、最高档/完整收件人、outbox/消费提交后ACK/fallback | scheduling/{scanner,facade}；messaging/{facade,worker,broker}；OutboxStore/ScanStore | tmp/backend/scheduling/974、991、990、973；messaging979/980/977/976/978；旧调度107、真Rabbit托管与模块原件 | 中批cursor恢复/101人实际投递/边界时钟/迟到原消息；后收到故障子集不当完整通过 |
| FR08 / AC01/09 | 组合根DI、全源码CI、精确SHA审核及部署CLI | Runtime/Business、product.yml、ops、acceptance环境工具 | tmp/deployment/997、971、953，tmp/ci/996；5dcb四job与f118中性能力，6ba后发同源组合CI/恢复另列 | reviewer/stage整产品、独立剩余矩阵、6051超951、正式P95及学生本人研究材料 |

## I/O与当前图示

- [M5函数契约](M5-function-contracts.md)/[准确源码索引](M5-function-sources.json)逐层核实际签名、输入输出/调用方/前后置/异常/事务；不使用猜测方法。
- [SRS](../../reports/final/requirements-report.md)按范围/角色、编号FR、输入输出/异常、量化非功能与AC组织；[设计](../../reports/final/design-report.md)分概设和详设，两组方案比较沿用真实历史。
- [新三图](M5-diagrams.md)为容量生命周期、真实需求变更链、七入口UI导航；已在18:40授权窗口真实渲染并逐张PNG实看，八旧图不重跑。
- 现行pytest入口`pytest -c backend/pyproject.toml tmp/backend`、前端`pnpm --dir frontend test:coverage`仅为已配置入口说明，本文未执行。文件迁移映射见records/validation/test-file-layout.json，历史backend/tests等命令不倒改。

## 跨模块同步与当前限制

1.1仅人力安排规则演进、metadata版本与声明分支同步；DDL/状态机边不新增，普通转派仍只原允许阶段。read-UoW仅validateContractPayload，未泛化全部GET或改写路径。UI75仅props边界，未改业务Schema。

模块自测、真依赖、完整CI、限定源码审核、独立阶段与正式性能分别记录于[测试报告](../../reports/final/test-results-report.md)。后收到的独立fault四子集与6ba同源CI另列发布时点；不把未来数据倒填本矩阵输入版本，不把模块数相加凑全局总数。
