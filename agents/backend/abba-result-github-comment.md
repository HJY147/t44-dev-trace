Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

ABBA单次执行结果已由backend离线复核，执行操作者是root总协调（不是本岗）：tool9741323，2026-10-23 18:38:01.58–18:38:41.46UTC，整体exit0/39.88秒，root观察18083已关闭。原件由root072bc4e归档，本岗没有复跑或发新请求。

36份gzip/raw SHA/长度核对通过；15557主请求0错，actualimport与A4c20/B5dcb快照、同fixture/配置、sanity/warmup均一致。四phase依次A/B/B/A，P95=31.206/23.974/23.390/31.358ms，每phase8并发8秒、1worker。三个candidate类别各自同向，仅代表契约校验三种payload，不能称三正式接口负载。说明与核对记录agents/backend/contract-abba-interpretation.md/json。

支持5dcb唯一接口单UoW在本次条件下有收益；只有一次顺序ABBA，无统计显著性或纯SQL/poolwait因果结论，CPU包含全生命周期。正式400并发10分钟/P95≤270ms和3500–5100源代码均为原任务书要求，未改变口径；6051源码仍超限，transition/escalation及独立正式性能未据此通过。03原controller exit1不改写。

接下来只写减少实际往返的内部RFC，先说明错误优先/锁序/撤销/幂等/独立审计/outbox/CommitUncertain与净LOC预算；不改生产/14冻结文件/项目X锁，不启动新负载，待总协调准入。
