# M6需求 模块和测试追踪

应用bc5aef9；本页只映射公开开发入口与已发布结果，不运行产品或读取独立私密。准确全源510BE/89FE见composite-bc5a-ci，不能把历史目标数重复累加。

| FR/AC | 关键实现 | 开发测试位置 | 已有证据与边界 |
| --- | --- | --- | --- |
| FR01/AC01 | api.validate_request、Runtime、Business.validateContractPayload | tmp/backend/contracts/986_http.py、985_mysql_http.py、987_faults.py | 开发全源510含真实MySQL；候选成功只结构，不证明所有551错误 |
| FR02/AC02 | persistence/rows、uow、migrations、schema | tmp/backend/persistence/988_mysql.py、989_rows.py、993_foundation.py、956_schema_semantics.py | 18业务226列/19表恢复；bounded reader66含48与2MySQL目标不累加 |
| FR03/AC03 | services/reviews.py、workflow.py | 986_http.py、985_mysql_http.py | 八段十项/证据/轮次/自评拒绝；独立完整矩阵未完 |
| FR04/AC04 | tasks/Projects.capacity、schedule_diff、history | 986_http.py、985_mysql_http.py、989_rows.py | 人力竞态/新写同Tx/旧页bounded投影；18目标/6新+1旧均重叠于全套 |
| FR05/AC05 | reviews、workflow、domain | 994_transitions.py、986_http.py、985_mysql_http.py | 风险/决定/回滚/返工；不是实际人的评审经历 |
| FR06/AC05/06 | domain/state_machine、Runtime、Call.cas | 994_transitions.py、985_mysql_http.py、987_faults.py | CAS与独立拒绝审计；全物理故障独立矩阵未完 |
| FR07/AC07 | scheduling、messaging、delivery/scans | tmp/backend/scheduling/973/974/990/991；messaging/976至980 | 准确开发CI、Docker、v2四故障子集；原消息捕获等未完 |
| FR08/AC09 | .github/workflows、CI gates、精确SHA reviewer | tmp/ci/996_gates.py及公开回执 | 510/89开发门禁、42243红/窄关闭分别；6307规模仍失败 |
| UI会话/FR01安全 | api.checkSession、clearSession、组件active | tmp/frontend/982_client.test.ts、983_application.test.ts、895_session_lifecycle_probe.test.ts | 原895 1红2绿→不改三绿；当前89含后续，不相加 |
| UI理由/FR04 | auditReason、RecordView | 982/983、tmp/frontend/872_plan_reason_browser.mjs | 89全源、42项目7写两宽度六图；组件边界不当浏览器全覆盖 |
| 部署 | deployment/ops、native lifecycle | tmp/deployment/971_credentials.py、972_compose_application.py、997_ops.py、873_native_runtime.py | Docker小规模真实；native阶段1有限，阶段2未完整运行 |
| AC08 | 三正式接口负载 | 独立原冻结入口，仅公开结果 | v1三P95失败；不读新私密入口，不用开发短跑替代 |

全部38操作输入/输出/error见[M6接口表](M6-api-contracts.md)，64源hash/函数声明见[M6源码索引](M6-function-sources.json)，当前技术[需规](../../reports/final/requirements-report.md)/[设计](../../reports/final/design-report.md)/[结果](../../reports/final/test-results-report.md)分别给行为与边界。
