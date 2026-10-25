# 性能新round2设计与旧轮停止边界

root于本阶段明确另开免费本地性能round2，因独立transport工具需要真实修正并完整630秒窗口，不缩负载/阈值。产品c8、7worker、新perf库及数据不变；新app停止09:10:30UTC、broker09:12、force09:15、首次启动准入09:00。functional原08:46:30/08:47/08:50及其grant/报告不延长。旧perf全部W8/W7/prestart/目录原字节保持，不给旧进程改时间常量。

先只停旧perf run performance_20261025_a32db96cee7e43c2。实际预检API/consumer/scheduler/application-guardian均无record/PID；guardian38088、Rabbit38097、EPMD38091的UID501、lstart/PGID/argv哈希与登记一致。信号前再逐项重核并追加独立owned receipt，SIGTERM仅给guardian38088，由其既有handler完成自己的正常broker/EPMD停机。最多45秒观察；只有身份仍全匹配才可强停该guardian，任何身份不明拒绝信号且如实失败。随后仅可对已证实属于旧perf的broker使用旧控制器正常stop，不操作functional/共享MySQL/全局进程。实际PID全部消失、指定新端口bind-free后才复用端口；停止回执/旧配置SHA保持公开留痕，不能用下一轮ready掩盖失败。

新round2使用全新父目录native-performance-round2-20261025、新runid/Cookie/user/vhost/privateCA。从已固定53d→performance W8→W7的精确公开工具派生链继续显式替换：仅新父目录/runid前缀、UTC时间常量/展示字段、首次准入09:00、应用watchdog相对broker提前90秒而非30秒；保留7worker/单perf库/精确源/私有与cookie/拥有权/关闭逻辑。每层原新SHA/位置/次数与配置留derivation，旧工具不覆盖。新guardian在broker启动前登记独立进程，应用仍不启动直到root单独phase许可。

仅prepare新source/archive/CA、broker/guardian、W7 binding及processes=[]的prestart metadata。root确认后才能API/consumer/scheduler；真正启动后另冻结运行native-build，停止与性能/完整回收结果都不预填。新检查用819目录round2子阶段，保持6项旧guard原件，记录本轮真实命令与状态后立即释放槽。
