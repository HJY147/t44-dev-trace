# tmp806_newscope：先设计，后计数

阶段：2026-10-25 消息模块真实结构去重；操作者 AI messaging。
基线：396b646adb87de183929ac6fc46bbe7e88074c8a。
本文件在首次 cloc/逐文件数量实测之前写入；下列是结构估计，不是已实现收益。
只允许消息产品目录与本岗记录、新开发用例；调度只读；共享 helper 须经 root 确认。

## 静态调用图与不变量

- HTTP → Business.listMyNotifications/markNotificationRead/handleNotification → NotificationFacade → RowsGateway；Runtime 持有鉴权、请求幂等、成功/拒绝事务和审计。
- NotificationFacade.list → membership share锁 → 当前project/recipient过滤 → 分页与三种count；写路径 → membership share锁 → notification update锁 → version CAS。read 与 handled 分离，不写 task。
- 消息CLI → Settings/MySQL engine/UoW/OutboxStore → DeliveryWorker；Worker先confirmed原子恢复，再claim短事务，事务外Pika IO，owner-token confirm/fallback/retry；consumer DB提交后ACK，毒消息reject到DLQ。
- Broker的connect/publish/get/keepalive均把AMQP/OSError转换为无凭据BrokerUnavailable并清理连接；connect额外接收ValueError。close自身清理失败被吞，不能递归调用同一错误包装。
- 调度CLI → Runtime/Business/EscalationFacade + Scanner + APScheduler；Scanner不直接投MQ；EscalationFacade在调用事务中写outbox/ledger/task CAS。不存在可删除的“重复发布者”。
- 调度ScanStore.start与EscalationFacade._run均维护scan_run字段，但一个自己UoW、另一个事务内gateway；不能为了少行直接互调破坏原子性。

## 可执行候选与结构预算（尚未实测）

1. Broker操作边界：一个小contextmanager收口四处同形的异常清理/脱敏，保留各操作分类、connect额外ValueError、False-NACK和close的特殊处理。估计净减5–15；不把几行try改成单行。
2. NotificationFacade：优先复用既有page/序列化函数，统一“本人项目集合”查询和计数构造，保持membership锁、项目不存在/拒绝语义和排序。估计净减10–25；若复用需要修改共享page，则先向root提案，不越权。
3. Worker/main：梳理资源所有权和每事件发布结果，只有确有重复才能收口；不能仅把循环拆成更多helper或靠**kwargs隐藏签名。估计净减0–15。
4. 传输事件三个固定字段共用声明，减少生产与验证协议字段重复，须保留精确字段集/整数排bool/authority复核。估计净减0–10，抽象成本大于重复则放弃。

本岗独立可维护净减的可信预算是15–50，不先承诺100–200。现有模块已复用DB门面和通用model，硬凑100很可能变成格式压缩/动态分派。

## 需root排调度/数据库配合的候选（本轮不实现）

- 复用既有model进行EscalationEvent投影，替代调度event()手工列同名字段，预计5–15；不动disposition优先级与handled_count。
- 将ScanStore.start和EscalationFacade._run的“同gateway创建/查重run”整理为数据库拥有的事务内原语，再由两个所有者在各自事务内使用，预计合并净减25–50。须保留duplicate savepoint、原始rule_hash/版本、UoW归属。
- Messaging/scheduling CLI的engine资源构造/释放有重复，但鉴权/tokenfile/进程锁/停止语义不同；只有root确认共享基础设施责任目录后才做，预算净5–15。两进程不可合并。

## 测量与回归计划

- 固定cloc2.10工具SHA先核对，仅访问root指定的该工具，不读其他runtime或凭据。
- 基线从已提交396b646归档；候选/完成版本沿完全相同application路径集合计数，测试/元数据单列，绝不迁出生产目录或修改计数脚本。
- 基线与候选运行本模块开发用例，不读任何独立材料、不跑全CI/云/正式验收；真实外部组件未运行即标未运行。
- 新用例重点比较异常分类与清理、connect失败不覆盖原始脱敏码、ACK/NACK/DLQ顺序、身份范围/CAS/read-handled、恢复与过期租约；原失败日志保留。
- 每个候选保存before/after、删除/新增结构原因、测试命令及结果；低于100直接实报，不改门禁。
