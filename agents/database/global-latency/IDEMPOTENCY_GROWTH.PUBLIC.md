# 单一当前实现：64次真实claim→complete局部观察

目的仅观察现有幂等行增长/页活动，不是策略对照、性能AB或P13根因复现。使用已保存native-segments-source-459-e07快照（全部文件SHA同getmarker1.PUBLIC.json），Runtime SHA84309825b2e0a214130a0871cd493773aab07f36721dddf45311c9312e68345a；精确生产DDL SHA c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4。诊断关闭。自建全新socket-only MySQL8.4.11，RC/flush1/sync1，128MiB bufferpool、maxconnections64，不连接云或无关实例。

原DDL/最小10任务seed后，真实create_app+SqlAlchemy UoW+TestClient对同一合成任务做64次合法BLOCK/UNBLOCK，各次新幂等key；真实请求/响应完整schema校验、鉴权/lease/fence/CAS/审计/outbox/原两事务均保留。COMPLETE写入原业务完整Task+decision响应，未用{}或部分payload。没有新DDL、删除索引、改事务或额外业务writer。

只在本专用实例启用index_page_splits，确认STATUS=enabled。SQLAlchemy事件仅识别幂等表INSERT及COMPLETE UPDATE的边界，通过独立只读原生连接取计数；不保存SQL/参数/token。这些全局计数仍可混入后台动作，遥测查询也扰动执行，故不报告SQL延迟/吞吐/P95。其余业务表的写入是同一真实请求必需部分，不偷偷删除以制造结果。

|实际结果|值|
|---|---|
|幂等行|0→64，最终pending0/complete64|
|response二进制JSON总量／均值|58432B／913B（原完整业务响应）|
|PRIMARY物理size|1→7页（16KiB页）|
|PRIMARY叶页|1→6|
|uq_scope/recovery二级索引size|各仍1页|
|幂等INSERT前后split增量求和|5|
|COMPLETE UPDATE前后split增量求和|0|
|整个64请求窗口全局split增量|7，另2不能归给幂等表|
|全窗口redo_current_lsn增量|528129B，含任务/审计/outbox/幂等/提交等全部工作|

表/index占用在测量前空表和测量结束后分别ANALYZE才取得刷新统计；ANALYZE不计入语句边界delta。结束后、ANALYZE前I_S仍报告TABLE_ROWS0/DATA_LENGTH16KiB，但真实COUNT=64，不能把滞后估计当成未增长。刷新后DATA_LENGTH114688B、INDEX_LENGTH32768B、ROW_FORMAT=Dynamic；这仅说明本地实例实际格式，未现场证明P13物理row_format。

原始语句delta另含Innodb_data_written/os_log_written等，但不能视为精确单SQL redo归属：异步刷新/全局采样/后台工作可跨边界。最终server shutdown0/socket消失、drivererrors空，原Starlette/httpx兼容warning保留。原始JSON、脚本及log为idemgrowth1.PUBLIC.json、observe_idempotency_growth.py、idemgrowth1.log。

结论：完整响应同行保存确实占用clustered行空间，现有完整生命周期出现5次在INSERT边界观察到的分裂；**本次没有观察到UPDATE直接分裂，也未观察二级索引页数增长**。一种更精确候选是complete长行占满末端clustered页，使后续新claim INSERT较快需要扩页；但64行正常增长本身也会扩页，不能据此证明P13 87/56ms INSERT被split支配，更不能排除I/O/内部latch/redo等其他机制。

窄控制行＋独立完整响应表可作为后续设计方向：保scope唯一/lease/owner fencing、同主事务原子COMPLETE与完整响应、拒绝审计事务及replay原语义。它同时新增响应表INSERT/FK/页与redo，可能只是把分裂搬到另一张表、甚至增总I/O；没有策略实测或明确版本设计前不声称改进、不实施DDL、不拿{}绕过原CHECK。当前可直接落地的工作仍是保durability的资源profile纠正与已可观测的热点分段；此probe仅把存储候选说准确，不是P95修复结论。
