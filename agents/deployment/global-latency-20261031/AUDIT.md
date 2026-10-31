# 全局延迟：部署层证据与可否定假设

基线bceb7ec5，执行者deployment AI。服务器关闭；未SSH、读QA PRIVATE、改用例、压测、build或更改资源。当前先交设计，不凭直觉增worker/pool。

## 已核事实及其边界

| 来源 | 事实 | 不能推出 |
|---|---|---|
| agents/coordinator/manual13-live/TIMING_RESOURCE.PUBLIC.md/json | 实际是p12/source90b，不是p13。482100配对exchange；contract appP50/P95=15.992/940.286ms，query28.648/957.313；配对E2E-app差值P95约62–66ms | app内部是SQL还是CPU；p13相同分布 |
| backend/t44/api.py:handle | perf_counter在sync handler入口启动，response schema检查后、JSONResponse编码前生成app header | 含AnyIO前排队、body接收、编码/send；app值是CPU时间 |
| agents/coordinator/manualp13-resume07-preparation/RESOURCE_WINDOWS.PUBLIC.json | p13前后各约64s窗口：API17.68/15.14核、MySQL3.85/3.31；throttle增0；MySQL设备写约3207/3200ops/s | 全程CPU/磁盘百分百饱和、IOPS==云盘额定IOPS、已唯一定位I/O根因 |
| 原kit manual13-ready-20261030/deployment/P09-existing-containers.PUBLIC.json（本机PUBLIC原件） | API10GiB、MySQL12GiB，七角色NanoCpus/CpuQuota=0；不是默认Compose的CPU约束 | 实际cpuset/host CPU pressure/64worker PID分布；不限quota不等于64核都可随时运行 |
| records/cloud/r30window01/r30-APP-prepare-status01.original.PUBLIC.txt | 历史执行probe报告64worker、pool5、overflow0，API预算320；actual MySQL max_connections384 | p13当时完整Cmd/Env、每worker active/queue。不能用历史预算当p13实时逐进程观测 |
| deployment/cloud-reuse/app-campaign.py / final-window原factory | 生成配置MySQL8G bufferpool、maxconn384；TLS nginx2048连接/worker、keepalive64；当前镜像web默认nginx1024连接/worker、upstream keepalive32 | 原p13磁盘/容器中的nginx -T与MySQL GLOBAL变量逐字一致，尚缺live snapshot |

四类约1s尾而轻contract/query中位仅16/29ms，支持共享等待/调度/周期争用优先于“每次业务都需1s CPU”；这是排查优先级，不是根因判定。p12延迟大尾已经在handle内，不能把主要责任直接归为nginx前、客户端pool或AnyIO前队列。handler内仍包括SQLAlchemy pool等待、DB往返、锁/IO以及worker线程被GIL/OS挂起。

400client是闭环有限并发：完成后才能下一次，320个API连接预算不代表320实际busy；每进程pool5可能在连接分配不均时局部排队，别的worker空闲。64进程×40token理论2560同步并发也不等于有2560可执行请求。CPU=请求率×平均CPU服务时间；等待DB时多余CPU空闲是预期现象，不以CPU必须100%作为优化目标。现有api耗核不是64worker实际busy数。任何pool放大同时需MySQL预算和持锁时间评估，不能把pool等待转成更大DB并发。

## 官方primary核对

- [Starlette线程池](https://starlette.dev/threadpool/)及[原run_in_threadpool源码](https://raw.githubusercontent.com/Kludex/starlette/main/starlette/concurrency.py)：同步def经AnyIO to_thread，默认40token共享于该进程上下文，不是全机40。增加线程有开销，不是CPU吞吐保证。
- [Uvicorn设置](https://raw.githubusercontent.com/Kludex/uvicorn/master/docs/settings.md)：CLI优先于环境；workers/limit-concurrency/backlog/keepalive分别是进程数/并发准入/等待连接/空闲保活，不可混为CPU核。当前官网master非已部署依赖版本证据。
- [官方fullstack模板Dockerfile](https://raw.githubusercontent.com/fastapi/full-stack-fastapi-template/master/backend/Dockerfile)使用fastapi run --workers4；这是应用模板，不是本项目400并发/64CPU的已验证容量。不能直接照抄4或64。
- [Nginx upstream文档](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)：keepalive是每worker闲置连接缓存，不限制总可打开连接数；keepalive32不是活跃并发32上限。upstream_response_time含响应接收；upstream_connect_time/header_time才能进一步拆连接/首字节。[日志模块](https://nginx.org/en/docs/http/ngx_http_log_module.html)支持buffer/flush，若新增每请求日志应考虑写入开销，不以大量日志制造新的盘瓶颈。

## 现有timing能定位到哪里

app monotonic duration与客户端monotonic elapsed相减不需要两机器wall-clock同步；但必须同一exchange配对，不能P95相减。Date/server_time只能作为元数据，不用于跨机精确耗时。QA PUBLIC未给本轮客户连接pool wait/握手/发送/读取分段，不能臆造客户端pool堵塞。

当前web/nginx日志有request_time/upstream_response_time但无connect/header_time；TLS与web是两跳，需分别记录，不能叠加两个request_time当CPU。原log_format用$request_id，而app忽略入站X-Request-ID后生成UUID，响应带另一ID；默认request_id列不一定能与客户端UUID直接join。可额外记录$upstream_http_x_request_id为response_request_id，不改变原字段。仅现有日志不足以定位handle内部wait。

## 最小可关闭观测设计，尚未实现或部署

1. 后端岗先加同线程perf_counter与thread_time配对、parse/runtime/schema分段；数据库岗加pool取得连接等待、持有时长、SQL/commit spans，统一request ID。thread_time和wall差大只说明等待/被抢占，不能直接等同DB时间；SQL span可能包含GIL deschedule，需与DB native waits联合。
2. 部署可单独提供默认关闭的nginx诊断include，不改任何worker/pool/资源/业务响应：追加response_request_id、proxy request_id、upstream connect/header/response时间、connection_requests、bytes、upstream_status，保留“-”及多上游逗号语义。不得记URL/body/auth/cookie。仅抽样并有缓冲/上界/显式关闭；两个代理分别标hop，按response UUID对齐。
3. 同期只读快照白名单Cmd中workers/backlog/keepalive、T44 pool非秘密数值、实际子PID数量/各进程CPU/线程数/上下文切换、cgroup cpu.max/cpuset/pressure、MySQL有效变量及native wait；不输出完整Env。它们解释“配置为何未用满”，不以默认Compose冒现场。
4. 当前不实施默认配置修改：没有证据证明nginx并发限制或worker不足。p12 handle内大尾优先由backend/database分解，若证明主因已在代码/SQL，先修该主因，勿再把可用服务器时间花在泛化对照压测。

当前缺少逐p13请求handler细分、pool分布、DB wait、逐worker压力；停机前无法补造。没有性能改善/根因关闭声明，原NP结论不改。
