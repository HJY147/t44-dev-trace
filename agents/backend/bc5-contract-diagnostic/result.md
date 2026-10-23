# bc5 契约路径：有界开发诊断结果

后端AI执行。生产/运行资源未改；应用文件与bc5aef9c62393134582affb7a690acb33ac2b833逐字一致。只读明确公开stage06 MD/JSON，没有读取其私密驱动、原始数据或其他业务库。本轮不是正式400VU×600秒或独立验收，不解释托管正式三组的根因。

## 两次控制器事实

先提交设计08f8050d，再工具231445d。第一批22:35:01.756–22:35:19.146 UTC，exit1，17.29秒；bootstrap及3类sanity有效，baseline三个已完成子段均有效。timings-1却在endpoint入口前因本岗工具`observed_dispatch(function,...)`截获FastAPI转发的同名keyword而TypeError：2501次非JSON500和2501次连接异常，2501个server记录均0进入runtime/0 SQL。不是产品500/503，不把它们混进有效延迟；原日志/metadata在raw/、summary.json和raw-manifest.json，没有覆盖。

总协调明确允许只续未完成观测，先追加设计并提交44b9e8c48e2beb2c0ed52fb4b2d92787d46ef48a。工具首参改位置专用`func, /`，用一次真实FastAPI `run_endpoint_function`→原`_run_sync_endpoint`转发验证原返回值、`function=`/`arguments=`透传及AnyIO线程ContextVar，见offline-forwarding-check.json；没有HTTP/SQL。随后22:37:42.655–22:37:55.745 UTC一次显式continuation，exit0/13.00秒，只timings1/8/32和三类profile，不重复baseline/bootstrap/sanity。两个controller结束均确认18083关闭、两个自有server均正常exit0；两次启动前本库其他连接数均0。

实际配置：本机arm64/8逻辑CPU、Python3.12.10、单worker、40线程token、默认pool5+overflow10；SQLAlchemy2.1.6/FastAPI0.161.1。未修改这些设置。新bootstrap仅t44_profile中的合成project44/task6004及相应成员/迭代/session；没有清库或重seed。原fixture/token留ignored0600私密目录，不提交。

## 有效样本（nearest-rank P95，毫秒）

| 模式 | 并发 | 请求数 | 失败 | P95 |
| --- | ---: | ---: | ---: | ---: |
| baseline原API | 1 | 975 | 0 | 3.681 |
| baseline原API | 8 | 1562 | 0 | 24.383 |
| baseline原API | 32 | 1229 | 0 | 87.779 |
| timings观测 | 1 | 905 | 0 | 4.199 |
| timings观测 | 8 | 1496 | 0 | 25.010 |
| timings观测 | 32 | 1015 | 0 | 89.705 |

profile单并发只有每类1请求、共3个有效请求；不拿其P95作基线比较。有效主baseline3766，观测含profile3419，sanity3另列。每个观测client request_id恰匹配1个server记录、恰1个同步endpoint入口；无丢记录。三类候选只是原开发createTask/transitionTask/createReleaseAssessment JSON，不是三正式入口。每次必须200/valid=true/violations空/business_guards_executed=false。

## 同分母观测（逐请求均值，毫秒）

| inclusive阶段或独立观测 | 并发1 | 并发8 | 并发32 |
| --- | ---: | ---: | ---: |
| ASGI wall | 3.008 | 14.957 | 65.259 |
| runtime wall | 2.471 | 8.008 | 28.630 |
| runtime同线程CPU | 1.287 | 1.482 | 1.766 |
| authenticate wall | 1.511 | 5.328 | 22.785 |
| SQL cursor wall合计 | 1.212 | 4.180 | 9.239 |
| SQL cursor同线程CPU合计 | 0.322 | 0.427 | 0.421 |
| engine.acquire含pre_ping | 0.141 | 1.451 | 14.525 |
| dispatch-to-entry wall | 0.059 | 1.273 | 6.123 |
| 三次HTTP schema遍历合计wall | 0.420 | 0.421 | 0.439 |
| 三次validator构造合计wall | 0.042 | 0.041 | 0.043 |

这些阶段重叠，不能相加作总耗时分配。runtime CPU/wall合计比从52.08%降至6.17%，支持“本次并发增加伴随更多未消耗该线程CPU的经过时间”，不能把剩余全叫SQL、锁或poolwait。ASGI还有其他线程/事件循环/响应等区间，dispatch-to-entry含调度/排队/线程启动，未单独证明limiter排队。响应完整往返还含客户端同机竞争，不做差分硬归因。

所有观测恰1 acquire/1 checkout/1实时authenticate。候选1精确4个、2/3各5个SQLAlchemy cursor执行，均SELECT/0 SQL错误；这是实际管理cursor计数，不是全部网络往返。COM_PING、commit、pool reset rollback和DBAPI新连session初始化SQL不在cursor计数中。每请求1次commit；1次左右rollback是连接/池收尾观测，不能记为失败事务。

并发1/8/32共新建DBAPI连接1/69/211次。并发32 acquire的14.525ms内，新连调用摊均3.958ms、ping摊均1.447ms；剩余含初始化/池内部/checkout/等待，非纯poolwait。连接生命周期是可核下一步观测候选，不据此更改池。此路径普通SELECT不等于已采MySQL锁状态；本轮没有server锁等待字段，不能证明有/无锁瓶颈。

3个cProfile各只1请求，默认elapsed inclusive：类别1 runtime.execute19.081ms、authenticate17.261ms、rows17.226ms（首请求有冷新连）；类别2 execute6.852ms、rows5.343ms、Rows._execute4.831ms；类别3 execute6.101ms、rows3.994ms、Rows._execute3.512ms。它们重叠，不是三个独立CPU份额，也不能据首冷样本选优化。原pstats及安全相对路径摘要保留。timings整个服务段CPU6.925秒/wall10.755秒含启动/请求/空闲，不能当单请求CPU。

## 结论与未达边界

当前只读契约入口在本机短样本未复现503；没有运行transition/escalation，因此原正式结构化503原因仍未知。观测支持查询/连接/调度经过时间随并发增长；尚不足判断哪个资源导致托管正式P95，更不支持立即应用C、改SQL/锁/池/线程或阈值。下一步若授权，应在自己的开发写路径保留结构化503 code并关联具体阶段/事务边界及安全DB错误类别；正式环境须另有同次资源/连接/锁观测，不能回填本机结果。

原正式结果不被这些数值替代：三组P95均未过270ms，失败1021/0/2原样保留。源码规模仍引用固定6307/超1207，本轮生产净变更0，不重数/不改口径。C/B及任何生产优化仍未准入。完整方法见design.md，原结果分别summary.json/continuation-summary.json，两份manifest逐项绑定原始bytes/gzip SHA；公件已检查已知口令/Token匹配0。没有重跑全套CI或正式负载。
