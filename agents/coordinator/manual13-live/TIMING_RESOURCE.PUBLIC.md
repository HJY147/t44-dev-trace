# p12既有证据：响应头耗时及压力机资源聚合

本次只离线分析已认证r30manualp12证据，无云访问、无测试或SUT重跑，无新准入或验收结论。

四类全部482100个稳态exchange均有可解析的`Server-Timing: app;dur=…`，dur单位为毫秒。未发现其他符合timing/process-time/response-time/runtime/duration/elapsed名称的响应头。以下P50/P95均采用nearest-rank；差值先对同一exchange逐项计算“端到端elapsed−app dur”，再求分位数，不能用两个P95相减替代。

| 请求类 | 配对样本数 | 服务端app P50 / P95 ms | 同exchange端到端 P50 / P95 ms | 配对差值 P50 / P95 ms |
| --- | ---: | ---: | ---: | ---: |
| query | 96410 | 28.648 / 957.313 | 71.162613 / 1065.937272 | 46.687066 / 61.942767 |
| transition | 192829 | 640.273 / 1040.715 | 680.760639 / 1622.151004 | 49.260505 / 101.897736 |
| contract | 96432 | 15.992 / 940.286 | 62.869427 / 1048.957214 | 47.614054 / 65.634115 |
| escalation | 96429 | 129.674 / 1038.544 | 180.099410 / 1205.121100 | 48.311551 / 70.099276 |

`app`是实际采集的服务端自报时段。已冻结中性契约没有定义其精确计时边界；本统计不据此拆分排队、数据库、CPU、代理、网络或客户端成本。

压力机稳态范围内有592个原始load_resource采样，首末相对cohort起点为60.012973192s和659.930514539s，实际差分区间599.917541347s；没有恰好60s与660s边界的采样，因此不将该差分写成精确600s累计。

| 原始采样字段 | 首末差分／观测范围 |
| --- | --- |
| cgroup CPU usage | 292.553426 CPU秒；user274.655560秒、system17.897866秒；该区间平均0.487656核当量 |
| cgroup限流 | nr_periods增5329；nr_throttled增0；throttled_usec增0 |
| 进程rusage | user增274.528019秒、system增17.870768秒；maxRSS首末63432→104564 KiB |
| memory.current | 首末及最小最大183037952→470306816字节；增287268864字节 |
| memory.events | low/high/max/oom/oom_kill差分均0 |
| pids.current / pids.events | 全部采样403；max事件增0 |
| 证据写入队列 | 首末0→0；采样范围0至67 |
| 上下文切换 | 进程voluntary增8141859、involuntary增3164 |

缺失项：原load_resource没有cpu.max、memory.max、CPU pressure、逐线程/逐核CPU、网络/磁盘速率或服务端分项计时；没有精确稳态边界累计读数。CPU瞬时利用率未直接采集，只能使用累计cpu.stat/rusage差分。原工具配置的8CPU/8GiB预算不替代上述缺失的实时cgroup上限读数。现有数据不支持对这些缺失项补值。

脱敏逐字段数字及响应头名称计数见同目录TIMING_RESOURCE.PUBLIC.json。原始payload、header值、密钥与分析脚本留在本岗PRIVATE；公开内容仅为字段名、脱敏聚合及方法说明。
