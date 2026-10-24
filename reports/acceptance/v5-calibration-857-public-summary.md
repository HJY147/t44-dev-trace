# 857 自有 stub 校准脱敏摘要

作者：AI /root/independent_method_v5。本轮结果：**有限本机 owned-stub 工具校准通过**，仅限冻结短时场景。**产品性能未测试**，未执行正式600秒负载，不作排名。

出处：F2 `ac645aa1de92b6ec61fd53301cb794f7ce00d4bc`；root明确执行准入提交（按提供值）`f7e83ca`。本轮只执行一次，冻结工具/环境/方法/案例指纹仍匹配；858原件与INVALID结论未回写，根索引未修改。私密源码、案例、trace、日志及nonce/PID/端口不开放。精确指纹与私密证据封印SHA见配套JSON。

| 冻结条件 | 实测结果 | 判定 |
| --- | --- | --- |
| 400逻辑用户、10000唯一请求全部成功，对账一致 | 400用户/400自有连接；10000到达与10000成功；失败/取消/未启动均0 | 满足 |
| 客户端入队未完成峰值400、stub到达驻留峰值400 | 均400 | 满足 |
| 固定4秒内部区间平均入队未完成数≥360 | 399.964807 | 满足，仅工具诊断 |
| 请求P95≤270ms，包含200ms固定等待和客户端成本 | 208.891291ms | 满足 |
| 短窗口归一化成功率≥1000/分钟 | 118107.042/分钟；观察5.080137375秒 | 满足，非完整分钟结果 |
| 每个客户端采样CPU比例≤1% | 最大0.011556% | 满足 |
| 完整parent寿命<150秒、client寿命<60秒 | 外层parent包络6.556952292秒；client最大创建至收回上界6.380755625秒 | 满足 |
| parent/child软硬限制读回符合阶段目标 | parent64/64FD与15/15CPU秒；stub512/512FD与20/20CPU秒；四client各160/160FD与20/20CPU秒 | 满足 |
| 全部owned孩子零退出并清理 | 5个孩子全部退出0并收回；最大6个owned Python进程 | 满足 |

外层使用同一现存工具运行时单调时钟，在spawn前取起点、close后取终点，覆盖解释器启动、冻结核验、派生、负载及cleanup；包络6.556952292秒确实包住内部工作段6.471196417秒。各client创建至收回上界分别为6.380755625, 6.378889833, 6.377425375, 6.376004167秒。未使用原858的冲突时域倒补。

资源限制的before/after软硬值、平台RLIM_INFINITY和五个进程的采样CPU/maxRSS原始值均在JSON中。RLIM_INFINITY实际为9223372036854775807，只有与平台常量相等才表示无限，不能按正负号猜测。CPU读数截至最后一次自身采样，不覆盖最终序列化/退出尾部；parent自身完整CPU与宿主总CPU/RAM未测量。采样成本未从请求延迟扣除，未做采样关闭对照，剩余扰动未知。

Python时钟为monotonic_ns纳秒，外层performance.now为毫秒，CPU为秒，输出文件为stat字节。maxRSS保留raw；当前[Apple XNU取值路径](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/kern/kern_resource.c)及其[resident_size_max单位](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/osfmk/mach/task_info.h)、[CPython3.12.10直传路径](https://raw.githubusercontent.com/python/cpython/v3.12.10/Modules/resource.c)支持按字节理解，但未匹配本机内核源码版本，故该单位解释有此限制，不转换KiB/MiB、不作为内存通过门槛。

物理wire发送并发未知；入队/到达驻留均不能称为同时CPU处理。短窗口归一化吞吐不证明完整一分钟或600秒。未接触SUT、既有服务、DB、MQ、付费资源或CI。原老师400并发/完整600秒/P95≤270ms/每分钟≥1000成功及无业务失败要求全部保留。本轮清理后停止，不自动重跑或延伸为产品验收。
