# M2 需求到设计、实现与本模块测试追踪

基线：冻结1.0.0；完整模块集成265d89b（先经f3235ba），测试机械迁移5e07887。**本表用于审查证据，不是独立验收/性能报告。** 先前规范设计和M1报告commit保留；M2图表与映射是开发中补充，不倒填为开发前已完成。

## FR映射

| FR | 概设责任模块 | 详设机制/实际实现 | 本模块测试入口（当前路径） | 证据和剩余系统验证 |
| --- | --- | --- | --- | --- |
| FR-01 | API/客户端/契约 | [api.create_app](../../backend/t44/api.py)、[Runtime.execute](../../backend/t44/services/runtime.py)、冻结OpenAPI | [986_http](../../tmp/backend/contracts/986_http.py)、[985_mysql_http](../../tmp/backend/contracts/985_mysql_http.py)、[982_client](../../tmp/frontend/982_client.test.ts) | 后端ec82正式报告：38操作/53 TCP+MySQL请求Schema；全错误分支证据仍逐项核，非独立验收 |
| FR-02 | persistence | [schema/migrations](../../backend/t44/persistence/migrations.py)、[RowsGateway](../../backend/t44/persistence/rows.py)、冻结字典/DDL | [988_mysql](../../tmp/backend/persistence/988_mysql.py)、[989_rows](../../tmp/backend/persistence/989_rows.py)、[993_foundation](../../tmp/backend/persistence/993_foundation.py) | 18表迁移及负向约束有真MySQL分批证据；SQLite基础另列，不代实库 |
| FR-03 | reviews/前端评审 | [Reviews](../../backend/t44/services/reviews.py)、[评审配置](../../backend/t44/resources/review-template.json)、[OperationForm](../../frontend/src/components/OperationForm.vue) | 986_http、985_mysql_http、[983_application](../../tmp/frontend/983_application.test.ts) | 八段十项/缺证据/非自审及浏览器流程；synthetic review不算学生或真人审查 |
| FR-04 | tasks/projects/持久层 | [Tasks](../../backend/t44/services/tasks.py)、[Projects](../../backend/t44/services/projects.py)、Runtime图锁/计划差异 | 985_mysql_http、989_rows、[994_transitions](../../tmp/backend/backend/domain/994_transitions.py)、[984_browser](../../tmp/frontend/984_application-real-browser.mjs) | 同项目/自边/环/前驱/排期差异分层验证；新场景按最终SHA继续 |
| FR-05 | reviews/workflow/决定 | [Workflow.transitionTask](../../backend/t44/services/workflow.py)、评估/决定FK和轮次守卫 | 986_http、985_mysql_http、983_application、984_browser | 四视角/预案/经理交付回滚返工真实路径；不代表执行外部云回滚 |
| FR-06 | domain/Runtime/UoW | [state_machine.decide](../../backend/t44/domain/state_machine.py)、[稳定codes](../../backend/t44/services/codes.py)、[UoW](../../backend/t44/persistence/uow.py) | 994_transitions、985_mysql_http、[987_faults](../../tmp/backend/contracts/987_faults.py) | CAS/重放/独立拒绝/提交不确定分层；领域覆盖不代全产品 |
| FR-07 | scheduling/messaging/persistence | [Scanner](../../backend/t44/scheduling/scanner.py)、[EscalationFacade](../../backend/t44/scheduling/facade.py)、[DeliveryWorker](../../backend/t44/messaging/worker.py)、[OutboxStore](../../backend/t44/persistence/delivery.py) | [974_application](../../tmp/backend/scheduling/974_application.py)、[973_rules](../../tmp/backend/scheduling/973_extensible_rules.py)、[980_delivery](../../tmp/backend/messaging/980_delivery.py)、[977_rabbit](../../tmp/backend/messaging/977_rabbit.py)、[976_process_mysql](../../tmp/backend/messaging/976_process_mysql.py) | 20任务/续扫/真MySQL/局部真Rabbit与自动fallback分别限定；非正式压测 |
| FR-08 | 组合根/CI/审核 | api门面DI、[工作流](../../.github/workflows/product.yml)、[ci入口](../../scripts/ci/run_tests.py)、准确SHA审核 | [996_gates](../../tmp/ci/996_gates.py)、[997_ops](../../tmp/deployment/997_ops.py)，产品模块入口分列 | 历史17/当前23配置安全检查不代完整Docker集成；265d89b四产品job成功；reviewer/stage与新版完整审核另验 |

