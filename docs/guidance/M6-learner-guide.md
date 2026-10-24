# M6：怎样读懂和检查本项目

这是 AI 指导资料，面向第一次接触前后端的学生；不是学生本人研究正文或操作成绩。代码说明固定在 `0783a42b26038d7d3e5a1fe07ae8219a47f06493`，文件哈希与函数行号见 [来源清单](M6-source-manifest.json)。下面所有练习均**未由学生完成，本岗也未运行**；没有亲改代码、打断点或独立识别幻觉的新证据。

学生在 [R001 原话](../../records/reflections/R001-original.md)中提出：人要把关需求、结构、封装和重要函数输入输出，审阅反复使用的代码，并把关自动测试的要求、过程与决策。这是本指南的学习依据；R001 不证明学生已经写过本项目框架或调试过代码。[R002 公开出处](../../records/reflections/R002-provenance.json)只说明课程反馈已提供、最终研究正文未提供；本岗未读其私密原文。

编写期间 root 补充：Issue28 后端0549与前端c79已合入新组合 `42243eb23aedf0edda7541ad83fd87ec3d17b616`，CI刚触发；本指南不等待或预判其结果，讲解仍按上述固定基点。

## 1. 先认识六个东西

| 名称 | 在本项目做什么 | 先看哪里 |
| --- | --- | --- |
| Vue 前端 | 浏览器中的表单、列表、提示；把输入发给服务器 | [WorkspaceView.vue](../../frontend/src/views/WorkspaceView.vue)、[OperationForm.vue](../../frontend/src/components/OperationForm.vue) |
| 接口契约 | 约定某种请求允许什么字段、返回什么数据和错误 | [OpenAPI](../../specs/contracts/openapi.json)，1.1.0，31 路径、38 个 operationId |
| FastAPI 后端 | 校验请求，核对身份、权限、状态和业务条件，调用业务函数 | [api.py](../../backend/t44/api.py)、[Runtime](../../backend/t44/services/runtime.py) |
| MySQL 与事务 | 保存任务、版本、审计和待发事件；同一事务的操作一起提交或回滚 | [UoW](../../backend/t44/persistence/uow.py)、[RowsGateway](../../backend/t44/persistence/rows.py) |
| RabbitMQ 与消息进程 | 把已保存的事件可靠投递，再落站内通知 | [worker.py](../../backend/t44/messaging/worker.py)、[broker.py](../../backend/t44/messaging/broker.py) |
| scanner 与定时器 | 定期从数据库读候选任务，判断临期/超期，留下扫描进度 | [scanner.py](../../backend/t44/scheduling/scanner.py)、[runtime.py](../../backend/t44/scheduling/runtime.py) |

前端有一个按钮不代表这个账号有权执行。浏览器传来的内容需要后端重新检查。38 个操作也不等于 38 套手写客户端：前后端都从契约提取 operationId、方法和路径；运行契约副本在 [backend/t44/contracts/openapi.json](../../backend/t44/contracts/openapi.json)，本次只读比较与权威文件字节相同。

## 2. 顺着“调整任务排期”读一遍

先只追这一条路线，不必从头通读所有文件。`params` 是 URL 中项目/任务编号，`draft` 是用户填的 JSON，`Call` 是后端为本次请求保存的上下文，`g` 是当前事务内的数据库访问门面。

| 顺序与真实入口（基点行号） | 输入 → 输出；要检查的事 |
| --- | --- |
| ① `TaskDrawer.operate()`（41） | operation、当前 task → 向父组件发 operation/schema/params/preset；按钮实际调用 `changeTaskPlan`。`presets()` 从任务带入 `expected_version` 和当前 plan。 |
| ② `OperationForm.submit()`（28） | 表单 draft → 本地 `validate()`；错误则停止。内容合格后 `intentFor()` 生成或复用同一操作的 key，再调用 `request()`。 |
| ③ `api.request()`（17） | operation/params/query/body/intent → `Promise<Envelope>`；查映射，拼 `/api/v1` 路径，带 Bearer、JSON、Idempotency-Key；失败抛 `ApiError`。TS 的返回类型断言不等于完整响应运行时校验。 |
| ④ `create_app()` 内 `endpoint().handle()`（215/216） | HTTP → `Call` → `Runtime.execute()`；返回状态、结果、是否重放、原追踪编号。成功包装 `{data, meta}`，错误返回契约错误对象。 |
| ⑤ `Runtime.execute()`（235） | Call/校验回调 → 先认证/校验和写请求的幂等 claim，再开主 UoW 锁定作用域、分派业务。只读校验、login、logout各有专门分支。 |
| ⑥ `Business.dispatch()`（38）→ `Tasks.changeTaskPlan()`（102） | 当前事务的 g 与 Call → 查经理权限、任务归属及非终态，解析五项 plan，调用 `Call.cas()`；返回 `{"task": …}`。不是 `execute_operation` 或统一 `save_task`。 |
| ⑦ `Call.cas()`（153）→ `Projects.schedule_diff()`（173） | 旧行/期望版本/新值 → 带版本条件的更新，必须影响 1 行，增加 task.version 和 schedule_version；写 schedule_changes 的前后 plan、reason、evidence，撤销旧上线批准。 |
| ⑧ 回到 `Runtime.execute()`（274）及 `UoW.__exit__()`（87） | 主事务继续写成功 audit、outbox、幂等完成快照并检查 data；`with` 正常退出才 commit。业务函数先返回的数据仍可能随后回滚。 |
| ⑨ 回到表单及 `WorkspaceView.saved()`（56） | `{data, meta}` → 成功/历史重放提示，再读最新列表和详情；旧请求重放结果不是“现在的任务状态”。会话已变化或组件卸载时，旧响应不得回写新身份。 |

