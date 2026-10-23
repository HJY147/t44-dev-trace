# 原生应用阶段设计 checkpoint

状态：phase2设计/控制器与依赖准备获根ec3e6b0准入；根随后给出修后精确SUT bc5aef9c62393134582affb7a690acb33ac2b833、records/validation/native-demo-source-bc5a-binding.json，并授权设计/871守卫/私密配置与拥有权预检通过后执行有限周期。42243旧快照从未启动应用，原件保留；当前bc5a的92源文件SHA已全部核对一致（44Py/20TSVue），正式CI/专审尚不由本岗宣称。

## 既有边界与新输入

- 延续phase1已验证的NativeBroker，不改其运行源、不重跑无变化的phase1守卫；phase2每次用新的broker目录/Cookie/账号/vhost，保留旧run和失败原件。
- 根已独占建立`t44_native_demo`，19表/18业务表226列、3个synthetic角色、2项目40任务60依赖100记录。只使用显式新`native-demo-20261023/{environment,credentials,database}.json`，均0600；不读admin，不迁移、不seed、不DDL/reset/drop，不扩大app的SELECT/INSERT/UPDATE/DELETE权限。
- `records/validation/native-demo-source-binding.json`与`native-demo-database-preparation.json`是实际资料路径；初次按派工中的decisions路径读取失败已记录，随后按准入正文正确引用读取。
- staging env的PYTHONPATH仍来自初始化0549，只在owner新副本中替换到根最终给出的精确snapshot；原私密文件不修改、不输出其值。
- 保护旧5173/18080、5175/18084、5176、18089、41/42及MySQL13306/PID7980。只操作18088、5178和已准入broker端口；发现占用即失败，不停止占用者。

## 最小控制器接口

`deployment/native/application.py`仅包含部署控制与能力回执，新增守卫使用根预留`tmp/deployment/871_native_application.py`。

1. `prepare-dependencies --source-binding FILE`：验证允许的snapshot/source_files manifest，按锁SHA准备项目内专用venv和frontend依赖副本；不启动网络服务或调用业务。允许先准备已给42243锁，若最终锁变更则换新依赖目录。
2. `prepare --source-binding FINAL --expected-source EXACT40`：必须显式给根最终源，核每文件SHA与44Python/20TSVue计数；新建0700 owner run，复制源与private env，记录controller/runtime/source/lock/rules hash。新broker仅prepare，不start。
3. `run --run-dir NEW_OWNER_RUN`：仅对已显式绑定的final manifest执行一次有限本地能力周期，最后finally停全部自有应用与broker。默认不提供无人值守start，防TTL300到期后继续空跑。

所有命令argv只含路径/公开SHA/IDs，子进程使用参数数组；失败只输出稳定代码与真实false回执，原stdout/stderr保存在项目私密日志，不将秘密或原异常串公开。

## 源、依赖与UI风险

- source binding必须40位提交号，root位于显式`.runtime/native-demo-20261023/source/<commit>`，路径白名单仅backend/frontend/specs contracts/database/deployment；拒绝`..`/符号链接/缺文件/额外被声明的测试或独立路径，逐文件SHA不符即停止。
- 原snapshot不写入node_modules或生成物。owner run复制精确源文件，并在安装/构建/启停前后复核原文件hash；允许的额外文件只有部署overlay、venv、node_modules、build/cache/log/state。
- Python3.12 venv完全在项目0700依赖目录，`uv pip sync --require-hashes backend/requirements.lock`；保存真实锁SHA、安装退出码、`pip check`、实际distribution版本和关键模块导入位置。只设owner env的PYTHONPATH，不改业务锁。
- frontend按原pnpm-lock frozen install到owner依赖副本，Node24/pnpm11.25.0版本核对。原Vite配置硬指18080，不能直接照跑；owner生成的部署overlay导入原配置并覆盖proxy为127.0.0.1:18088、host127.0.0.1/port5178/strictPort、独立cache。原源码/规则/锁完全不改。
- UI直接启动所选副本的Node/Vite入口，避免pnpm额外launcher妨碍拥有权。验证5178 HTML与真实API proxy；是否有完整浏览器业务验收另行标明，不由HTTP200推导。

## 进程与拥有权

顺序：验证final源/锁/私密文件/空闲端口 → fresh broker真实start/inspect → API四worker → 用既有鉴权路由401与synthetic login/API查询核ready → consumer → service credential → scanner → UI与有界观测。

