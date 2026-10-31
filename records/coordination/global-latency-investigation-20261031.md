# 全局延迟排查：证据、修正与未证因果

用户要求先暂停文档，从第一性原理及网上/GitHub同类项目出发定位根本原因，再做全局代码修正。操作者为AI；本记录是实际工程留痕，不是学生本人研究报告。本轮服务器保持关闭，没有SSH、云变更、SUT压测或自动关机。

## 第一性原理与计时边界

端到端时间包含客户端、网络/代理、进入handler前的接收与调度、handler内部、响应编码及发送。线程CPU是handler墙时的一部分；墙时超过线程CPU可能是socket、连接获取、DB锁/I/O、GIL或OS调度，不能直接叫作数据库锁等待。嵌套span与DB累计计时均不能简单相加，更不能把两个独立P95相减。

现有source90b的api.py中，Server-Timing app从同步handler线程内开始，至响应schema检查之后、JSONResponse编码之前。历史p12已公布482100个逐请求配对：query appP95=957.313ms，contract=940.286ms，同exchange的E2E减app差值P95分别61.943/65.634ms。这削弱了“绝大部分发生在代理或进入线程前”的解释，不能替代p13，也不能细分handler内部等待。

## P13已经确认的热点

原PUBLIC早晚各12行样本来自.runtime/p13-app07-live-20261031，UTC17:31–17:32及17:37–17:38；不能与manual13-live目录内UTC14时段的p12混用。原件SHA、24行非SQL投影、可重算增量及MySQL本地语句摘要匹配在agents/database/global-latency/P13_IO_FINDINGS.md及配套PUBLIC文件。

- `INSERT/idempotency_requests`摘要78ceeee04…经自有MySQL8.4.11 STATEMENT_DIGEST精确匹配。两个窗口平均87.31/56.25ms，占窗口语句累计计时55.52%/47.23%。这是DB端真实热点，不是HTTP时间占比，不是P95，也不是COMMIT。
- COMMIT摘要另行精确匹配，平均约8.64ms。行锁累计只增加103/23ms、7/5次，削弱普通行锁为主要解释，但不排除采样间瞬时锁、内部latch或I/O。
- 实际buffer pool8GiB且大量空闲，buffer_wait_free/log_waits不增；redo仅100MiB，名义约32–36秒redo量，checkpoint age采样16–37%，没有“容量已满”的证据。
- io_capacity10000/max20000；doublewrite文件事件平均约110/118ms。文件事件均值不是设备单次延迟或请求P95，也不能仅凭额定IOPS认定磁盘饱和。
- API采到pool5/overflow0及supervisor configured_workers64；未采到64个活worker各自处理分布，不能把配置当实用核数。API无CPU限流，低CPU不能单独定位原因。

最有根据的待验证链条是：幂等INSERT/写入压力→持有连接与共享资源→其他请求排队。小redo、后台刷盘过快、幂等行从小claim扩展为大JSON及索引维护是候选机制；没有把其中任何一项冒称唯一根因。未删除恢复索引、拆表或以空JSON绕过完整响应约束。

## 参考的一级资料

