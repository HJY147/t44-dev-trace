# 两台整机资源序列：能力交付，非性能结论

root审核源码hash后分别单独执行：应用机 `python3 /run/t44-delivery/seven-resource-sampler-v3.py`；发压机 `python3 /run/t44-relay852/host-resource-sampler.py`。不接受参数，不安装依赖/改网络/服务/现有权限，不操作任何独立脚本/环境包。两个父目录须分别已root-owned0700，脚本不会自动创建或修权限。

app v3只从冻结v2派生：PROC_FILES新增/proc/net/snmp、context新增os.cpu_count；其他AST/反向bytes完全相同。固定projectt44七服务与所有既有约束保持。v2原件与未执行状态不改；root转述旧v1已自然16:44结束，本岗未kill/观察其回执，不代写成功。

host版不含Docker/网络/DB调用，仅五固定/proc：stat原始CPU累计ticks、meminfo含MemAvailable/Swap、diskstats、net/dev含各接口bytes/packets/errs/drop、net/snmp保留TCP表头和值（含RetransSegs）。cpu_count为os.cpu_count实际OS逻辑数量，不推定cgroup配额/物理核；未知null。两版都是UTC/monotonic时间包围，目标每10秒，最大5400秒或10:10Z较早停止采样，不补迟启动窗口。多源非原子/非峰值，命令/读取/序列化/落盘/收尾hash有真实开销；网络和IO累计非速率，CPU累计需按实际间隔解释，不保证两机时钟误差，仅UTC格式不证明已同步。不能据此改变600秒门槛。

host版只检查/run/t44-relay852目录元数据，并O_EXCL0600新建host-resource-UUID.ndjson；不列目录、不打开任何既有852文件。最终只回读自身已创建inode/uid0/mode600/nlink1文件计算hash，创建碰撞失败绝不读取旧文件。每固定源读上限256KiB，缺失/超限为null+NOT_PROVEN，其他源保留；未知CPUcount也NOT_PROVEN。摘要严格file/sha256/bytes/nsamples/fails五项，nsamples为完整写入的样本行，fails是含缺失的样本数；零样本/IO失败或任一缺失均非零，不能冒容量通过。stdout不输出/proc内容/原异常；数据仅私有NDJSON，无应用日志或密码。采集完成与正式测试通过分开。

预算100元/两机18:30释放/正式18:10硬停据root此前实际转述继续有效，100不是已花100；本工具不延长云租期或负载。独立中性新增字段只为容量饱和度解释，缺证NOT_PROVEN，不注入案例/成功预期。本岗没有云执行、没有collector main或本机/proc读取；842五项最小合成guard和Ruff/compile/diff-check通过，uid元数据仅测试中mock。真正两台样本/完整性待root实际回执。
