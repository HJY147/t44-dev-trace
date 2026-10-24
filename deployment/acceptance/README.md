# 独立 harness 的托管 Linux 环境

此目录提供中性运行环境和操作能力，不包含独立用例、预期缺陷或通过判据。环境使用现有固定摘要镜像/Compose，真实启动 MySQL8.4、RabbitMQ、4worker API、独立消费者、扫描进程及前端。它补足本地没有 Docker/Erlang/RabbitMQ 的运行条件；独立案例冻结、执行、审查和报告发布仍由隔离的 tester 负责。

## 精确版本与可触发入口

`.github/workflows/acceptance-environment.yml` 接受两种模式：

- `environment-check`：不选择、不执行独立 harness。只构建和启动环境，验证只读 SQL/队列审计连接、可恢复 RabbitMQ stop/start与pause/unpause、逐次JSON回执及合成输出加密/解密传输。本次能力核验不重复原 Docker 业务/备份恢复整套，也不证明独立 fault 覆盖。
- `harness`：要求完整40位 `product_source_sha`、独立冻结的40位 `harness_ref`、该 commit 中 `tmp/independent/` 下的 Python `harness_path` 和 RSA 接收证书 `recipient_certificate_path`。分别 checkout 产品和 harness，拒绝浮动分支/tag、目录逃逸和符号链接入口。超时60–1800秒，默认900、最小60，严格整数；workflow job仍上限40分钟。新上限不延长旧请求或已完成运行，也不保证准备/执行一定完成；正式性能指标与判据不变。

新 `workflow_dispatch` 必须已存在于默认分支才能触发；本仓库 main 受保护，目前不能把新文件静态合格视为已能手动 dispatch。官方说明：[手动运行 workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)。本实现另提供无需改 main 保护的 push 入口：**仅** `codex/deployment-acceptance-environment`、`codex/independent-harness-*` 分支，且**仅** `deployment/acceptance/request.json` 发生变化才触发。

环境核验请求格式：

```json
{"version":1,"mode":"environment-check","product_source_sha":"<40位产品commit>"}
```

独立 tester 先冻结自己的用例/入口/证书 commit H，再于带本环境实现的 `codex/independent-harness-<轮次>` 分支提交新的请求 commit R；R 的请求只引用 H，不把 R 自身说成预先冻结的 H。请求示例中的路径由 tester 自定；开发侧不打开或检查其中未发布的用例内容：

```json
{
  "version": 1,
  "mode": "harness",
  "product_source_sha": "<精确产品SHA>",
  "harness_ref": "<预先冻结H的完整SHA>",
  "harness_path": "tmp/independent/<tester冻结入口>.py",
  "recipient_certificate_path": "tmp/independent/<tester接收证书>.pem",
  "harness_timeout_seconds": 900
}
```

这是部署 JSON 请求，非测试脚本。新增实际测试脚本仍须遵守项目 tmp 编号登记。`workflow_dispatch` 待工作流以后经正常保护流程进入默认分支才作为可用入口，不绕过 main 保护。

必要修复后的复核请求可递增正整数 `request_revision`（默认1）；精确产品/harness SHA不因此漂移，先前失败仍保留，不用无变化请求反复重跑。

## 初始条件与中性 context

runner 建立独立 Compose project/数据库 `t44_acceptance`，随机生成256位数据库/队列凭据并以私有文件保存、GitHub mask。只为启动建立一个 synthetic manager 和一个空项目，**没有任务/独立案例**；实际 user/project ID 在 context 中，不能猜 ID。产品迁移仍是独立显式步骤。调度凭据使用真实 CLI，JSON0600，扫描容器只读挂载目录，共享持久 flock 卷。

仅 runner loopback 开放 web18082、只读 SQL13306、AMQP15673；不映射队列管理面板、不购买或访问云/个人服务。SQL新建专用 `t44_audit`，只授目标库 SELECT；控制入口还设置只读事务和5秒语句上限。直接 AMQP 凭据只适用于本次一次性 synthetic vhost，允许 tester 自己的消息操作；它不提供任何业务预期或缺陷提示。