`TaskPlanChange` 要求 `expected_version`、`plan`、`reason`、`evidence`。plan 五项是起止 UTC 时间、预计工时、缓冲工时、延期预案；结束晚于开始，工时按 0.25 小时约束。数据库用四分之一小时整数保存工时，接口仍用小时；转换见 [common.py 的 plan/plan_values](../../backend/t44/services/common.py)。别把界面上的小时直接当数据库整数。

有三个“版本”要分开：`meta.contract_version` 是接口版本；`task.version` 防止别人改过后你覆盖旧数据；`schedule_version` 标记排期轮次。幂等 key 则标识一次请求意图：网络不确定时保留内容及原 key 重试，内容变更才形成新意图；它不代替版本冲突检查。读到 `409` 时先看具体 code，不能把所有 `409` 都当成同一个原因。

如果业务拒绝，主事务先回滚，再由 `Runtime.rejection()` 用新 UoW 留拒绝审计。幂等 claim 的独立事务可能已存在，不能据此认为任务保存成功。若提交确认不明，返回 `503 TRANSACTION_UNCERTAIN` 等分支；不要因为页面断网就推定数据库没有提交。

## 3. 保存以后，消息和扫描怎样接上

这不是“浏览器 → MQ → scanner”的一条流水线。**浏览器与 scanner 是两个入口**，共同使用 Runtime、业务规则和数据库；消息进程处理已经提交的 outbox。

普通项目写操作的 `Business.outbox()` 产生 `event_type=1`，payload 为 operation_id/request_id，收件人为空。它用于业务事件，不会让每次保存都产生一条用户提醒。升级提醒由 `EscalationFacade.create()` 另写 `event_type=2`，包含任务/排期/级别、标题、正文和收件人；升级记录与该 outbox 在业务主事务内保存。

| 函数 | 输入 → 输出及边界 |
| --- | --- |
| `DeliveryWorker.cycle()` | 无参数，使用注入的 store/publisher/consumer → 本轮 confirmed/fallback/retried/consumed 等计数。先短事务领取带租约的事件，事务外访问 RabbitMQ，再短事务确认/重试。 |
| `PikaBroker.publish(event)` | 数据库事件 → MQ 消息只装 event_id/schema_version/event_type，开启发布确认；成功后才能 `store.confirm()`。发布确认不等于用户已读。 |
| `consume_delivery(store, channel, method, body)` | MQ JSON 字节 → 校验引用，`store.consume()` 提交站内通知后才 ACK；数据库故障 NACK 重排，坏消息隔离。`OutboxStore._notices()` 只为 type2 建提醒并去重，type1 不建提醒。 |
| `Scanner.run(run_id=None)` | 可选扫描 UUID → `scan_runs` 持久结果；读规则快照、截止时间和按 task id 推进的分页，逐任务调用 `_execute()`，成功后记游标/计数；续扫用同一 run_id。 |
| `Scanner._execute(candidate, run_id, rules)` | 候选任务/扫描编号/规则 → 构造 `createEscalation` Call（任务版本、排期版本、规则版本），用服务 token 调同一 `Runtime.execute()`；版本冲突最多刷新重试 3 次，未达窗口则不创建。它不通过浏览器或 HTTP fetch。 |
| `EscalationFacade.create(g,c)` | 已授权服务 Call → 检查作用域/版本/窗口；按 task_id+schedule_version+level 去重，返回 event/created/task_version。状态1–5才候选；扫描不会替人把任务改成已交付。 |

APScheduler 的 `build_scheduler()` 只按规则安排同步扫描回调，`max_instances=1`；恢复进度和去重存在 MySQL，不存在定时器的内存里。[独立扫描进程入口](../../backend/t44/scheduling/__main__.py)还有文件锁；API 的多个 worker 不各启动一个扫描器。默认规则 JSON 的扫描间隔是 60 秒；临期为到期前24小时至到期时刻，超期为其后不足24小时，严重超期从24小时起。

消息不可用时，type2 可降级落站内通知；type1 重试。已发布却未完整落通知的升级也有超时恢复。**outbox 已提交、MQ 已确认、通知已落库、本人已读/已处理是不同状态。**检查证据时先说清楚自己证明的是哪一步。

## 4. 怎样检查结构、配置和边界

