# Direct16 数据库离线复核（非追加压测）

结论：Direct16 已发布的四类稳态 P95 均满足原 ≤270ms 门槛，128989 次稳态请求零错误；原后置快照 243/400、完整审计 227/400 未完成，独立整体结论仍为 NP。P13 的幂等 INSERT 数十毫秒平均热点在 Direct16 两段观察中没有重现。没有理由根据旧热点立即修改 DDL、删除恢复索引、减少完整响应缓存或降低持久性。

## 输入、可复核边界

只读 Git `3d6f7eab` 的已发布 PUBLIC 文件；未访问 PRIVATE、数据库、SSH、云或 SUT，也未启动实例。原应用产品源为 P16 `bcec`、P13 `90b`，不是同一源/同一负载的单变量对照。原 digest 映射证据见本目录 `P13_IO_FINDINGS.md`、`digestshapes1.PUBLIC.json`：SQL 结构由自有合成请求取得、原生 MySQL STATEMENT_DIGEST 映射，78ceeee…=INSERT/idempotency_requests，f2b9be5…=COMMIT；本次直接复用准确 hash，不重新生成生产 SQL。

`aggregate_direct16.py` 只通过 `git show` 读取准确 ref 的 PUBLIC 字节；断言各窗口 12 样本、Uptime 单调、配置不变、各累计计数不下降、目标 digest 每个样本都在 top20。生成 `DIRECT16_DATABASE_DELTAS.PUBLIC.json` 和原运行日志 `direct16-aggregate.log`。计数差使用窗口首末，覆盖约 62 秒；不是完整十分钟总计，也不是 12 个独立压测。

|窗口|UTC（2026-10-31）|秒|原 JSONL SHA256|
|---|---|---:|---|
|early|09:30:51.093023–09:31:53.326565|62.233547621|3a0b0620a5eb8dbe8ac65fb397408e6caffb58e0996d1f5aff95a333c970cea5|
|late|09:38:52.015621–09:39:54.274566|62.258953711|6518fef080d4f12dc18a5dc4b7ab9a767e11dd29e33c180927e00a71c87bb931|

原路径为 `agents/coordinator/direct-p16/actual-run-20261031/{early,late}.PUBLIC.jsonl`；全 SHA、字节数和独立 SUMMARY/DIAGNOSTICS 输入 SHA 均在生成 JSON。P13 对照仍来自原已核 24 样本，准确时间、原 SHA 和增量见 `P13_IO_DELTAS.PUBLIC.json`，不混入 P12。

## 精确 digest 增量

|指标|P13 early|P13 late|P16 early|P16 late|
|---|---:|---:|---:|---:|
|INSERT 调用数|45092|39987|8279|11244|
|INSERT calls/s|695.78|628.52|133.031143|180.600529|
|INSERT mean ms|87.311|56.253|0.078092422|0.076507401|
|INSERT 累计并行 SQL 秒|3937.036|2249.388|0.646527158|0.860249214|
|INSERT 占所有 digest 计时比例|55.52%|47.23%|2.1980%|2.1869%|
|COMMIT 调用数|139917|124361|30101|38799|
|COMMIT calls/s|2158.95|1954.71|483.678035|623.187472|
|COMMIT mean ms|8.635|8.639|0.415502265|0.464841602|
|COMMIT 累计并行 SQL 秒|1208.172|1074.333|12.507033670|18.035389312|

P13 的调用速率也是 digest 计数差除以其原窗口秒数，并非 HTTP 吞吐。P16 COMMIT 现在占累计 digest 计时约 42.52%/45.85%，这是在总 SQL 时间大幅下降后的相对比例，不能因占比升高就认定 COMMIT 成为新的尾延迟瓶颈。均值不是 P95；累计并行 SQL 时间不是可相加的 HTTP 时间或请求占比。

## 刷盘、redo 与锁观察

P16 两窗口配置固定：redo 2147483648B、io_capacity 1000/max2000、buffer_pool 8589934592B/16 instances、flush_log_at_trx_commit=1、sync_binlog=1；不把 1/1 保留误写成性能换持久性。doublewrite 保留来自原发布运行配置，当前 observer 的 effective_global_config 本身没有该字段，故不伪称由这 24 条单独再次核定。

