# P13真实SQL热点及写路径证据

来源仅为已发布PUBLIC两窗口：early17:31–17:32Z、late17:37–17:38Z；各12样本、64.808/63.621秒。不是P12。原文件SHA分别41169ef083fd531c5bfdf2d21a30acabba37d3bc42896dafda52d4df0eb25800、0d009738b45c167458fb77f781936d427cfda23b74de45bc9605db9606fc4084。24行所需原计数另保P13_SELECTED_COUNTERS.PUBLIC.json，离线计算程序aggregate_p13_io.py与完整结果P13_IO_DELTAS.PUBLIC.json可复核。未访问生产、PRIVATE或新压力实例。

## 已确认而非猜测的热点

observer原文件manual13-observe.py SHA67cb55f1d958f2245de464518dcfb6bf545e0755f99ca913f488c490f2a13c45，第71行选DIGEST，第373行直接lower，没有再次hash。自有短寿socket MySQL8.4.11以STATEMENT_DIGEST直接计算受信SQL控制语句，COMMIT严格匹配f2b9be5f...，ROLLBACK匹配3e67fa...。为确认最大热点，再在同类自有实例用3个当前代码合成HTTP请求在内存捕获SQLAlchemy/PyMySQL渲染结构，调用STATEMENT_DIGEST，最终只发布操作类别及hash，没有SQL文本、参数、用户资料或真实生产查询。

|P13类别|early调用数／平均ms／并行累计秒|late调用数／平均ms／并行累计秒|
|---|---|---|
|INSERT/idempotency_requests，78ceeee04e3c5f9d92f1e2375cb142031ccd5252a477e2b768ebad7d110cf45c|45092 / 87.311 / 3937.036|39987 / 56.253 / 2249.388|
|COMMIT，f2b9be5f0f32ca7507e4ddf133cd2fad0993a1c26fde9caa6f067b1af2b7603c|139917 / 8.635 / 1208.172|124361 / 8.639 / 1074.333|

该INSERT分别占全DIGEST_TOTAL.sum_timer_wait增量55.52%/47.23%。这是被测DB语句计时的突出热点，**并行累计秒/占比不是HTTP耗时占比，均值不是P95，不能把两窗口当完整600秒**。匹配范围是当前3个路径执行过的相同SQL结构；其他hash未知就保持未知。映射raw与脚本为digestmap1.PUBLIC.json/map_p13_digest.py、digestshapes1.PUBLIC.json/map_p13_shapes.py，两自建实例finally shutdown0/socket消失，durability1/1。后者3个请求仅为语句结构定位，不测性能。

## 写路径与配置的实际证据

- redo容量实104857600字节=100MiB，LSN生成3.237/2.929MB/s，名义容量仅32.4/35.8秒当前redo量；checkpoint age实18.2–38.6/17.2–35.1MB，即容量17–37%/16–33%，**没有观测到逼满或log-space停顿**。
- 每秒flush1639/1667页，数据文件写33.65/33.39MB/s，os_log_written5.13/4.54MB/s；host块层另约66MB/s。这些不同层/不同含义计数不可相加，页写/redo比也不能直接当物理写放大系数。
- dblwr文件等待事件每窗1099/1037次，总121.36/122.42并行秒，均110.43/118.05ms；data-file均1.008/1.232ms，redo-file均0.125/0.152ms，binlog均0.633/0.729ms。不同文件事件可能并行/重叠，不能相加得到请求延迟或用生命周期max当本窗口P95。FILE_IO写事件总体均值0.504/0.627ms会掩盖dblwr大批次事件。
- bufferpool8GiB中87–94%页仍free，物理读仅2.8/4.5次每秒，buffer_wait_free增量0，不支持当前主要是读缓存不够。盲目把128GiB主机内存全给DB不会直接修复这些写热点。
- 行锁wait增量7/5、time103/23ms，相对INSERT累计耗时很小，削弱普通InnoDB行锁是全部主因的解释；不排除未采到瞬时锁、元数据锁/索引latch/redo内部mutex。115种选定wait instrument仅9已enabled+timed，未启用的0不能当无等待。
- Innodb_log_waits增量0是已记录计数事实，不能扩大解释为全部redo/log-space/checkpoint等待不存在。观察的是离散全局计数，缺逐请求与wait stage因果链。
- Threads_connected248–249/279–280低于max384，不能因此排除某worker自己的5连接池排队；configured64workers、pool5+overflow0为本轮实采。后台IO压力、连接持有与进程内调度可共同把只读拖慢，后半链尚未证实。

