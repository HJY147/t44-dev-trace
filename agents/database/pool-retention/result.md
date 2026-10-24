# 同15峰值的池保留ABBA：一次开发诊断结果

数据库岗AI执行；不是学生本人研究或手改。设计42a8bcb先于工具14490fe/0f6fdf5，离线检查/精确命令f75a8a419d04531a30788a734e56d2dda64baed0先于实际比较。应用文件仍逐字bc5aef9c62393134582affb7a690acb33ac2b833；14冻结件全同，生产净变更0，未修改默认池、SQL/锁/线程/全局参数。

唯一ABBA于2026-10-23T23:02:14.376665Z–23:02:53.234248Z完成，38.842秒含清理、exit0。每段单worker/40线程token，32客户端同步后1秒warmup与4秒steady；A=(5,10)，B=(15,0)，各段新engine并dispose。实际机器arm64/8逻辑CPU、Python3.12.10/SQLAlchemy2.1.6，pre_ping/LIFO/rollback未改。只t44_profile/127.0.0.1:18083和22:35原私密fixture，没有刷新登录/session或修改旧fixture/业务数据。预热2198、稳态8684，共10882请求，失败0；预热与稳态各存原件，没有从总连接成本中删除预热。

| 段 | 池保留+溢出 | 稳态请求 | 失败 | 稳态nearest-rank P95 ms | 成功请求/active秒 |
| --- | --- | ---: | ---: | ---: | ---: |
| A1 | 5+10 | 2079 | 0 | 91.591041 | 513.804 |
| B1 | 15+0 | 2255 | 0 | 74.471792 | 560.155 |
| B2 | 15+0 | 2237 | 0 | 72.908250 | 553.843 |
| A2 | 5+10 | 2113 | 0 | 92.600542 | 522.315 |

四段P95分别报告，不平均。成功吞吐分母是同步开始到实际完成排空的active wall；client整体wall/CPU另在原元数据，不用固定4秒冒充实际分母。

| 段 | 预热请求 | 预热新建/关闭/ping | 稳态新建/关闭/ping | 清理关闭 | dispose前idle | 观察峰值/清理后open |
| --- | ---: | --- | --- | ---: | ---: | --- |
| A1 | 551 | 112/107/439 | 436/436/1643 | 5 | 5 | 15/0 |
| B1 | 554 | 15/0/539 | 0/0/2255 | 15 | 15 | 15/0 |
| B2 | 556 | 15/0/541 | 0/0/2237 | 15 | 15 | 15/0 |
| A2 | 537 | 109/104/428 | 427/427/1686 | 5 | 5 | 15/0 |

DBAPI connect/do_ping/do_close为实际dialect调用尝试，原件保留异常类/false ping/线程CPU和阶段；当次所有调用成功、false ping0、无未分类事件。峰值统计为已成功创建且尚未观察关闭的连接，同时固定QueuePool预算15；四段dispose前checkedout均0，最终观察open均0。各段startup没有连接事件；预检自己的短连接在server启动前已dispose，不与15负载连接并存。

| 段 | 每请求acquire inclusive均值 ms | acquire P95 ms | 同线程CPU均值 ms |
| --- | ---: | ---: | ---: |
| A1 | 15.761147 | 40.596417 | 0.323226 |
| B1 | 2.561286 | 10.949917 | 0.057077 |
| B2 | 2.916320 | 13.900333 | 0.058474 |
| A2 | 15.357136 | 39.400000 | 0.310276 |

acquire包含队列/池内部、ping、建连、初始化、checkout与线程调度，不是纯poolwait；表中wall/CPU不能相加为总耗时。所有client request_id与server恰一匹配，每请求恰一同步endpoint/runtime/authenticate/acquire/checkout；三候选的SQLAlchemy cursor计数仍4/5/5，全SELECT、SQL错误0。初始化直接DBAPI SQL、COM_PING、commit/rollback不在该cursor计数内。19个实际应用/资源/池源摘要与bc5或已核官方2.1.6源相同。

## 结果边界与代价

这次短段支持“提高保留数减少观察到的连接关闭/重建”这一受限假设；B两段均无稳态重建，A两段有436/427次。四段延迟和吞吐同向，但只有一次固定ABBA、每稳态4秒、本机客户端与服务共享资源，且timings/lifecycle钩子开销没有独立校准，不能把差值全部归因给池或承诺生产延迟收益。它不是原400VU×600秒三正式组的错误/P95根因，也不是正式270ms门槛达标证据。

B当次每worker多保留10个空闲连接。服务端每连接内存未测，不能说零成本；未来多worker/多服务总连接预算、配置输入与默认值、故障恢复和回滚仍须另设计/交接/专审，当前不准入生产池改变。原正式三组失败、源码6307超1207及本人应完成的人工材料缺口均不改写。

18083前后均free，四自有server全部exit0且PID最终不存在；每段前当前app可见的本库其他连接0，后检0。该PROCESSLIST视图不证明跨账号全局无连接，没有扩权限。完成后已立即通知root释放窗口，此后仅离线分析/归档，没有第二次采样、额外profile/负载或HTTP/SQL。

完整summary.json、43份原件gzip及raw-manifest.json保留原bytes/gzip SHA256；公件扫描已知DB口令、完整DSN、原fixture Token及Authorization标记匹配0，值未输出。工具初次I001与源读取CA问题、离线合成失败路径测试均保留，其合成计数不混入上述真实请求。Issue4/3实际协商与精确GET读回另附本岗收尾回执。


已实际通过GitHub connector向[Issue4](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6376531906)/[Issue3](https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6376532216)交付上述事实与后端边界，再按各comments/:id精确GET读回；正文与实际提交/本地文件逐字一致（github-readback.json）。结果公开commit9d1deff3592d12e169f30a25537540c93096abf0，未设置review成功/关Issue或准入生产。本收尾只补文档/回执，955/生产与实际执行源字节不变。
