# M6当前函数和模块输入输出

源码固定 `bc5aef9c62393134582affb7a690acb33ac2b833`，64源hash及全部Python真实签名见[M6索引](M6-function-sources.json)。本页是静态源码说明；未导入或执行产品。

## 后端 存储 消息和调度

| 准确函数与签名 | 输入到输出 | 前后条件 异常 事务和副作用 |
| --- | --- | --- |
| [validate_request](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/api.py#L104) `validate_request(request, operation, c)` | operation/path/query/body等输入→校验结果或Rejected；冻结Schema/时间域约束 | 只结构验证，不提交业务，不替代状态/人力/依赖守卫 |
| [Runtime.prepare](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/runtime.py#L45) `Runtime.prepare(self, call, validate)` | Call和validate回调→幂等已有结果或None；可拒会话/结构/意图冲突 | 实时鉴权；写意图claim在明确UoW；validateContractPayload有独立只读专路 |
| [Runtime.execute](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/runtime.py#L235) `Runtime.execute(self, call, validate, source='unknown')` | Call/validate/source→(HTTP status,payload,replayed,原response request_id或None) | 统一成功事务；拒绝另事务审计；CommitUncertain返回503，不能假定服务端未提交 |
| [Runtime.rejection](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/runtime.py#L85) `Runtime.rejection(self, call, error)` | Call/Rejected→四元组错误/审计ID | 业务事务先回滚，独立拒绝审计；审计不可用为AUDIT_UNAVAILABLE，不能造audit_id |
| [Business.validateContractPayload](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/application.py#L108) `Business.validateContractPayload(self, g, c)` | 三category候选及可选task→valid/category/operation/schema_version/business_guards_executed:false | 只结构/时间；无task/audit/outbox/idem写入；候选1.0与外层1.1分开 |
| [Business.listProjectAuditEvents](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/application.py#L132) `Business.listProjectAuditEvents(self, g, c)` | 已授权g/Call及page/filter/sort→AuditEvent分页dict | 先原page/COUNT/order，再当前页project_reasons；不额外读取别项目页 |
| [_snapshot](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/history.py#L11) `_snapshot(audit)` | 单个审计dict→(before,after,old_schedule,new_schedule)或None | 成功human、task、无reason/字段上限、指定动作/7→2、版本规范+1；不做SQL |
| [_matches](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/history.py#L57) `_matches(audit, snapshot, change, project_id)` | 审计/已核快照/唯一schedule_change/project→bool | 完整Plan生产字形、actor/微秒时间/版本/双侧合法EvidenceRefs及精确JSON；不trim字符串/排序数组 |
| [project_reasons](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/history.py#L93) `project_reasons(g, project_id, result)` | 活动g/授权project_id/原分页结果→同一分页dict | 提取本页pairs，0或1次bounded batch；仅响应copy after追加原文，不改DB/order/total/重放 |
| [RowsGateway.task_schedule_changes](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/persistence/rows.py#L195) `RowsGateway.task_schedule_changes(self, project_id: int, pairs: tuple[tuple[int, int], ...]) -> list[dict]` | 正整数project_id、tuple[(task_id,to_version)]≤100→list[完整行dict] | 拒bool/超界/坏形状StatementRejected；结果跨项目/重复/多余/超界毒化并PersistenceUnavailable；不提交 |
| [Projects.schedule_diff](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/projects.py#L173) `Projects.schedule_diff(self, g, c, before, after, *, iteration=False)` | g/Call、前后行、iteration flag→None | 插schedule_changes与c.after reason；任务另添版本和五Plan字段；随调用者事务，不自己commit |
| [Tasks.createTask](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/tasks.py#L58) `Tasks.createTask(self, g, c)` | TaskCreate/有效owner/capacity/deps→{task} | manager、项目锁/CAS关联规则；异常不留半写 |
| [Tasks.changeTaskPlan](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/tasks.py#L102) `Tasks.changeTaskPlan(self, g, c)` | 任务ID/expected_version/Plan/reason/evidence→{task} | 拒已交付/回滚；CAS计划/排期版本、失效批准预案、同Tx差异理由 |
| [Tasks.changeTaskAssignment](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/tasks.py#L124) `Tasks.changeTaskAssignment(self, g, c)` | 任务ID/version/owner→{task} | 仅原允许状态，有效developer后capacity；缺工时CAPACITY_REFERENCE_INVALID |
| [Projects.changeIteration](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/projects.py#L145) `Projects.changeIteration(self, g, c)` | 迭代ID/version/计划capacity/reason→Iteration | 检查全部状态1至5负责人；不混成员1至5加7保护；CAS/差异同Tx |
| [Workflow.transitionTask](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/workflow.py#L61) `Workflow.transitionTask(self, g, c)` | TransitionRequest/可信快照→{task,decision或None} | typed Command→decide→effects/CAS；返工重验人力/计划/依赖，schedule_diff/决定同Tx |
| [decide](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/domain/state_machine.py#L90) `decide(position: TaskPosition, command: Command, context: TransitionContext) -> Decision` | TaskPosition/typed Command/TransitionContext→不可变Decision | 无SQL/网络/文件/提交；DomainViolation由服务映射冻结错误 |
| [Call.cas](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/services/common.py#L153) `Call.cas(self, g, table, row, values, *, expected=None)` | g/表/旧行/values→更新行 | expected_version乐观版本，失败拒绝；追加前后版本差异，不自提交 |
| [SqlAlchemyUnitOfWork.__exit__](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/persistence/uow.py#L87) `SqlAlchemyUnitOfWork.__exit__(self, exc_type, exc, traceback) -> bool` | 异常三元组→False | 正常commit、异常rollback、finally close；毒化不能commit，未知确认语义保留 |
| [DeliveryWorker.cycle](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/messaging/worker.py#L33) `DeliveryWorker.cycle(self)` | 已注入store/publisher/consumer→各类计数dict | 短事务claim、事务外publish、token确认；先DB消费提交后ACK，计数非用户已读 |
| [consume_delivery](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/messaging/broker.py#L122) `consume_delivery(store, channel, method, body)` | store/channel/method/JSON bytes→consumed或quarantined | 只信三字段并查权威DB；坏消息reject不重投，持久故障NACK并抛 |
| [Scanner.run](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/scheduling/scanner.py#L102) `Scanner.run(self, run_id=None)` | 可选run_id→持久scan_run | cutoff/keyset/续扫；结果确定后推进游标，有限版本重试，不吞其他故障 |
| [EscalationFacade.create](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/backend/t44/scheduling/facade.py#L106) `EscalationFacade.create(self, g, c)` | 活动g/服务Call→{event,created,task_version} | 服务scope/project/task/版本/规则重验；同task/schedule/level一次，随Runtime提交，202非送达 |

## 前端会话和理由

| 源码函数或组件 | 输入到输出 | 边界 |
| --- | --- | --- |
| [request/checkSession](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/frontend/src/api.ts) | operation/params/query/body/Intent→Promise Envelope；token→void或ApiError | fetch与JSON解析前后重验；旧身份成功/错误均SESSION_CHANGED；当前401清会话，NETWORK_UNCERTAIN不换意图重做 |
| [intentFor](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/frontend/src/api.ts) | operation/params/body/previous→fingerprint+key | 内容未变保留key；内容变化形成新意图，需先确认旧未知结果 |
| [clearSession/context/bootstrap/allPages](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/frontend/src/workspace.ts) | notice或授权读取→更新reactive workspace | clearSession清token/项目/成员/字典并递增sequence；异步结果核token/project/sequence |
| [OperationForm.submit/组件卸载](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/frontend/src/components/OperationForm.vue) | draft/checkOnly→结构检查、API意图、saved/close | active+当前token门禁覆盖success/catch/refresh；卸载旧表单不清新身份数据；当前403/409仍权威刷新 |
| [LoginView.login与TaskDrawer.refresh](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/frontend/src/components/LoginView.vue) | 登录输入或task/tab/page→当前身份/任务记录 | active/session/sequence阻止迟到写回；密码finally清空，不在正文打印 |
| [auditReason](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/frontend/src/audit.ts) | Row→{text?,missing}或undefined | 只单个有效reason，保留字面；相关成功变更缺理由标missing，原记录不改 |
| [RecordView](https://github.com/HJY147/t44-dev-trace/blob/bc5aef9c62393134582affb7a690acb33ac2b833/frontend/src/components/RecordView.vue) | Json/field→递归DOM和纯文本理由 | 不经日期display改写reason；默认转义HTML，缺失/原始未核对条目标识，其他actor/time/evidence仍可见 |

## 验证边界

bounded reader原66含48、2MySQL目标；BE0549最终18含既有回归；bcb窄修7含6新+1旧；当前bc5 510/89完整集合均相互包含或重叠，不累计。原42243 HTTP红与bc5同例绿仅限定历史证据比较，不证明所有历史都可恢复。前端真实42项目两宽度六图不等于全部组件边界都浏览器覆盖。详见[M6追踪](M6-traceability.md)与[测试报告](../../reports/final/test-results-report.md)。
