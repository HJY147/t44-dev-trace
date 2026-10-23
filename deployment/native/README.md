# 项目内 macOS 原生运行设计

状态：设计与依赖能力准备，尚未启动 RabbitMQ、API、consumer 或 scanner。此目录属于部署岗；不改变 Docker Compose 技术基线，不替代云部署或独立验收。

## 准入与保护对象

- 本轮基点 `275dd3e`，worktree `.agent-worktrees/deployment-native`，分支 `codex/deployment-native`。最终应用必须由总协调另给精确 commit 后绑定；不得把当前部署设计 SHA 当成最终 SUT。
- 原用户预览 `5173 → 18080 / t44_demo_v11`、既有隔离预览 `5175 → 18084`、MySQL `13306 / PID 7980` 均不可停止、重配或复用其业务数据。不检查未发布独立资料。
- 只在项目根 ignored `.agent-worktrees/.runtime/` 创建运行目录、私密凭据、日志、状态和本地依赖。不修改系统配置、全局 PATH、HOME/home/CODEX_HOME，不安装全局软件，不租赁/付费/外发。
- 依赖准备来自根 `records/decisions/local-mq-runtime-preparation.json`；下载、首次 configure 失败及 attempt2 原始回执由根保留。部署岗不并行重编译。
- 启动须等总协调审查本设计并给出准入；数据库的新 schema/user 由根协调数据库职责实施，部署岗不读取旧环境的秘密文件来猜连接信息。

## 两个独立环境

| 项目 | 原生演示候选 | 未来隔离 v3 |
| --- | --- | --- |
| 目标 | `t44_native_demo`，2 项目 / 40 任务的小数据演示 | 根冻结后重新分配，UI 与性能各用新库 |
| API / UI | `127.0.0.1:18088` / `127.0.0.1:5178` | `18086` / `5177` 仅候选预留，未绑定 |
| Rabbit AMQP | `127.0.0.1:25674` | 新节点/数据目录/端口/vhost，由根确认 |
| EPMD | `127.0.0.1:24369` | 不共享演示 EPMD |
| Erlang distribution | `127.0.0.1:35674` | 新分布式端口 |
| CLI distribution | `127.0.0.1:45674–45683` | 新 CLI 范围 |
| 节点 / vhost | `t44_native_demo_<runid>@localhost` / `t44.native.demo.<runid>` | 按目的新建；不克隆演示业务结果 |

以上未监听、未做可用承诺。每次启动前只检查指定端口是否空闲；发现占用即失败，不杀占用者。AMQP、distribution 和 EPMD 都必须显式 loopback，不能只限制 API/AMQP。不开 management、Prometheus、stream、MQTT、STOMP 等额外插件/端口。

## 固定依赖与来源

