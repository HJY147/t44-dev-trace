# 消息与通知模块报告

## 任务与范围
- 实际派工 ROLE-messaging-APPLICATION-v1 覆盖 M0 只设计限制；依据冻结 v1、D001/D004、FR-07/AC-07。
- 当前：通知 API 与独立消息进程已实现并完成真 MySQL/真实进程自测；真实 Rabbit CI 待执行。
- 产品仅 backend/t44/messaging/；测试仅 backend/tests/messaging/；未改共享依赖、DDL、其他岗实现或独立验收资料。

## 通知业务
- facade.py 的零参 NotificationFacade 对齐 API 实际 list/mark_read/handle 签名，接收现有 RowsGateway。
- 使用调用者 Runtime 的事务、身份、幂等与成功审计，不自行启动业务事务。
- 每次限制当前 recipient 与 active membership；指定项目不存在/非成员按冻结错误返回。
- 列表在当前 active membership 共享锁范围内分页，按通知 ID 降序；total 服从 read/handled 筛选，未读/未处理计数为相同本人项目范围内各自计数。
- 读与处理分别 CAS notification.version；标读保留首次 read_at，处理保存 note/evidence，不自动标读。
- 只输出冻结 Notification 字段，fallback 显式 bool；不改 task.state，也不建第二套通知数据。

## 投递、故障与进程
- broker.py 使用 Pika 1.x BlockingConnection；每个连接由单一进程线程拥有，publisher/consumer 各自连接。
- durable exchange/queue、persistent 消息、mandatory+confirm；body 只传 event_id/schema_version/event_type。
- 消费先验证 schema 与权威 DB event，OutboxStore.consume 返回（事务提交）后才手动 ACK。
- 持久错误 NACK 重投；非法/永久坏消息 reject 到持久 quarantine；ACK 丢失靠 redelivery+DB 唯一约束去重。
- worker.py 先短事务 claim pending/过期 leased，再在事务外 broker I/O，confirm 核同 lease_token。
- 升级事件发布失败用同 event/token 原子 fallback；终态不再 claim；普通 business.changed 仅 retry。
- recover_confirmed 已接 DB 1602f359 门面，120秒超时后锁内只补缺失，完整正常事件不改标；缺门面显式失败。
- __main__.py 独立进程读取 DATABASE_URL+匹配 T44_DATABASE+AMQP_URL；不在 API worker 启动。
- publisher 空闲连接维护心跳，失效 channel 关闭重建；SIGINT/SIGTERM 优雅停止并关闭连接与 engine；--once 有 broker 错误返回2；异常只输出脱敏分类。
- 传递语义是至少一次，业务唯一由 DB UNIQUE(event_id,recipient_id) 保证，不承诺 exactly-once。

## 实际验证
- 独立 venv 从既有 lock 同步，Pika 1.4.4；Ruff 通过，CLI --help 已运行。
- 首次真 MySQL 7 错误来自本岗 capacity=[] 合成夹具，保留 mysql-run1-failure.txt 摘录；仅修合法数据后通过。
- module-run11.log：28 通过、3 本地真 Rabbit 跳过；17 基础/SQLite/fake/配置，11 真实 MySQL。
- 真 MySQL 覆盖通知权限、分页计数、CAS、read/handled、HTTP 幂等、并发仅一次更新及撤权与读范围线性化。
- fake 通道覆盖 confirm/ACK 错误与 ACK 提交顺序；DB 覆盖重复/重启/fallback 同 event 不二提醒。
- 真实 Rabbit 测试包含 mandatory return、连接关闭 redelivery、重复、恢复及 DLQ；CI 缺配置直接 fail。
- coverage-run9.log：消息模块语句覆盖84%，不是全后端或全产品覆盖率；首轮85%保留为当时事实。
- b5a16e6 的3项真实 Rabbit 已在两次托管CI实际通过，见ci/AUDIT.md；整run因BE旧fixture/FE脚本失败，当前后续快照须新CI，独立验收/性能未验证。

## 对接与记录
- DB Issue4 问询 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6360793043。
- DB已接受精确 recover_confirmed(confirmed_before,now,limit) 并交付1602f359，默认真实门面接线验证通过。
- 实际进程+MySQL+真实TCP拒绝已验证fallback与SIGTERM；runtime-process-run8.log，未越权改 persistence。
- 调度确认升级事件/ledger/recipients 快照，消费者不信 broker 中的接收人或级别。
- API 导入自动获得 NotificationFacade；错误统一 services.errors.Rejected，成功审计交 Runtime。
- 日志 agents/messaging/WORKLOG.md；handoff records/handoffs/messaging.json。
- 实际提示词 ROLE-messaging-APPLICATION-v1；摘记 agents/messaging/prompts/ROLE-messaging-APPLICATION-v1.md。
- 未发生用户亲自改码/人工审定，不制造人工修改或幻觉纠正记录。
- 既有 contracts 开发回归25通过/1失败/1跳过：依赖缺失用例未显式移除现已实现的通知门面，实际200；原失败 api-regression-run1.log 已上报根，请BE修夹具，本岗未改外岗断言。
- 首阶段SHA b5a16e6、draft PR20已推送并attach；当前规模由根实测超范围，未宣称达标。
- run10批次夹具假设失败已保留；只修测试容量并新增本次retry尝试断言，run11复跑通过，不改生产batch或清理共享数据。


## 2026-10-25 结构规模候选
- 基线396b646，独立codex/messaging-size-20261025；提示词ROLE-messaging-SIZE-20261025-v1。
- 先设计再计数：agents/messaging/tmp806_newscope/DESIGN.md；固定cloc2.10基线5875，其中消息357。
- 共用通知active membership锁/范围与既有page，Broker网络错误清理/脱敏单点维护；错误分类、权限/CAS、ACK/NACK/DLQ与恢复不变。
- 保持原展开风格，未移出生产目录、不动DDL/OpenAPI/门禁/调度；初步diff仅净11行，未承诺100。最终cloc与SHA见后续RESULT。
- 新22项性质/故障用例在原基线通过；当前现有+新增39项通过，23个integration不运行，不读凭据、不跑云/独立验收。原0收集和ruff失败保留。
- 跨岗候选（调度event投影、scan_run事务内原语、outbox信封工厂）已交根排班，不自行落新sharedhelper。
- 提交快照c4b3f114固定cloc净减13（application5875→5862，消息357→344）；只Facade-10/Broker-3，其他application不变。设计预算15–50未兑现上界，未达到100，未隐瞒总量仍超762。
- 代码已stage push；Issue5实际评论6397897311。完整before/after、性质/故障和原始失败见tmp806_newscope/RESULT.md；不包含全CI或真实组件结论。
# 2026-10-28 通知 Call/CAS 候选

已审A后半由messaging AI实际实现，产品6977e5b7、上游backend2d947d23；只改通知facade。list/mark_read/handle内部统一(g,c)，值构造前先核版本，复用cas(record_diff=False)保持成功审计before/after为空且Runtime.audit仍执行；项目资格/收件人/SQL锁/UoW/handle不隐式read保持。REST/DDL不变，旧平铺Python是明确迁移，产品没有兼容壳。

原979/806函数与36assert AST完全同，仅test-only调用适配；新780直接7边界先7签名红、后7绿。联合模块60pass/23integration未执行，API164pass/40未执行，并集203而非224；Ruff首次I001修后绿。固定cloc：5935→5916→5898，消息85→67净18、合包37，仍超798/exit1。实际原件见agents/messaging/component-call-20261028/，不冒原生MySQL/Rabbit/完整CI/独立/正式性能通过；780需根接入CI，云候选仍5d。