客户端就绪分开核对SQL/AMQP。连接失败仅记录异常类别/数值码、TCP监听状态、Docker实际端口绑定和本项目网络Internal布尔；若实际观察到监听不可达且只连接internal网络，才在**本验收override**增设client bridge并受控重建/复连，保留原观测。鉴权失败或其他网络状态不自动绕过。产品Compose保持原样，绑定仍仅127.0.0.1。

独立 Python 入口无额外参数，通过环境变量 `T44_ACCEPTANCE_CONTEXT` 读取0600 JSON，字段包括：

| 字段 | 用途 |
| --- | --- |
| api_base_url / web_base_url | 同源 HTTP 与前端入口 |
| product_source_sha / bootstrap_project_id | 被测精确提交/真实初始项目ID |
| manager_credentials_file | 私有JSON，含synthetic用户名、口令、会话及真实user ID |
| readonly_database_url | SELECT-only 审计连接，不是应用写库凭据 |
| amqp_url | 本轮真实 RabbitMQ/vhost |
| mq_transport | 本产品镜像默认exchange/queue/routing、隔离拓扑、真实outbox字段映射及AMQP属性 |
| python / control_cli / control_state | 固定中性操作入口和私有状态文件 |
| runtime_metadata | 只宣告runtime-metadata只读命令；不自动采样，完整JSON退出0，不完整退出非零 |
| service_credential | 限定escalation:write的真实bearer签发能力、短TTL和私有文件位置 |
| harness_output_directory | tester主动准备的受限证据输出目录 |
| archive / faults / isolation | 加密取回、控制租期及环境隔离边界 |

Python依赖使用被测产品 `backend/requirements.lock`、`--require-hashes` 安装在独立 venv，含HTTP/MySQL/AMQP/pytest客户端；不安装harness自带未锁定依赖。harness所有入口/辅助材料须在冻结 `tmp/independent/` 内。部署人员不读取未发布的案例、私有结果或 coverage 数据。

## 只读审计、账号和受限故障控制

以下是调用约定，不是案例或断言。运行时 `T44_ACCEPTANCE_STATE` 已设定；harness 可用 context 中的 `python` 和 `control_cli` 构造 argv 调用，SQL/口令通过 stdin，不放命令行。所有操作仅指向本次项目。

```text
control.py audit-sql                         # stdin一条SELECT/SHOW/EXPLAIN，结果仅返回harness
control.py broker queues                    # 当前队列元数据
control.py broker connections               # 当前连接元数据
control.py init-user --username NAME --display-name NAME  # stdin口令，真实CLI初始化
control.py scheduler-scope --project-id ID [--project-id ID] # 受控替换授权scope并轮换
control.py service-credential --project-id ID --ttl-seconds 300 --output-name bearer.json
control.py fault --service rabbitmq --action stop --lease-seconds 60
control.py recover
```

`recover` 每次调用在stdout返回**一个JSON回执**；成功进程退出0，失败退出非零且仍返回结构化false，不输出原始异常或凭据。

| 回执字段 | 含义 |
| --- | --- |
| schema_version / recovery_id | 回执版本1 / 每次调用独立标识，可关联control-events |
| recovery_completed | 仅本次必需操作全部成功才true，不由finally被调用决定 |
| started_at / finished_at | UTC ISO时间 |
| requested_services / restored_services | 固定服务范围 / 对应批次up --wait成功后才列入的服务 |
| paused_services | 实际Compose ps查询到的暂停服务 |
| steps | 逐步名称、实际退出码和执行时间；不需要unpause时needed=false/exit_code=null；未取得命令结果也保留null，不能按0解释 |
| error / failed_step | 失败时稳定错误RECOVERY_FAILED及阶段；控制状态不可用为RECOVERY_CONTROL_UNAVAILABLE |