|窗口增量或范围|P16 early|P16 late|
|---|---:|---:|
|current LSN bytes/s|637698.259|834141.098|
|Innodb_os_log_written bytes/s|1029412.631|1326526.629|
|Innodb_data_written bytes/s|2297739.490|3569199.975|
|pages flushed/s|46.277|97.143|
|row lock waits / time ms|0 / 0|0 / 0|
|log_waits / buffer_pool_wait_free|0 / 0|0 / 0|
|checkpoint age bytes range|83341377–119395773|242721153–251983707|
|checkpoint / 2GiB capacity|3.881%–5.560%|11.303%–11.734%|
|buffer free pages fraction|95.438%–95.844%|93.362%–93.608%|
|Threads_connected|231|231|
|dblwr file event mean ms|0.609156|1.002193|
|redo file event mean ms|0.052252|0.051718|
|binlog file event mean ms|0.189066|0.185274|

P13 对照：redo 100MiB/io10000/max20000、LSN 3.237/2.929MB/s、pages flushed 1639/1667/s、Innodb_data_written 33.65/33.39MB/s、dblwr event mean110.43/118.05ms。P16 的刷新与 dblwr 等待显著较低，但同时写入调用率、业务源、连接复用/测量路径等有差别；不能把全部改善归因于扩大 redo 或 io 参数，也不能从旧 rowlock 小就排除当时所有内部 latch。0 等待增量不能排除离散采样未分解的瞬态锁。

P16 host nvme0n1（259:0）原生完成计数：early 写16.188MB/s、完成2014.34/s；late 写22.376MB/s、完成2710.34/s。是整机 Linux block 层 counters，不是云盘计费 IOPS、单一 MySQL 写放大倍率或真实设备饱和率；不同层计数不可直接相加。`Innodb_data_written` 也只按原 counter 名解释，不强行归到一个物理文件。

## 64 核与 HTTP 分段

基于同窗口 API cgroup cpu.stat usage_usec 差，API 平均2.2470/2.2842核、MySQL平均0.4061/0.5138核；单位为 CPU 秒/采样墙秒，采集服务的时点与顶层时间有小偏移，这是约62秒平均，不能称峰值或推算所有核心瞬时闲忙。两窗口 throttled_usec/nr_throttled 增量0，没有观察到该 cgroup quota 限流。

原进程采集器只识别到 configured_workers=64 的 supervisor，未识别实际 worker，故 worker 数 UNKNOWN；不是实际0 worker。独立 HTTP 原 raw 有18个响应 PID，不能解释成只启动18个进程，也不能证明已充分利用64核。当前采样负载下，CPU没有接近64核；低CPU本身既不证明算法差，也不证明提高worker数有收益。已发布稳态约215 req/s的需求完成量应与潜在更高吞吐上限分开。

独立 DIAGNOSTICS 覆盖128989稳态请求且全部 diag-incomplete=0。app P95=32.080ms，逐请求 E2E−app P95=88.951085ms（配对差，非两个P95相减）；db.execute_fetch.wall 的每请求聚合 P95=20.226ms、CPU P95=7.385ms；db.acquire.wall P95=2.172ms、db.commit.wall P95=3.128ms。不同分布的P95不可相加。acquire 每次 gateway 调用均可被计数，均值17.798次/请求，不是每请求17.798次实际新连接/checkout；span 含既有连接返回、建连/preping/隔离设置及调度，不能直接当 pool queue 等待。execute_fetch 包含网络、服务端执行/等待、Python fetch/解码与调度，不能直接当 SQL 锁时间。

这些分段支持：本轮 app 内部与数据库访问已在较低量级，旧 INSERT 热点不是当前已证主要尾因。E2E−app 的具体组成（同步worker进入前排队、网络/TLS、客户端等）缺少进一步边界证据，不能直接归因 Nginx 或线程池。

## 验收与下一步边界

四类 P95 精确值分别57.388297/77.296637/99.256754/81.441719ms，稳态128989零错误；全程并非零错误。16个已发布错误均在后置 audit-events GET，集中原40秒后置截止；原独立时间线支持验证池截止及随后集中关闭连接的候选解释，缺少逐调用栈，不能删除这些错误或宣称后置已完成。消息实际送达及被豁免的完整原准入门禁也未验证。

先由 QA 工具 owner 在本地修正后置验证/停止生命周期，保留原断言与失败证据；数据库岗本次不修改应用、规格、DDL、SUT参数，不建议额外付费AB或再开服务器。若未来仍需追查数据库尾部，应使用准确请求配对分段及服务端指标，不能只凭旧P13平均值实施大迁移。
