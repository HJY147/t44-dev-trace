# 中性主机序列：先行设计

v3只由冻结v2派生：PROC_FILES追加/proc/net/snmp，context追加os.cpu_count实际逻辑CPU数（未知null），其余AST不变；v2原件/未执行状态不改。另独立load-host脚本不导入Docker/网络/DB模块，无参数，只读固定五/proc，UTC/monotonic/10秒目标/5400或10:10Z较早停。root现有0700 /run/t44-relay852仅新建自身UUID0600输出，不列目录/读取任何852私有内容，只回读自己创建的文件作hash。

保留raw CPU累计、MemAvailable/Swap、netdev bytes/packets/errors/drops、TCP RetransSegs等原始表，缺源null+NOT_PROVEN，无性能门禁/600s口径变化。摘要仅file/sha256/bytes/nsamples/fails。IO/调度和双采样重叠有真实开销，非峰值/非原子；CPUcount非cgroup quota。842仅最小合成guard，不运行collector/proc/Docker/云。
