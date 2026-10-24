# 七服务只读资源记录（不是性能门禁）

root审核script SHA后在应用机云助手root前台单独执行 `python3 /run/t44-delivery/seven-resource-sampler.py`，不接受参数。要求现有/run/t44-delivery为root-owned0700、Docker default context本地unix、/opt/t44-c-0dfb55c HEAD精确C且tracked clean；没有容器内容attestation，不把源码HEAD当镜像身份。

固定project=t44、mysql/rabbitmq/api/consumer/scheduler/web/tls-gateway七服务，ps唯一64hexID与inspect只投影ID/project/service/running；拒外来、缺失、重复、停止，不读Config.Env或容器日志。每次复核原映射，不自动重发现/修服务；一次docker stats --no-stream --no-trunc仅ID/CPUPerc/MemUsage/MemPerc/NetIO/BlockIO/PIDs；固定读取/proc/stat、/proc/meminfo、/proc/diskstats、/proc/net/dev，各256KiB上限。UTC+monotonic包围样本；错误为稳定unknown，failed_samples真实累计，无原异常/凭据。

从进程开始最长1200秒且不晚于2026-10-24T08:44:00Z结束采样，迟开始不补时；收尾flush/fsync/hash实际耗时计入最终elapsed。目标start-to-start每10秒，命令/proc/序列化/落盘/调度都有开销，超时可能延后实际间隔、减少样本数，不称零影响。root外层云任务应只覆盖该截止内窗口，不能因任务超时延长云资源或负载。

唯一数据文件为/run/t44-delivery/resource-UUID.ndjson，O_EXCL0600，不覆盖旧文件、不改已有权限/网络/服务。context行+真实sample行，最终stdout仅安全路径/hash/bytes/actual_samples/failed_samples/setup_ok/实际elapsed/结束UTC及performance_verdict=null。exit0只表示采集完成且无失败样本，exit1指telemetry缺失/不完整，不是产品性能判定。开始后容器重建导致原ID无效时保留failed样本、不切换到别人容器。

Docker MemUsage扣缓存不等于RSS；PIDs含线程；IO为累计格式非速率；CPU展示窗口不是全正式负载窗；多源非原子、非峰值。现有scheduler/consumer/health probe继续，不能宣称无其他流量。此为新的七服务主机/容器观测，不是原六服务runtime-usage合格声明，也不是独立验收结论。只读能力本地8项合成guard/Ruff/compile通过，未运行collector或读取本机/proc/Docker/云；root16:13全7healthy仅实际转述，尚非采样回执。