先查询白名单服务的paused状态，只对确实暂停的服务执行unpause；unpause后按基础服务→应用的依赖批次，只读观测相应已解除暂停服务的运行/健康状态(每批观察预算60秒，单条Docker调用另有超时)，再执行该批up --wait；基础依赖就绪后才等待应用健康。任一必须步骤非零就保留false/真实步骤退出码，不清除尚待恢复的租期。部分服务已恢复时仍可返回整体false。显式、到期租期、最终恢复仍使用相同服务范围与动作；execution中的final_recovery_receipt只代表最终那次，不能代替harness拿到的各次CLI回执。Docker健康/运行状态恢复不代表业务故障场景已通过。

fault服务白名单为 mysql/rabbitmq/api/consumer/scheduler/web，动作仅 stop/pause，租期1–120秒。拒绝任意 Docker命令、删卷、DROP/写SQL、外部地址及系统数据库。租期到期由环境进程恢复，显式recover和finally同样先恢复基础服务再恢复应用，记录控制动作/退出码，不记录 SQL/行数据/口令。恢复失败保留 failure，不以 finally 被调用冒充恢复成功。harness超时终止进程组后也尝试恢复、最后只 stop，不删卷。

`service-credential`使用现有真实 `t44.cli service-token`，仅对本次项目库中**显式提供的项目ID**签发，scope固定 `escalation:write`，TTL60–900秒（默认300）。容器内只读查询实际session的actor/scope/project/expiry元数据后才返回；不会把数据库摘要当可用bearer。省略`--output-name`时真实Token仅返回harness私密stdout；指定时仅在context的受控0700目录内O_EXCL创建0600 JSON，stdout仅文件位置/会话元数据，拒绝覆盖已有文件。该操作绕过环境原始命令日志，公开control-events仅记project_count/session/expiry/TTL，永不记token。此能力支持内部升级接口的既有鉴权，由tester自行决定用例，不预置业务案例。

## MQ中性传输约定

`mq_transport` 来自实际产品镜像的BrokerSettings及broker.py定义，附product_source_sha和definition_sha256。固定4c20f32的Compose只提供AMQP_URL，worker未覆盖exchange/queue；环境不替业务用例制造outbox消息。

| 项目 | 默认值/来源 |
| --- | --- |
| exchange / exchange_type | t44.events / direct，durable |
| queue / routing_key | t44.notifications / t44.notifications |
| quarantine_exchange / quarantine_queue | t44.events.quarantine / t44.notifications.quarantine |
| quarantine_routing_key | t44.notifications，未加.quarantine |
| wrapper.event_id | 真实outbox_events行的id |
| wrapper.schema_version / event_type | 同一真实outbox行的schema_version / event_type |
| properties.content_type / delivery_mode | application/json / 2 |
| properties.message_id | str(event_id) |
| properties.type | t44.event.v1 |
| basic_publish mandatory | true，属于发布参数而非BasicProperties字段 |

wrapper是UTF-8 JSON，取实际outbox行这三个字段，不猜测/硬编码event_id或把外层API Meta版本代入消息版本。context中`properties.message_id`以`source_wrapper_field=event_id, convert=str`表示动态映射；这是描述元数据，实际AMQP属性值应为该event_id的字符串，不能把描述对象直接当message_id。环境能力检查只读核对真实绑定和默认元数据，不构造业务消息，也不提供独立场景预期。

这是方便审计的受限操作接口，**不是针对恶意 harness 的操作系统沙箱**。受信冻结 harness 运行在一次性 hosted runner；它拥有该runner通常的权限。强制取消、runner失联或平台硬超时可能打断finally，须读取实际 recovery_completed，不能假称每次已恢复。

## tester 私密证据的可取回机制