R001 提到 class、manager based 和参数管理。这里实际用 `Business` 组合 Projects/Tasks/Reviews/Workflow，用 Runtime 管事务流程，用 UoW 管连接生命周期，用纯函数 [decide()](../../backend/t44/domain/state_machine.py)返回不可变状态决定；`decide()` 自己不写数据库。没有因为 R001 的举例而改成另一套 manager 架构。

当前配置也各有用途：`Settings.from_env()` 读数据库 URL/会话时长，`mysql_settings()` 要求显式数据库并核对 T44_DATABASE；升级规则和评审模板是版本化 JSON；Compose 的 YAML 编排进程。先问“这个值由谁读、影响谁、是否要版本化”，再选格式。查看配置时保留脱敏，不把口令或 token 复制进作业。

人力规则已有真实 D005/D006 与 v1.1 冻结：状态1–5负责人工时受保护，6/7可移出迭代工时，7返工先补回；项目成员/开发角色保护仍包括7。**移出工时不等于移除项目成员**。同一个 `422 CAPACITY_REFERENCE_INVALID` 可能由不同操作/条件产生，前端应结合操作和表单解释，不能从当前20条可见数据猜全项目情况。

在本指南基点中，`RowsGateway.task_schedule_changes(project_id, pairs)` 已新增：限定同项目、最多100个精确(task_id,to_version)对，返回完整行；它不负责鉴权或业务匹配，也不自行 commit。Issue28 的理由投影/前端展示仍是后续候选：本指南不把新入口存在说成整条修复已通过。收到两岗的真实候选答复见 [M6 实际问答](M6-actual-qa.md)。

## 5. Git、审核、测试分别证明什么

| 看到的证据 | 可以说明什么 | 仍不能替代什么 |
| --- | --- | --- |
| 分支 / worktree | 分开工作目录和 Git 索引，避免互相覆盖；同仓库仍共享历史 | 不会自动隔离开发讨论或私密测试上下文 |
| commit SHA / push | 固定一份可比较的快照 / 把它上传到远端 | 不证明功能正确或已合入主干；文档 `[skip ci]` 提交未跑新产品 CI |
| 审核报告 | 审核人在报告指定 SHA 和范围内检查了变化 | 不等于真实运行、性能或整体验收；SHA 变化后须重新判断 |
| 开发自测与 CI | 指定版本在指定环境执行了列出的检查；覆盖率是执行范围指标 | 不等于所有需求/副作用正确，也不等于独立验收 |
| Docker 合成演练 | 指定镜像组合的进程、扫描、备份恢复等演练结果 | 不等于已租云、正式400并发负载或独立验收 |
| 独立测试 | 无开发历史实例先冻结用例，再对固定 SUT 按独立标准执行 | 用例冻结数不是通过数；修复后开发绿灯不能改写旧失败 |

本轮可引用的最近完整组合是 **8323692**：开发 CI 后端437、前端65项，Docker 合成演练绿色，详见 [精确记录](../../records/validation/composite-832-ci.json)。本指南基点已经含后续 DB reader，不能套用旧组合结果为当前全部代码背书。原正式三组 P95 为3035/1908/5506ms，均高于270ms；没有新正式通过。DB 产品3b7对应有效源码6186行，超过5100，后续修复还会增加待统计量。独立v2整体仍未完整验收；v3公开元数据为先冻结、0执行。以上状态据 [公开检查点](../../records/github/integration-pr-832-body.md)，不要把短开发诊断变成正式指标结论。

## 6. 五个小练习：全都待学生本人完成

这是建议练习，不是已完成清单。可以只读代码作答，无须启动服务或修改数据库；以后若真做断点/改码，再记录真实版本、动作和证据。

1. **找到一次请求。** 从“调整任务排期”按钮追到唯一 fetch，写下操作名、HTTP方法/路径、四个必需顶层字段；回答哪些在 params，哪些在 body。
2. **判断保存时刻。** 在 `changeTaskPlan()` 返回处与 `UoW.__exit__()`之间，标出还要发生的四类写入/校验。回答：“这里返回了 task”能否证明已 commit？
3. **区分规则与格式。** 找到 `submit(true)` 和 `business_guards_executed: False`。写一个“格式正确仍会被业务拒绝”的情形，并用真实守卫位置支撑；不要实际伪造用户操作。
4. **追一条提醒。** 画文字箭头，分别写 scanner 入口、type2 outbox、MQ 引用、通知落库、ACK；圈出数据库事务与 MQ 网络之间的边界。再解释 type1 为何没有用户提醒。
5. **评价一条通过声明。** 对照832记录，为“已push / 审核 / 开发CI / Docker / 独立验收 / P95 / 5100行”各写一句有范围的结论。指出哪些仍未达标，不把这些结论写成自己的实测。

本人填写的空表（保持空白直至有真实行动）：

| 日期 / 学生姓名 | 准确 SHA / 文件函数 | 本人实际阅读、操作或修改 | 原始观察及证据位置 | 本人判断与未解决问题 |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

若尚不能解释某一步，向总协调提出“我读到哪个函数、输入是什么、哪项输出/副作用不明白”。AI 可以继续解释；AI 回答本身仍只记 AI 问答，不计学生亲改、亲测、打断点或独立发现问题。