## 可以交部署岗实施的保durability调优候选

这是针对**APP唯一40GiB、用户提供PL1额定3800IOPS盘**的显式资源profile，非通用默认、非已测P95修复。MySQL实io_capacity10000/max20000与该资源预算不匹配；MySQL官方说明应按系统近似可用IOPS而设置，并提示过高会过早刷出缓存。redo100MiB与当前redo速率也缺乏平滑余量。可以先修配置，不能直接承诺消除87ms INSERT热点。

```ini
innodb_redo_log_capacity=2147483648
innodb_io_capacity=1000
innodb_io_capacity_max=2000
innodb_flush_log_at_trx_commit=1
sync_binlog=1
```

保持doublewrite保护、binlog和现有数据卷；不关闭flush_sync、降低持久性、删redo文件或改bufferpool实例/页大小。io_capacity不是磁盘硬限流，默认flush_sync在checkpoint burst时可越过这些值，不能称2000已保证foreground剩1800IOPS。2GiB以当前redo速率约11分钟名义空间，只是减少过早checkpoint/热页重复落盘的候选，不能证明32秒默认一定导致实测延迟。

执行前由部署岗核当前物理盘/共享IOPS/吞吐、原参数与命令行优先级、磁盘余量（至少新增redo约2GiB外再留镜像、备份、binlog和运行余量）、无其它测试或迁移、保留回滚参数。先持久化明确profile，再按已选启动/动态接口实施；动态resize后实际读取Innodb_redo_log_resize_status=OK和Innodb_redo_log_capacity_resized=2147483648，所有durability值保持1。不要手工删除#innodb_redo，不把SET GLOBAL当已持久。容量增大可能延长崩溃恢复；不能为缩回100MiB强行等或破坏数据，回滚须有明确resize空间/时窗。该岗没有修改deployment目录或执行这些命令。

## 幂等存储结构的工程候选，尚不实施DDL

schema.sql中idempotency_requests为顺序AUTO_INCREMENT主键、uq(actor_kind,actor_id,operation_id,idempotency_key)、ix_idempotency_recovery(status,lease_until,id)，含JSON response_body；CHECK要求pending response_body=NULL，COMPLETE必须非NULL且完整状态/response_request_id/completed_at。claim INSERT小行(status1)后main COMPLETE将完整成功或拒绝业务响应写回同一行(status2)，导致行增长和recovery二级索引状态移动，这是可审查的写放大/热页候选，**不是已证明87ms内部原因**。

对当前backend/t44所有Python搜索，idempotency访问仅runtime.py：uqscope查、主键owner fence/get/update、主键CAS complete；未找到按status/lease扫描的生产查询。ix_idempotency_recovery当前没有明确查询调用方，值得审索引维护成本，但不能据此直接DROP：冻结DDL/未来恢复语义及实际EXPLAIN/索引使用必须先评审，再明确版本迁移。

另一条后续提案是窄控制行+独立完整响应存储：控制行保持唯一scope、request_hash、状态、lease与owner fencing；完整响应与控制行COMPLETE在同一个main事务原子提交；replay先按原key/授权锁定再完整回读响应，拒绝独立audit+COMPLETE事务语义和4xx优先级保持。需要显式schema/CHECK/FK/迁移设计，不能偷偷将response_body改成{}、删payload校验或只缓存部分response；不能放松原claim跨事务所有权或复活已拒INSERT-first。这只是在确认热点后的下一工程提案，当前无DDL/业务改动。

## 官方依据

[Redo优化](https://dev.mysql.com/doc/refman/8.4/en/optimizing-innodb-logging.html)：小redo可造成不必要写入；[I/O容量](https://dev.mysql.com/doc/refman/8.4/en/innodb-configuring-io-capacity.html)：按资源调值及flush_sync例外；[STATEMENT_DIGEST](https://dev.mysql.com/doc/refman/8.4/en/encryption-functions.html)：同一解析器规范化hash；[binarylog耐久性](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html)：sync_binlog1与flush1保护。文献解释机制，不替代本项目因果测量。
