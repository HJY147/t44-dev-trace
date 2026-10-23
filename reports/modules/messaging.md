# 消息与通知模块报告

## 任务与范围
- 实际派工 ROLE-messaging-APPLICATION-v1 覆盖 M0 只设计限制；依据冻结 v1、D001/D004、FR-07/AC-07。
- 当前：通知 API 业务与持久投递逻辑已实现；完整进程待 DB confirmed 恢复门面及真实 Rabbit CI 验证。
- 产品仅 backend/t44/messaging/；测试仅 backend/tests/messaging/；未改共享依赖、DDL、其他岗实现或独立验收资料。

## 通知业务
- facade.py 的零参 NotificationFacade 对齐 API 实际 list/mark_read/handle 签名，接收现有 RowsGateway。
- 使用调用者 Runtime 的事务、身份、幂等与成功审计，不自行启动业务事务。
- 每次限制当前 recipient 与 active membership；指定项目不存在/非成员按冻结错误返回。
- 列表分页按通知 ID 降序；total 服从 read/handled 筛选，未读/未处理计数为相同本人项目范围内各自计数。
- 读与处理分别 CAS notification.version；标读保留首次 read_at，处理保存 note/evidence，不自动标读。
- 只输出冻结 Notification 字段，fallback 显式 bool；不改 task.state，也不建第二套通知数据。

## 投递、故障与进程
- broker.py 使用 Pika 1.x BlockingConnection；每个连接由单一进程线程拥有，publisher/consumer 各自连接。
- durable exchange/queue、persistent 消息、mandatory+confirm；body 只传 event_id/schema_version/event_type。
- 消费先验证 schema 与权威 DB event，OutboxStore.consume 返回（事务提交）后才手动 ACK。
- 持久错误 NACK 重投；非法/永久坏消息 reject 到持久 quarantine；ACK 丢失靠 redelivery+DB 唯一约束去重。
- worker.py 先短事务 claim pending/过期 leased，再在事务外 broker I/O，confirm 核同 lease_token。
- 升级事件发布失败用同 event/token 原子 fallback；终态不再 claim；普通 business.changed 仅 retry。
- recover_confirmed 注入点待数据库提供；无门面会显式失败，不以事务外预查代替锁内原子恢复。
- __main__.py 独立进程读取 DATABASE_URL+匹配 T44_DATABASE+AMQP_URL；不在 API worker 启动。
- SIGINT/SIGTERM 优雅停止并关闭连接与 engine；--once 有 broker 错误返回2；异常只输出脱敏分类。
- 传递语义是至少一次，业务唯一由 DB UNIQUE(event_id,recipient_id) 保证，不承诺 exactly-once。

## 实际验证
- 独立 venv 从既有 lock 同步，Pika 1.4.4；Ruff 通过，CLI --help 已运行。
- 首次真 MySQL 7 错误来自本岗 capacity=[] 合成夹具，保留 mysql-run1-failure.txt 摘录；仅修合法数据后通过。
- module-run4.log：24 通过、3 本地真 Rabbit 跳过；16 基础/SQLite/fake/配置，8 真实 MySQL。
- 真 MySQL 覆盖通知权限、分页计数、CAS、read/handled、实际 HTTP 幂等及并发仅一次更新。
- fake 通道覆盖 confirm/ACK 错误与 ACK 提交顺序；DB 覆盖重复/重启/fallback 同 event 不二提醒。
- 真实 Rabbit 测试包含 mandatory return、连接关闭 redelivery、重复、恢复及 DLQ；CI 缺配置直接 fail。
- coverage-run4.log：消息模块语句覆盖85%，不是全后端或全产品覆盖率。
- 未执行真实 Rabbit、托管 CI、独立验收或正式性能测量，不能引用本模块自测冒充。

## 对接与记录
- DB Issue4 问询 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6360793043。
- 期望 recover_confirmed(confirmed_before,now,limit) 返回实际 fallback 列表，锁内核缺失收件人且正常消费不改标。
- 根已确认 DB 后续补门面；本岗只注入/测试边界，未越权改 persistence。
- 调度确认升级事件/ledger/recipients 快照，消费者不信 broker 中的接收人或级别。
- API 导入自动获得 NotificationFacade；错误统一 services.errors.Rejected，成功审计交 Runtime。
- 日志 agents/messaging/WORKLOG.md；handoff records/handoffs/messaging.json。
- 实际提示词 ROLE-messaging-APPLICATION-v1；摘记 agents/messaging/prompts/ROLE-messaging-APPLICATION-v1.md。
- 未发生用户亲自改码/人工审定，不制造人工修改或幻觉纠正记录。
- 既有 contracts 开发回归25通过/1失败/1跳过：依赖缺失用例未显式移除现已实现的通知门面，实际200；原失败 api-regression-run1.log 已上报根，请BE修夹具，本岗未改外岗断言。
