# ROLE-deployment-HOST-RESOURCE-SERIES-v1

## root实际派工原文

独立测试新增中性量测字段要求（无case细节）：两台整机UTC序列/proc/stat CPU累计与cpu_count、/proc/meminfo(MemAvailable/Swap)、/proc/net/dev(bytes/packets/drop/error)、/proc/net/snmp(TCP重传)。请最快另存app sampler-v3仅在v2 PROC_FILES新增net/snmp及context cpu_count（保留v2未执行原件）；同时单独host-resource-sampler.py供load无Docker，固定root700 /run/t44-relay852下exclusive600 NDJSON，5个固定/proc（stat,meminfo,diskstats,net/dev,net/snmp）/UTC+monotonic、10sec间隔/5400秒或10:10Z较早停、无网络/DB/应用日志/参数/私有852读取、只输出file/hash/bytes/nsamples/fails。根还未云启动v2，无需kill旧v1（已自然16:44）。先设计，再快速实现freeze/hash供审，最小guardprefix842（root843已用于失败的本地HTML下载桥，浏览器拒绝未运行）。不要云执行。这是为容量解释保留饱和度证据，缺失NOT_PROVEN，不改600s门槛。

## 取舍与实际边界

先host-resource-design，再v3严格2处源码添加（PROC路径与context cpu_count），用冻结38400258…v2 Gitblob做AST/反向bytes校准。load独立无Docker模块/任意参数，仅五/proc，新建自身UUID600文件与inode验证回读，绝不列目录或读既有852。CPUcount按实际os读，未知null不猜配额；缺源NOT_PROVEN、不改600秒。842纯合成5guard，不执行collector main/实际proc/cloud。checkout首次未完成即调用Ruff造成配置缺失exit2，等待实际完成后按同CI配置绿，真实失败保留。核心hash先交root，后档案不阻塞正式窗口；没有接触root843桥脚本/任何852私密资料。
