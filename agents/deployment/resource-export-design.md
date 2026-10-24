# 资源证据回收：实施前设计

只导出本岗NDJSON。root从采样器最终安全摘要提供精确路径+SHA，不扫描任何目录。app只接受/run/t44-delivery/resource-32hex.ndjson；load只接受/run/t44-relay852/host-resource-32hex.ndjson；两机分别执行，禁止任意路径/.env/token/key/用例/结果。目录root0700、文件root0600/regular/nlink1，NOFOLLOW及前后inode/size/mtime/ctime稳定核对，原SHA必须等于完成摘要。

每机一个新UUID.tar.gz排他0600，仅含原始中性NDJSON与manifest。manifest记录原hash/大小/真实sample UTC范围/样本数/失败数/解析缺证；有缺失或坏行保留raw、NOT_PROVEN，不补数据。stdout只安全archive路径/hash/bytes/计数，不打印raw/proc/私有IP。压缩输出写入时计算hash，不读取其他文件。资源限额：最多8文件、单64MiB、总256MiB、输出128MiB、每行2MiB、执行预算60s；超限/不稳定fail-closed，保留失败不自动删除其他文件。

UTC10:10之后、10:28之前准入（18:30释放前留120秒），先等两采样完成摘要，不导出活动文件。root用已授权官方文件下载功能分别下载两机包，先核完整包hash/bytes，再在本地只验证manifest白名单原hash/bytes，UTC/计数以raw实际观测为准，不当性能通过。当前49,520B密文成功且hash一致只是已有小文件通道事实，不保证新大包已下载；源释放后无法补取，目标18:10–18:20完成，18:25前处置传输失败，不自动续费或延长负载。

本岗只准备代码/离线合成检查，不执行云/浏览器/下载，不读取任何852私有资料；本轮无新test代码文件/编号。
