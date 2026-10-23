# 消息进程

冻结 v1；消息岗实现。使用已有数据库迁移与 `OutboxStore`，不会在启动时建表。部署前必须包含数据库岗的 `recover_confirmed` 原子恢复门面；缺失时进程显式失败。

配置通过环境提供 `DATABASE_URL`、与 URL 库名一致的 `T44_DATABASE`、`AMQP_URL`。凭据通过私密环境/挂载注入，不写入命令或日志。安装仓库既有锁文件后运行：

```sh
PYTHONPATH=backend python -m t44.messaging
```

`--once` 只执行一个有界批次；返回0表示该批次无已观测组件错误，2表示有 broker 错误（升级 fallback 可已提交），1表示配置/数据库等失败。批次成功不等于所有历史消息均已送达。

默认 durable direct exchange `t44.events`，queue `t44.notifications`，对应 `.quarantine` 持久死信交换机/队列。消息为持久 JSON `{event_id,schema_version,event_type}`；数据库是业务正文与收件人快照的权威。每轮最多50条，租约30秒，confirmed消费超时120秒进入数据库锁内缺失核对；轮询1秒。旧 lease_token 不可 confirm，fallback 是终态。进程使用两个独立 Pika 连接，均由当前单一线程操作。

至少一次传递，DB 唯一约束保证同 event/recipient 只有一条通知；确认丢失不等于未投递。消费事务完成才 ACK，临时持久错误 NACK 重投，永久坏消息转 quarantine。人工检查 quarantine 时仅使用已授权运维工具，不将消息重投视为新的 event。

API 工作者只装配 `NotificationFacade()`；不得从 API 多worker 启动此进程。SIGINT/SIGTERM 设置停止信号，在当前短事务/有界网络操作结束后关闭连接与引擎。

模块验证：`PYTHONPATH=backend python -m pytest backend/tests/messaging -q`；真实组件用 `-m integration`，由 CI 提供 `DATABASE_URL`、匹配 `T44_DATABASE=t44_ci` 与 `AMQP_URL`。CI 缺配置直接失败；本机没有 AMQP 配置时仅 Rabbit 用例 skip，不作为通过。

Pika官方参考：[BlockingConnection与线程限制](https://pika.github.io/pika/latest/modules/adapters/blocking/)、[1.x blocking实现及confirm/mandatory语义](https://github.com/pika/pika/blob/1.3.2/pika/adapters/blocking_connection.py)。实际依赖锁为 Pika 1.4.4；不使用新版文档中不适用1.x的跨线程 `Connection` API。