- [FastAPI官方full-stack模板请求Session](https://github.com/fastapi/full-stack-fastapi-template/blob/f4bcfaba7c85be3c6332cc74a20819f586dcdbc6/backend/app/api/deps.py)及[CRUD路由](https://github.com/fastapi/full-stack-fastapi-template/blob/f4bcfaba7c85be3c6332cc74a20819f586dcdbc6/backend/app/api/routes/items.py)：对照其同步路由与请求级Session；没有复制JWT替代本项目实时撤销，也不把PostgreSQL模板性能当MySQL基准。
- [Starlette线程池](https://www.starlette.io/threadpool/)：40 token是单进程默认限制，不是整台64CPU共享40；增加线程不是根因证明。
- [SQLAlchemy2.1连接池](https://docs.sqlalchemy.org/en/21/core/pooling.html)：保留pre-ping及rollback资源清理；checkout事件发生于获取之后，不能单靠该事件测池等待。
- [MySQL8.4 redo](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)、[I/O容量](https://dev.mysql.com/doc/refman/8.4/en/innodb-configuring-io-capacity.html)和[刷脏页](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool-flushing.html)：据实际负载准备调优候选，不能靠放松持久性获得成绩。

## 本轮实际修正

1. GET合并为一个RC UoW，保留authenticate→validate→再次实时authenticate→dispatch的顺序。SELECT仍9次，checkout/commit从2次到1次。真实MySQL中validate期间撤销、成员停用、自然过期及输入错误优先四项通过。连接持有至validate结束的成本仍需实际负载观察；contract原来就是单UoW，不能据此解释其全部尾延迟。
2. 默认关闭的请求/数据库分段：wall、线程CPU、连接获取、SQL执行/取数、commit/rollback/close及实际worker PID。仅调试时数值PID是明确授权的操作标识例外，没有用户/project/session/SQL/参数/token。默认off不额外读时钟/PID；诊断故障不改变成功提交或原业务异常；上下文必清理。2048字符/64指标上限及incomplete标记防止把缺数据当0。请求始终全部计入性能指标，诊断缺项只能影响归因，不能剔除慢请求。
3. 可关闭双hop代理诊断：保留原日志列，白名单响应UUID相关1/256采样，只加固定耗时数字/字符串，不记录URL、凭据、整Server-Timing。默认配置不变；官方固定Nginx两hop语法检查通过，首轮fixture失败保留。
4. PL1候选profile入口默认只plan，目标redo2GiB/io_capacity1000/max2000，仅三变量SET PERSIST；保留flush1/sync_binlog1/doublewrite和其余保护。先核原owned DB/image/volume、真实空间与新计划，再由root绑定实际事实执行；partial、resize pending及恢复流程明确。没有实际运行SQL或宣称收益。

## 验证及限制

15个本地顺序SQLite样本不复现940ms。自有socket-only MySQL的17个HTTP/ASGI检查、2个人工等待校准和3个新marker请求通过，所有自建实例关闭。50ms人工持池落在acquire，人工SQL等待落在execute_fetch，证明诊断可区分这两类人工等待，不证明生产根因。本地定制socket pool32、非TCP/TLS/代理、数据量很小，不能外推服务器或正式P95。

初稿诊断的clock/finally异常会泄漏上下文或将成功commit误报uncertain，源级审核真实复现后修正；原记录保留。新7+5项公共回归已进入CI实际发现目录，而非只留owner脚本。当前准确整合fullCI及覆盖证据另行收口。

固定cloc2.10在源4ff25f79计量：应用66文件5993有效行，三个辅助文件仍780行，用户采用核心口径63文件5213行；两口径均超过5100。调查诊断增量真实计入，不藏代码或改统计口径；此调查分支不是最终规模通过版本，定因后仍需精简/复核。

旧p14工具包准确绑定13ac，仅作历史准备，不能用于冒充本分支新源码/镜像或复用旧grant。下一步现场采样与验收须绑定最终精确源和实际配置；本轮不编造新压测结果。

## 最终源码检查收口

初轮准确源dd32059的诊断off/on全量后端均为809个独立主测试通过，另5个unittest子检查，JUnit tests属性814不能当作814个独立用例；两轮覆盖2632/2916行。两次整体CI仍为失败：Bandit B110发现3处诊断记账异常吞没。a71a1529将三处改为窄范围contextlib.suppress，仅包计时/计数，不包业务、yield或commit；本地完整static通过，最终精确源需重新跑完整CI，旧失败证据保留于agents/coordinator/global-latency-ci。

64次真实MySQL幂等生命周期的拆分计数：INSERT边界5次，UPDATE边界0次，整窗口7次，其中2次来源未定。该实验不证明生产热点来自页拆分，也不证明大响应UPDATE直接拆页。所有自有MySQL实例已关闭。

最终固定cloc2.10计量应用5987行、辅助780行、核心5207行；核心仍超5100上限107行。新增诊断未从应用规模中排除，当前调查版本不能宣称作业规模通过。

## 准确源最终CI结果

准确源`bcec3326b40814fdb1922bbfea7c29473b47ba47`：默认诊断off推送CI41169683822、显式on CI41169697472均四job全部成功。各809个独立主测试通过（另5子检查；XML tests属性814）、前端89项通过，全部44个生产Python文件被覆盖，2628/2910行=90.31%，Ruff/配置/Nginx/Bandit通过且Bandit零问题。PUBLIC最终gate与原JUnit gzip及精确摘要见agents/coordinator/global-latency-ci/FINAL_RESULTS.PUBLIC.json。

上传未完成时误触发旧源dd320的dispatch41169619555已立即取消，不作为最终验证。初轮Bandit失败保留，不改写成成功。此后的提交仅归档CI结果；不变更上述被测业务/测试/部署源码。此CI不等于生产270ms性能验收，不等于云端已应用PL1配置，规模超限仍未通过。