- RabbitMQ `4.3.6` generic UNIX archive；SHA256 `aa0ff5de9ff0136dc42eba21dc3a973cc3b286437cdba0f45556e890509c1614`。
- Erlang/OTP `28.5.0.7` source；SHA256 `ddf17db6d3e9b7a7cfac0d72238ddc8ea040fedc5e3dfad82fc90675319d6c93`。精确 Rabbit 4.3.6 官方兼容表列 OTP 27.0–28.x；网页正文另外描述更新版本的 fully-supported 状态，不把二者混写。
- 原包路径和编译 prefix 取根允许的 `.agent-worktrees/.runtime/native-mq-20261023/layout.json`，启动前重新核文件/版本。实际单次非分布式 probe 证实 OTP28、ERTS16.4.0.6、crypto/ssl 和 OpenSSL3.6.2，见本岗 `native-validation/erlang-capability.*`；这不证明 broker 可启动。
- Python 3.12 项目内专用 venv，只按最终 SUT 的 `backend/requirements.lock` 做 require-hashes 安装；不得修改锁。记录 Python、锁 SHA256、实际安装清单与 `pip check`。Node/pnpm/前端构建按最终前端门面，UI 不得随代码漂移。
- 官方依据与逐页/源码 SHA：`agents/deployment/native-validation/official-source-map.json`。主要链接：[版本表](https://www.rabbitmq.com/docs/4.3/which-erlang)、[generic UNIX](https://www.rabbitmq.com/docs/install-generic-unix)、[OTP28 auth](https://github.com/erlang/otp/blob/OTP-28.5.0.7/lib/kernel/src/auth.erl)、[OTP28 filename](https://github.com/erlang/otp/blob/OTP-28.5.0.7/lib/stdlib/src/filename.erl)、[OTP28 init](https://github.com/erlang/otp/blob/OTP-28.5.0.7/erts/preloaded/src/init.erl)。

## Cookie 必须先解决

1. 不使用 `-setcookie SECRET`、`--erlang-cookie SECRET` 或带秘密的 shell/命令行。OTP28 没有本设计能核实的独立 `-cookie-file` 参数，不发明参数。
2. 已实测 `ERL_FLAGS=-home 项目路径` 会与 launcher 自动加入的原 HOME 产生两份 `home`。OTP auth 对这种结果走 fallback；Darwin 的 `filename:basedir(user_config,"erlang")` 又采用 `Library/Application Support`，不读取 Linux 的 `XDG_CONFIG_HOME`。因此不能采用这两条路径。原始成功/不适用结果保留，不写作 cookie 隔离通过。
3. 已执行两次有明确变化的非分布式 early-init probe：首次 args_file 嵌套引用/UTF8表达式词法失败；改用ASCII codepoint路径、无空白/引用的表达式后，词法修正但 `erlang:set_cookie/1` 真实抛 `distribution_not_started`。OTP28 auth 只在auth进程已存在时接受setter，因此单纯前置eval不能作为可用方案。两次原始失败/stdout/stderr/hash和受限dump定位均保留，dump不解析、不提交。
4. 提交根审查的下一步候选（尚未运行）：在 `ERL_AFLAGS=-args_file 项目内cookie-init.args` 中用标准 `-nocookie -sname 精确唯一节点` 令kernel先初始化auth，再执行只从0600文件读Cookie的前置eval，之后才进入Rabbit boot/CLI escript。Rabbit4.3.6 prelaunch_dist L18–30显式接受已经运行且同名的节点；CLI distribution L87–91接受already_started，未传cookie option时不覆盖已有Cookie。该方法需要loopback分布式启动，超出此前非分布式probe授权，必须由根准入后真实认证验证。设Cookie前存在短暂nocookie阶段，只能在专有loopback EPMD/分布式端口上进行，不开放AMQP直到后续Rabbit boot；不能宣称已经解决或已经安全鉴权。
5. 不更改官方auth源码或用户家目录，秘密不进入参数文件/argv/环境；标准args文件仅路径与读取表达式，真实Cookie只存项目0600文件/进程内存。若根不准入受控分布式候选则明确阻塞broker部分，继续其余部署资料。Rabbit4.3.6 仍有 deprecated `RABBITMQ_ERLANG_COOKIE` 环境覆盖，但其源码可能 debug 记录环境/context；不以该方式作为当前首选。所有 Rabbit 日志禁止 debug，秘密日志仍归私密目录，不直接上传。

## 目录、账号与最小权限

每个 runid 使用排他新建 0700 根目录，含 `config/`、`secrets/`、`data/`、`logs/`、`state/`、`receipts/`、`tmp/`。拒绝符号链接、越出项目路径、目录属主不符和组/其他用户权限。Rabbit 显式设置 config/advanced config/env conf、Mnesia/Khepri、quorum/stream data、feature-flags、enabled-plugins、PID、log、crash dump、临时目录；不用官方包目录的默认共享 var，也不使用用户默认 cookie。

- Cookie 随机至少 256 bit，0600、排他写入，只供本节点与本岗 CLI。运行中不轮换 cookie；计划轮换先停本环境所有 Rabbit 客户端和节点，再同时切换文件后重启，旧文件归私密保留/销毁策略，不能覆盖运行中的单端。
- AMQP 用户和口令每环境随机生成。首选开机加载项目内 0600 definitions：只有新 vhost、新用户、无 tags、权限只覆盖 `t44.events`、`t44.events.quarantine`、`t44.notifications`、`t44.notifications.quarantine`；采用官方 SHA256 salted password hash，不在公开 config 放明文。启动必须核实无默认 guest、新 vhost 生效后才能启动 consumer。definitions 功能/密码格式须在服务前完成精确版本源核对。
- DATABASE_URL/AMQP_URL 保存在独立 0600 JSON；launcher 解析 JSON 后只注入必要的业务子进程环境，不 source shell 文件，不打印值。公开回执只写路径类别/权限/目标库名/vhost/角色/版本等非秘密。
- MySQL 只连接既有 127.0.0.1:13306，新 demo schema 与专用最小权限用户由根明确提供；不更改服务器/PID7980、不运行 drop/reset、不清空现有库。

## 应用进程与凭据

| 进程 | 真实入口 | 主要依赖 |
| --- | --- | --- |
| API | `python -m uvicorn t44.api:app --host 127.0.0.1 --port 18088 --workers 4` | 最终冻结源、Python锁、新库；不在 API lifespan 启动 worker/scanner |
| consumer | `python -m t44.messaging` | 同源代码、同新库、私有 AMQP vhost |
| scanner | `python -m t44.scheduling --token-file 私密JSON` | 同源代码/规则/库、service会话、项目内共享 flock |

全进程 `PYTHONPATH=<最终SUT>/backend`，以冻结目录为 cwd；记录 git commit 和关键源文件 SHA，不读取/更改业务源码。API/consumer/scanner 使用同一升级规则资源的实际 hash，规则 `scan_interval_seconds=60` 保持不变。

scanner 凭据必须经真实 `python -m t44.cli service-token --name ... --project-id ... --token-file 新路径` 签发；project IDs 来自该新库初始化，不猜 ID。`T44_SESSION_TTL_SECONDS=300`，只设 `escalation:write`，文件 0600、目录0700，不输出 bearer/hash。记录 session ID、scope、project count、expiry 与签发入口。

轮换先等 scanner 当前回调排空并停本环境 scanner，以新私密文件签发、验证元数据/expiry、原子替换稳定文件、通过真实 `revoke-session --session-id OLD` 撤销旧会话，再启动同源 scanner。初次 60 秒演示在300秒TTL内完成；长期运行必须在 expiry 前主动轮换，签发/撤销失败保持停机并返回 false。不得修改业务默认 TTL 或放宽 scope。新旧服务会话的公开回执不含 token/hash。

## 拥有权、启停与回执

所有启动由 `subprocess` 参数列表完成，无 shell。每环境写公开 manifest（部署脚本SHA、SUT SHA、依赖SHA、目的/库/端口、角色）和私有进程登记（PID、PGID、UID、启动时间、可执行路径、命令指纹、日志路径）。启动新 session，使信号只作用于本环境进程组。

顺序：只读预检 → 新目录/配置 → 自有前台 EPMD → 自有前台 Rabbit → 受限 CLI 实际 readiness/listeners/vhost/权限 → 根准入的新库初始化 → API → consumer → 签发 service token → scanner → UI。每步超时、退出码、UTC、唯一 receipt ID 与 needed 字段独立记录；失败不改写前次回执。

停止：先 UI/停止接入，scanner 等待回调，consumer 等待当前 cycle，API 排空；经精确节点 `rabbitmqctl shutdown` 等待 Rabbit 退出；确认自有 EPMD 无节点后停止其自有进程。停止前重核 PID、UID、启动时间、路径、PGID，无法证明拥有权即拒绝信号。不使用 pkill/killall、不向旧环境端口/PID发信号，不把被调用等同于成功。超时/部分恢复仍保存 `success=false`，必要强停也必须受同样拥有权约束并显式记录。

## 根准入后最小验证计划

1. 依赖 probe、锁安装、无冲突/路径权限/源hash等能力检查。单次 Rabbit 启停先核本节点、实际listener地址/端口、随机用户/vhost、无 guest；不是业务验收。
2. 新 demo 库只用批准的迁移/初始化/seed 门面生成 2 项目40任务。API 401/真实登录/项目任务查询，保持冻结鉴权和 API 契约，不新增 health 端点。
3. 启动真实 consumer/scanner；从新库的正常业务/扫描产生最小通知，核 outbox确认、AMQP实际绑定、真实消费落库，并通过已鉴权 API读取。消息只通过现有发布门面，不伪造 outbox或直接改状态。
4. 调度启动本身会即时 tick；另等待至少一个真实60秒周期，分别记录两次持久 scan_runs/heartbeats/完成状态与实际调度UTC间隔。进程存在或 sleep60秒均不能代替周期扫描证据。没有可升级任务时只声明扫描能力，不伪造通知成功。
5. 验证本环境 scanner 停启与service token轮换；操作前后记录自有进程/端口。上述是部署演示自检，未跑400并发/10分钟，不构成AC-07或独立fault/性能通过。

后续供隔离岗位的材料只能由根从中性环境信息白名单生成：精确SUT、入口、库/端口、受限账号和能力；不包含本部署日志、开发发现、预期结果或私密 Cookie/Token。UI/性能环境必须重新建库和vhost，不能把本demo结果注入其中。
