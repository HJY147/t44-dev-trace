# 连续资源raw与私网append mirror（不改变SUT）

resource-stream.py 44067B/SHAf911acf470a61221197e58fbd18d4cc42c1a5a7693ae929454f540e2c400f76d。17项本地检查0.10s/Ruff绿，包含真实loopback TLS/CA拒绝/nonce/单路径/原字节。没有云daemon、Docker/cgroup真实采样或跨VMmirror成功事实；这些待root实际执行，不预填。

仅新f4 generation（controller9c1abe）可prepare；不接受旧935 phase。root通过官方云助手分别将同一脚本以新路径O_EXCL落app/load，44KB原文base64超过32KiB，应压缩后传并核上面原文SHA，不改旧helper。全部stdio/stdlib，无pip/新账户/SG/IAM/公网口。

## App端准备与启动

```sh
python3 /root/t44-r9/resource-stream.py prepare-app \
  --phase-dir /root/t44-r9/campaign-f4-01/p --phase-binding-sha256 ACTUAL_NEW_P_BINDING_SHA \
  --app-ip ROOT_PRIVATE_APP_IP --load-ip ROOT_PRIVATE_LOAD_IP --port 18446 \
  --run-id r10metrics01 --output /root/t44-r9/resource-app-f4-01 \
  --sample-until 2026-10-25T20:59:00Z --serve-until 2026-10-25T20:59:50Z \
  --interval 1.0 --byte-cap 268435456
```

这些时间是可审示例，root应按真实完整warmup/steady/postconditions设置；sample至少未来120秒，serve至少再留30秒收finaltail且不晚于21Z。不能选完整测试中间结束的短窗口。原SUT phase停止时间不自动延长。端口先bind冲突检查；appIP必须等于新phase私网IP、load不同私网IP。cgroupv2不可用则prepare失败，无静默估算。

输出只有新目录/bindingSHA/private-mirror-handoff.json路径与SHA，不打印nonce。原leaf server.pem/server.key只读建立TLS，CA.key从不读取；load只得公共CA。准备不启动服务。随后：

```sh
python3 /root/t44-r9/resource-app-f4-01/controller.py start \
  --directory /root/t44-r9/resource-app-f4-01 --binding-sha256 ACTUAL_APP_RESOURCE_BINDING_SHA
```

新systemd unit=t44-resource-r10metrics01.service，Restart=no、UMask0077、ReadWritePaths仅自己新目录，原代码/binding/unit文件SHA与MainPID/UID/startticks/argv实核。RuntimeMaxSec＋daemonUTC/monotonic双截止，不依赖CLI/浏览器或agent活跃。只Docker ps/inspect元数据和精确CID cgroup/proc读取，绝无Docker exec/SUT REST/DBSQL/环境读取。

root用官方同账户私有运输把新private-mirror-handoff.json原字节放load新0600文件，核handoffSHA；它含独立telemetry nonce/两私网地址/公共CA，是本通道最小配置，不含账号、DSN或API token。不得入仓/公开日志/下载URL参数。

## Load端准备与启动

```sh
python3 /root/t44-r9/resource-stream.py prepare-mirror \
  --handoff /root/t44-r9/inbound/private-resource-handoff-01.json \
  --handoff-sha256 ROOT_VERIFIED_HANDOFF_SHA \
  --run-id r10mirror01 --output /root/t44-r9/resource-mirror-f4-01

python3 /root/t44-r9/resource-mirror-f4-01/controller.py start \
  --directory /root/t44-r9/resource-mirror-f4-01 --binding-sha256 ACTUAL_MIRROR_BINDING_SHA
```

若有中性真实阶段起止UTC，可给prepare-mirror同时传required-start/required-end，必须有序且结束≤sampleUntil。未给则包络检查为null，不能默认通过。monotonic只用于同一主机CPU差/延迟；跨节点与请求时间对齐用实际UTC/NTP证据，不能跨VM减monotonic。