- API真实`uvicorn t44.api:app --app-dir FINAL/backend --workers 4 --host127.0.0.1 --port18088 --no-access-log`；API不启动scanner/consumer。
- consumer与scanner分别采用精确final源的`python -m t44.messaging`、`python -m t44.scheduling --token-file PRIVATE`，只对owner新数据库环境。
- 记录PID/UID/lstart/PGID/命令SHA、期望可执行文件/cwd/source hash；核实际cwd属于已校验owner源。API只枚举已证明自有parent的child PIDs，识别4个spawn workers与resource tracker，逐个登记；不遍历未发布独立资料。
- 停止前重新逐项比对拥有权与源。API先给自有supervisor正常SIGTERM并等待其worker排空；必要清理只给已登记且仍精确匹配的自有PID信号。scanner等当前tick结束、consumer等cycle结束、UI/API排空后才关broker/EPMD。不使用全局kill，不以finally被调用当成功。
- scanner轮换使用新generation记录，旧generation原件不覆盖；任意部分失败保留false，最后按实际逐项报告哪些进程已经停止。

## 最小真实能力周期

- 登录凭据只从根新credentials文件读，HTTP请求体不写公共日志；得到的用户token仅存新0600文件。用实际manager权限查询两个项目ID，并用新库只读查询交叉核对，不猜ID。
- 通过真实final CLI签发新service account/session，显式两个实际project IDs、固定`escalation:write`、`T44_SESSION_TTL_SECONDS=300`与0600新文件；直接核实际session元数据/expiry/scope，不公开token或token_hash。
- scanner使用项目内共享0600flock，保持冻结规则60秒。启动即时tick与随后真实60秒周期应形成至少两次新的持久completed scan_runs；记录started/finished/heartbeat与实际cutoff，不以sleep或PID替代成功。
- 正常scanner产生的outbox交由真实Pika consumer发布确认/消费确认，核真实拓扑与新库outbox/notification的关联、fallback=0和可鉴权读取的站内通知。禁止伪造outbox、直接改业务状态/到期时间或补seed来凑结果；若数据无适用任务则报告实际边界。
- 两次真实周期后，先排空并停自有scanner；新300秒凭据写新私密文件、验证元数据、原子替换稳定文件，再真实revoke-session旧ID，核旧会话已撤销；同源scanner重启后验证新的tick与锁持有。签发/撤销失败不留下无人管理的scanner。
- finally依次停UI/scanner/consumer/API，并撤销本轮service与用户会话，最后停止fresh broker；后置只读核所有登记自有PID/worker已消失、broker端口不再由本轮进程占用。保留数据/原件，不删库/目录。

## 证据和失败边界

公开资料只包含版本/SHA、role、项目IDs、scope/expiry/session IDs、UTC/退出码、计数/关联、地址与拥有权摘要。所有原始输出先留私密；公开前对已知Cookie、AMQP/DB/3登录口令、用户/新旧服务bearer逐字面扫描；压缩内容必须解压后检查，dump不打开/上传。

stage1原始失败与phase2设计、依赖安装、守卫、真实driver/setup失败分目录保留。871只做本岗坏输入/路径/源/秘密/端口/拥有权合成守卫，不是独立用例；本轮不做400并发/600秒、独立验收或云发布，不修改业务、锁、60秒规则或冻结契约。

## run1后小范围设计勘误

run1实际exit1/cleanupfalse保留。两次completed scan真实间隔60.383994秒，16升级事件→16已确认outbox→26正常通知逐事件收件人和scan/UTC已只读关联；应用与broker最后全PID/端口gone是独立后置absence，不能改写原停机回执。

Rabbit4.3.6 JSON的peer_host实际是inet整数tuple数组，client_properties是AMQP typed三元组列表。修正仅严格解码4个0–255整数（排除bool）或8个0–65535 IPv6整数/合法地址，仍要求loopback、精确自有user/vhost与唯一longstr Pika产品；未知形状拒绝。同一原始JSON在历史427b实现真红、修正真绿，不重启来猜DTO。

shutdown默认等待分支实际报告远端成功退出后CLI code_server badarg并超时exit-15；随后ps/getpgid观察竞态使broker最终回执未写，原cleanupfalse保持。固定官方v4.3.6 shutdown源码证明`--no-wait`同样调用`rabbit:stop_and_halt`终止整个VM；新wrapper仅改该标准参数，独立保留精确自有PID退出/EPMD空/退出/端口观察，CLI非零仍false。进程在ps与getpgid之间消失只表示absent，不授权任何信号。既有phase1 run2历史仍绑定7e942，不挪用新实现。

根授权第二次fresh有限周期：新Cookie/user/vhost，复用同一未reset的新demo数据；显式`prepare --prior-run`核同源owner前run和私密只读关联hash，绑定既有16个eventIDs。二轮核这些真实ID/收件人/鉴权通知可读，明确不声称二轮新publish；新轮继续两真实60秒completed扫描、受控凭据轮换与完整正常清理。不得SQL改业务/去重或补seed来制造新消息。