公开仓库普通 Actions artifact 没有“仅tester可读”ACL，因此不上传未审查的明文 harness输出。tester在本地私有目录、`umask 077` 下生成 RSA3072或更强的私钥和自签接收证书，仅把证书加入冻结 H；私钥留在本地，可交互设置私钥口令。证书是加密接收者标识，不是TLS/CA信任声明，运行时要求至少仍有效一小时。

```sh
umask 077
openssl req -x509 -newkey rsa:3072 -sha256 -days 30 \
  -subj '/CN=T44 independent evidence recipient/' \
  -keyout tester-private-key.pem -out tester-recipient.pem
# 只把tester-recipient.pem复制到自己冻结的tmp/independent证书路径；不提交私钥。
```

runner将 stdout/stderr 收入私有目录，不输出到公开 Actions console。另只收集输出目录中固定白名单 `report.md`、`results.json`、`events.jsonl`、`trace.log`；拒绝符号链接、目录、单文件>20MiB或总计>100MiB，其他文件全部忽略。禁止把整个workspace、.env、凭据文件、coverage或私有用例复制到输出目录。stdout可能误含临时凭据，所以**即使加密取回，也须tester本地审查/脱敏后才显式发布**。

部署侧另在归档前写入保留名 `environment-control.log`，仅供tester在密文中取回环境控制失败的原始诊断；harness不得使用该保留文件名。环境诊断不会在harness模式下明文发布。