独立systemd t44-mirror-r10mirror01.service，从offset0持续append新app-raw.jsonl。连接显式source_address=load私网IP，严格公共CA+appIP，无代理/重定向；服务端先load IP allowlist再TLS、有专用nonce头，字面GET/raw，无query/目录/其它数据。每块≤256KiB、offset/nextOffset/stream/binding/chunkSHA/wholeSHA严格校验。失败原件前256份保留、总错误数真实计数，不无限造日志；镜像原始字节不插入元数据、不覆盖/截断。

**必须在warmup开始前启动两端**，先status确认app已有真实numeric row且load实际有前缀数据；不能在steady结束才取一次snapshot冒充全区间。当前status只反映真实tail/null/错误，若没有数值不得进入正式阶段。诸如scheduler未启动时，会如实记录missing/null，不猜PID。

## 原始记录契约

raw.jsonl先resource_header，之后每轮七role的resource_sample，最后resource_final。采样错误是resource_sampling_error，不能补数据。每role有UTC/monotonic_ns/scheduledMono/延迟/耗时、resource_id=project/role/CID、actualImage、initPID/startticks/进程列表、Running/RestartCount、累计cpu_usage_usec、interval cpu_percent、rss_bytes、cgroup_memory_bytes、cgroup_anon_bytes。API整组含所有worker/tracker/init，CPU单核100%可大于100%。RSS是进程RSS之和（共享页可重复），cgroup memory含cache/kernel，二者分别记录；anon不能冒RSS。

首CPU无delta=真实null，缺进程/读取失败/多CID/未知image/计数reset均有明确reason；PID/CID和重启真实可见。每个数值都来自当次本机元数据，无插值/补0。参照[Linux cgroupv2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)与[proc stat](https://www.man7.org/linux/man-pages/man5/proc_pid_stat.5.html)。

## 状态、封尾、停止与证据

```sh
python3 /root/t44-r9/resource-app-f4-01/controller.py status --directory /root/t44-r9/resource-app-f4-01 --binding-sha256 APP_SHA
python3 /root/t44-r9/resource-mirror-f4-01/controller.py status --directory /root/t44-r9/resource-mirror-f4-01 --binding-sha256 MIRROR_SHA
python3 /root/t44-r9/resource-app-f4-01/controller.py seal --directory /root/t44-r9/resource-app-f4-01 --binding-sha256 APP_SHA
```

seal发USR1给经过unit/UID/PID/startticks/argv核对的本进程，只停止继续采样并写finaltail，**继续服务供load收全**。若无需提前结束，sampleUntil自动封尾。raw固定O_EXCL|NOFOLLOW FD/0600，inode/size/owner与封尾前全prefixhash复核；bytecap封尾原因真实记录，不能当正常完整区间。

load收到全部tail且wholeSHA/bytes/prefixmarker一致，才写mirror-final.json的transport_complete=true与原始SHA。actual_coverage给首尾UTC、各role数量/真实最大gap/null计数、采样错误和finalReason；required包络只检查真实时间边界，独立验收仍自行判完整性与阈值。transport完整不等于数值完整/覆盖或性能通过。

root确认mirror-final后各自正常stop：

```sh
python3 /root/t44-r9/resource-mirror-f4-01/controller.py stop --directory /root/t44-r9/resource-mirror-f4-01 --binding-sha256 MIRROR_SHA
python3 /root/t44-r9/resource-app-f4-01/controller.py stop --directory /root/t44-r9/resource-app-f4-01 --binding-sha256 APP_SHA
```

先直接stop app可能失去load读取finaltail的窗口，不能宣称完整回收。ownedstop核冻结unit与真实进程，未知不信号，保存PID前后和真实停止状态，不删raw/DB/卷/VM。raw.jsonl、sealed.json、daemon-final.json、load app-raw.jsonl、mirror-final.json、错误与control回执全部留私有；root可把load完整镜像交独立工具只读。最终云持续采样/覆盖/两端hash/实际进程停止均须另行真实回执，当前无这些通过声明。