## 每个部分自己的验证边界

| 岗位 | 本轮可用事实来源 | 真实执行和边界 | 当前命令/路径含义 |
| --- | --- | --- | --- |
| frontend | [模块报告](../../reports/modules/frontend.md)/handoff及root迁移回执 | 21模块测试，whole frontend行92.21%；七态真实浏览器和1440/390检查；当时通知接口503不掩盖 | `pnpm --dir frontend test`；迁移后21通过由root已报告；tmp/frontend为当前源 |
| backend | 本轮原文问答与ec82最终报告；旧初失败日志保留 | 二轮314通过/3本机Rabbit skip，全t44行87.78%；38/53实际TCP+MySQL及CLI撤销/自动fallback | `python -m pytest -c backend/pyproject.toml tmp/backend`为当前入口；迁移后仅317 collect成功，未重跑全量 |
| database | [模块报告](../../reports/modules/database.md)/handoff、已发布真实MySQL/seed结果 | 通用SQLite/mock与真MySQL分批；40项目6000任务9000依赖、11400评审+3600决定全为synthetic | tmp/backend/persistence；旧run1..日志仍保留旧命令，不能加总成最终验收 |
| messaging | [模块报告](../../reports/modules/messaging.md)/handoff | 本地28通过/3真Rabbit未配；11真MySQL；早期b5a16e6三真Rabbit托管CI通过，整体run有其他失败 | tmp/backend/messaging；早期CI不套到最新head，新的成功网络/全CI需另证 |
| scheduler | [模块报告](../../reports/modules/scheduler.md)/handoff | 107通过，22真MySQL/ASGI/CLI；20任务与进程退出续扫；83%仅scheduling且CLI子进程未汇入 | tmp/backend/scheduling；不是本机Rabbit网络/400并发/独立验收 |
| deployment | 本轮实际回复f052及已发布报告 | 历史11安全+6守卫、当前23 guard/config；f052接线已发布，真实Docker job39932416571进行中，尚未报成功 | tmp/deployment/997_ops.py、tmp/ci/996_gates.py；265d89b四job成功；Docker运行结果待owner最终回执 |
| documentation | M2来源/冻结/链接/图表/隐私检查 | 只核对文档和证据，产品测试0 | M1旧校验迁至tmp/documentation/992_report_drafts.py；旧证据不改写，M2不拿文档检查计产品覆盖率 |

编号与[迁移清单](../../records/validation/test-file-layout.json)、[tmp说明](../../tmp/README.md)一致：27脚本999..973按Git首引入时刻、同批按旧路径排序；conftest.py/__init__.py保留框架名，不含独立用例。新文件需领下一个编号，文档岗不改产品测试或私有验收用例。

## 证据分级

设计静态/Schema → 模块unit/SQLite/mock → 真实MySQL/HTTP → MQ网络/跨进程 → 集成整套 → CI门禁 → 独立验收/正式性能，各层分别记录。当前任何“通过”只对相应版本、命令、环境和范围有效；本表不以局部数据推断未运行层次通过。

最新整合CI：265d89b / run39931640641四job成功，覆盖率整套317通过/0失败/0跳过，whole Python2399/2724=88.07%、前端308/334=92.21%；[归档](../../records/ci/39931640641/junit-summary.json)及[M2快照](M2-ci-snapshot.json)。这是迁移后的实际执行，不能反向改写岗位本机仅collect的快照。仍不代表独立验收/性能/最终LOC。
