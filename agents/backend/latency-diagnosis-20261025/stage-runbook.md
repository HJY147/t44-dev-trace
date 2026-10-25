# source935开发诊断包交接（不自动执行）

当前代码C：b76775326095bdc92ddd5883eaa4dc79eaf7d2d1。只用`stage-delivery.b7677532.json`或`stage-install.b7677532.txt`，不要使用历史`stage-delivery.initial.json`及旧`stage-delivery.final.json`。current core SHA8f0dbec80e168a8dbac7f3707b467d16c9146fe7937b7c5c2f6825b20bf966f6，net SHAdd776e1fe6c94aa005fa6b00734a6f8cebe54b24a9352917dbea7a771682552b。

JSON投递10575字符；附自解码install段11205字符，均≤18432。根先设置`T44_DIAG_INSTALL_DIR`为绝对、尚不存在、父目录owned的新public-tools目录；install仅解压/双SHA/长度核验、O_EXCL写两文件0444，不启动服务、接库或改内核。新目录最终0555供原容器UID读取，诊断输出用**另一目录**，须原UID可写。原source935镜像/root完整hash证明仍由部署岗保管；工具5件关键源指纹不是完整镜像attestation。

## 应用入口和中性packet

在原源935 Python3.12容器、原UID、原TLS/证书验证/端口/worker/keepalive/backlog/线程设置上，仅换诊断app目标：`python -m uvicorn --app-dir <public-tools-mount> 810_stage:app_factory --factory ...原launch参数...`。数字模块入口已本地importlib离线验证。根保留原外层controller的硬stop/deadline；本工具不创建新watchdog线程。根先持有新sessionpacket、准备新可抛schema和真实20任务/3角色/serviceP1再启动，工具不DDL/seed/登录/猜ID；不触旧13306或任意旧P/F库。

根在私密env中提供：

| 字段 | 精确要求 |
|---|---|
| T44_DIAG_ALLOW | source935-development-only |
| T44_DIAG_PRODUCT_SHA | 935ab5b93bea788672c2b4a088c79cfeed848954 |
| T44_DIAG_MODULE_SHA256 | 8f0dbec80e168a8dbac7f3707b467d16c9146fe7937b7c5c2f6825b20bf966f6 |
| DATABASE_URL | 仅根新sessionpacket内的mysql+pymysql专用角色DSN，不放本报告/公开日志 |
| T44_DATABASE、T44_DIAG_DATABASE、DSN库名 | 三者逐字同；本轮允许精确`t44c_r9diag935_p`，或原`t44_diag810_[A-Za-z0-9_]{1,40}`；其它旧库/近似拼写拒绝 |
| T44_DIAG_HOST、PORT、USER | 与DSN解析后的新私有MySQL host/port/user逐字同，禁止root用户与13306；本轮容器3306由根指定 |
| T44_DIAG_OUTPUT | 绝对、已存在、非symlink、原UID可写的独占新目录 |
| T44_DIAG_LIMIT | 每worker1..10000，默认128；是总样本cap不是每operation配额 |
| T44_DIAG_SAMPLE_MODE | header（默认）或all（显式，不要求改客户端header） |

header模式仅`x-t44-diag-sample: 1`记录；all模式从启动起采样，不改任何HTTP响应/错误/业务；需将setup/warmup与测量阶段分开、核cap_skips，不能让健康检查/预置耗尽cap后把空文件冒steady采样。若既有consumer不允许加header，根可选all，分阶段用新进程/新输出目录；不得改冻结压力工具来配合采样。

每worker生成独立`stage-PID-UUID.jsonl`：probe_start、source_binding、request、probe_final。request只有原request_id/response_request_id、route固定operation、UTC/perf ns、真正handler thread id/CPU、聚合phase、最多16个真实池快照和peak、status/exception class/响应字节数；无body、token、SQL文本/bind、DSN。四路径真实fixture与合法请求由另一harness/根packet提供；本工具不提供JSON stub代替业务SQL。

## 各阶段语义和验收诊断文件

ingress→body_consumed是应用读到最后request帧，非网络首包/末包；body_consumed→handler_start含框架、路由和线程等待，不单称线程pool队列。handler phase含Runtime/DB/schema/wire/render；各phase inclusive重叠，**不可相加**。同线程CPU只对同步函数/SQL/pool计时，不把async eventloop CPU当单请求CPU。

pool_connect包含队列/新建连接/preping/checkout；pool_queue_get是该实际QueuePool内部Queue.get调用耗时（含队列bookkeeping），不含后续connect/ping。Empty可为正常非阻塞取空，不能记业务失败。若queue接口不可用，queue_get_available=false而不是伪0；pool快照size/checkedin/checkedout/overflow是非原子原方法取值，overflow初始化可能负，checkin回调发生在真正return之前。

cursor_execute是SQLAlchemy事件包络，PyMySQL buffered execute可能已包含fetch；不是MySQL纯执行/锁等待。ASGI send_end只是末body send await返回，不是TCP ACK。旧Server-Timing漏handler前及最后wire/render/send，本工具补这些边界；latency-appdur残差不是网络根因。

只在root确认每workerprobe_final存在、selected==written、diagnostic_valid=true、无T44_DIAG_INVALID stderr、ID未串/丢、cap/skips与阶段合理时使用数据。observer/writer失败保原HTTP/SQL异常，但标诊断INVALID；write在app返回之后并累计writer_ns，开销非零，能影响后续调度，不把诊断短窗直接当正式P95。close恢复所有钩子，app_factory拥有的engine在shutdown dispose；记录归还前checkedout，不隐式dispose外部调用者engine。强杀缺final或记录未闭合为证据缺口，不补0/伪终态。

## Linux网络旁路工具（根以后执行）

显式`python 810_net_snapshot.py --run --pid <同namespace已确认ownedPID> ... --port <新API端口> --seconds <1..120> --interval 1 --output <新文件>`。只读ss -Htan、当前namespace/proc sockstat/snmp/netstat、ephemeral range与指定PID起始tick/FD计数；不读取FD指向、cmdline/env、连接地址或payload，不改sysctl/协议/冻结工具，不派生PID发现。

只输出TCP状态/API port状态、非LISTEN字节队列、LISTEN按ss原报告的queue值、TIME_WAIT/distinct ephemeral local ports（非4tuple耗尽证明）、全namespace RST/retransmit/ListenOverflows/Drops等累计值及采样开销。全局计数不独占归SUT；host/containerPID与network namespace必须在根packet明确。不足interval/权限错误/null/PID变化保留，事后单快照不冒完整区间；当前仅parser owned测试，没有在本机或云运行网络采集。

根未来按1client每四路径20请求、40/400短诊断，保真实existing-event escalation dedup；正式400持续600秒/270ms/零错需另独立准入，这些门槛没有降低。新schema精确允许项是本轮一次性诊断授权，不套未来正式F/P。