归档采用 [OpenSSL CMS](https://docs.openssl.org/3.0/man1/openssl-cms/) AES-256-GCM和RSA-OAEP/SHA256。公开artifact只包含 `tester-output.cms` 密文、密文/证书SHA256和环境/控制/退出元数据；`environment-check` 额外允许不含harness内容的脱敏环境诊断gzip。绝不上传明文tar、.env、context、Token JSON、完整workspace或coverage目录。密文保留14天，context明确给出artifact名与时效；runner临时明文随job销毁，**tester须在14天内下载密文**。

本地解密需支持CMS AES-GCM/RSA-OAEP的OpenSSL3.x；本机默认LibreSSL未核验，不假设它可解密。托管Linux能力自检使用OpenSSL3实际加密/解密roundtrip，tester私钥仍须留在自己本地。

```sh
# 由tester自行下载acceptance-<run_id>中的tester-output.cms；root/dev不下载或读取未发布明文。
umask 077
openssl cms -decrypt -binary -inform DER -in tester-output.cms \
  -recip tester-recipient.pem -inkey tester-private-key.pem -out tester-output.tar.gz
tar -tzf tester-output.tar.gz
# 在本地审查/脱敏，之后由tester明确发布报告；不要把解密文件交给开发岗提前查看。
```

环境步骤失败、harness非零、超时、加密失败及恢复失败都保留失败状态。若加密失败，宁可不发布明文；公开 execution.json 记录 archive_error，不能把丢失证据写成验收通过。加密是取回保密措施，不证明案例设计独立或覆盖fault。

## 执行边界

环境check只核验服务和操作能力，不包含独立用例/产品通过判据。独立模式要求tester自己冻结入口和接收证书后才能执行；不得把环境状态、合成加密传输或控制命令成功当成独立fault覆盖。pause/自动租期路径属于可用接口，具体独立用例及覆盖结论仍由tester自己决定并实际运行。

## stdout 精确约定补充（中性输出修订）

容器进度/诊断 stderr 仅写私有环境命令日志，不混入控制 stdout。非零退出或超时仍是失败，不应忽略非空但不可识别的输出。此修订不改变任何产品用例或判据。

| 命令 | 成功 stdout |
| --- | --- |
| init-user | 单个JSON对象，仅 `user_id`，实际整数1..4294967295；严格校验后返回 |
| scheduler-scope | credential-admin 的单个JSON：`session_id, expires_at, credential_written, rotated, previous_session_revoked, previous_session_already_inactive`；无bearer |
| service-credential | 上文定义的JSON；是否含bearer取决于是否指定output-name；只供tester私密读取 |
| recover | 上文定义的单个结构化恢复回执；必须同时检查退出码和recovery_completed |
| audit-sql | MySQL原生批量表格文本（制表符分隔，含列名），不是JSON |
| broker queues / connections | rabbitmqctl原生制表符文本，不是JSON |
| fault | 成功无stdout；退出码仍须检查 |

五次H2控制输出歧义在公开stage02报告原样保留。该修订的合成回归不是独立业务通过；实际托管控制仍须由冻结的独立入口验证。

MySQL `--batch` 成功零行 SELECT 允许 stdout **完全为空**（不保证空结果仍有列头）；非空行有列头及TAB文本。必须先检查退出码；不得将控制失败或不可解的非空文字当空行。已对同系8.4.11客户端两个固定常量SELECT实际核对，未使用任何业务数据或独立用例。

## 同次运行的只读资源快照

可通过已有context中的python/control_cli/control_state显式调用 `control.py runtime-metadata`。该命令无额外参数，不接受任意命令、SQL或观测路径；stdout始终单个JSON。`observation_complete=true`仅表示必需观察取得完整，不是服务就绪或性能通过；任何必需观察缺失时退出非零且返回false、稳定component/error，未知值保留null，不猜默认。调用方可自行在正式负载前后取回私密审阅。run.py仅宣告能力，不自动采集，也不改变既有七命令、产品源、资源或阈值。

- runner：逻辑CPU数、当前进程CPU亲和范围数量、/proc/meminfo总可见内存，以及当前cgroup v2成员可见祖先的cpu.max/memory.max/memory.swap.max/pids.max/cpuset.cpus.effective原值。当前采集器支持Linux cgroup v2；不支持的版本、不可见或缺必需controller时incomplete，不以宿主可见内存冒充容器限额。
- 六服务：先由当前Compose项目 `ps -q SERVICE`取得唯一64hex ID，再以白名单inspect模板只取同ID及project/service标签、Running、HostConfig CpuQuota/CpuPeriod/NanoCpus/Memory/MemorySwap/CpusetCpus/PidsLimit与health interval；标签不符即拒绝，绝不请求完整inspect、Config.Env或health命令。返回compose_project和实际容器ID便于同次前后关联。0/null/空字符串是原始配置值，不代表无限物理硬件；health interval原值也不自动解释成没有探针。
- API：在已验证API容器内，只输出实际uvicorn supervisor数量、从其实际命令解析的workers值、spawn_main进程数量和读取失败数量；不输出PID、argv或环境。数量是采样时值，不据配置猜运行worker数。
- MySQL：只调用现有SELECT-only审计入口的固定 `SELECT @@max_connections`，严格解析该标量；不接受其他SQL或读取业务行。
- Nginx：在已验证web容器执行 `nginx -T`，仅内存投影worker_processes/worker_connections/upstream keepalive/proxy connect/read/send timeout，完整配置及stderr不落盘/不进入控制日志；未显式观察到的directive不补默认。此命令校验当前配置文件，不重载，也不能单独证明最近一次reload的内存配置与文件相同；多位置取值保留列表。
- daemon：只取所选Docker context的endpoint字段并返回local-unix布尔/transport类型，不输出endpoint地址。harness由workflow在runner执行，六服务是同一所选daemon的容器；unix socket仍不足以证明物理同机，不推定底层硬件关系，也不持续追踪每个客户端来源。

已知背景活动包括scheduler基线60秒扫描、consumer与容器健康探针；实际Running和probe interval随快照记录，扫描基线不是本次流量测量。没有持续抓包/负载归因，other_traffic始终unknown，不宣称无其他流量。输出不自动写公开artifact；调用方按独立证据的私密审阅/显式发布流程处理。

参考：[Docker字段格式化inspect](https://docs.docker.com/reference/cli/docker/inspect/)、[Docker资源约束](https://docs.docker.com/engine/containers/resource_constraints/)、[Nginx -T说明](https://nginx.org/en/docs/switches.html)。

## 有界runtime-usage只读快照

按context的python/control_cli/control_state调用 `control.py runtime-usage`，无额外参数；context.runtime_usage仅声明能力，不自动采样。旧runtime-metadata及原命令格式不变。先验证本项目mysql/rabbitmq/api/consumer/scheduler/web各自唯一64hex容器ID与project/service标签、运行且未暂停，再一次 `docker stats --no-stream --no-trunc` 显式传这六个ID。固定模板只请求ID/CPUPerc/MemUsage/MemPerc/NetIO/BlockIO/PIDs；所有原始stdout/stderr仅在内存处理，不进入控制日志。预算是多次调用分别有限：六个服务各有Compose ID查询10秒、inspect 15秒，全部验证后stats另有15秒。整个runtime-usage没有统一15秒总deadline，不能把它表述为总耗时≤15秒；进程启动、解析等也有实际开销。调用方须自行给足覆盖这些验证/采样步骤的超时，整体墙钟由started_at_utc/finished_at_utc实测包围，不能称采样零影响。没有任意命令、容器、路径或SQL参数。

有效调用的stdout是单JSON；0只代表六项观察完整，非零+observation_complete=false代表不完整，不是业务失败/性能判定。验证任一服务失败则不调用stats；stats批次缺行、重复、外来ID或格式错误时全部统计字段置null，不尝试从不完整批次补零或猜值。已验证container_id可保留；未验证身份为null。无stats调用时sample时间为null；执行stats时六项时间同为实际调用包围窗口，失败亦保留。错误仅稳定码，原驱动异常/原stderr不回显。

顶层固定字段：schema_version=1、observation_complete、started_at_utc、finished_at_utc、services、limitations。services固定六个服务名，每项固定字段如下：

| 字段 | 含义 |
| --- | --- |
| container_id / observed | 已验证64hex ID或null / 是否完整取得本次格式化观测 |
| sample_started_at_utc / sample_finished_at_utc | stats调用UTC包围窗口；未调用为null |
| cpu_percent_cli | Docker CPUPerc原字符串 |
| memory_usage_cli / memory_percent_cli | Docker MemUsage / MemPerc原字符串 |
| network_io_cli / block_io_cli | Docker NetIO / BlockIO原字符串 |
| pids_cli | Docker PIDs原字符串 |
| error | 成功null，否则稳定码；失败统计值均null |

完整格式见[成功合成示例](runtime-usage-success.example.json)和[不完整合成示例](runtime-usage-incomplete.example.json)。两者只说明合同，不是真实runner数据。稳定错误白名单：CONTROL_UNAVAILABLE、CONTAINER_ID_INVALID、CONTAINER_ID_DUPLICATE、CONTAINER_SCOPE_INVALID、CONTAINER_NOT_RUNNING、VALIDATION_INCOMPLETE、COMMAND_FAILED、COMMAND_TIMEOUT、STATS_MISSING、STATS_DUPLICATE_ID、STATS_FOREIGN_ID、STATS_FORMAT_INVALID。CLI语法仍由原argparse拒绝不支持的额外参数，不接受它们作为采集目标。

Linux CLI内存会扣缓存，**不是RSS**；PIDs含内核线程，不等于进程数。网络/块I/O是带单位的格式化累计量，不是速率或物理设备耗时；不把这些字符串伪造为精确字节。CPU百分比窗口不等于完整600秒窗口。六样本非原子，单次或前后快照不证明全程峰值、无其他流量或物理同机；采集的墙钟耗时及负载开销不能当作不存在。不回填历史unknown、不自动发布输出，调用方自行私密取回/审查。语义参照[Docker官方stats](https://docs.docker.com/reference/cli/docker/container/stats/)，限制配置参照[资源约束](https://docs.docker.com/engine/containers/resource_constraints/)。
