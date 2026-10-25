# 消息与通知岗位工作日志

## 2026-10-23 初始化（ROLE-messaging-BOOTSTRAP-v1）

- 操作者：消息与通知岗位 AI；实际派工来自总协调，任务文件为 `agents/messaging/TASK.md`。
- 已读取：`AGENTS.md`、本岗 `TASK.md`、`docs/collaboration/team.md`、`docs/collaboration/report-template.md` 及 `specs/sources/` 下三份指定文本。
- 依据：FR-07、AC-07、消息队列故障降级与消费端幂等要求；当前仅为需求设计准备。
- 已确认责任：RabbitMQ 投递/消费、通知去重、故障降级、站内消息列表查询及已读业务；前端负责页面，数据库岗负责唯一一套通知模型，调度岗负责扫描和升级规则。
- 已形成：事件必要字段、稳定业务幂等键、提交/确认边界、MQ 故障与恢复、查询权限等待冻结问题，见 `reports/modules/messaging.md`。
- 已执行命令：`pwd`、限定文件名的 `rg --files`、`cat` 读取指定资料、检查本岗三个产物是否存在、`date '+%Y-%m-%dT%H:%M:%S%z'`。读取成功；三个本岗产物此前不存在；时间为 `2026-10-23T11:47:58+0800`。
- 本轮写入仅为本日志、`reports/modules/messaging.md`、`records/handoffs/messaging.json`；未写产品代码、DDL、共享规范、其他岗位文件或台账。
- 未启动 RabbitMQ、数据库或服务，未运行产品测试、集成验证或独立验收；未联系或读取独立测试岗内容。
- 提示词使用：实际使用 `ROLE-messaging-BOOTSTRAP-v1`；该派工限定初始化范围，关联本轮三份设计记录；未生成新版本、未记录不存在的人工修改。
- 待总协调冻结：事件版本/幂等口径、持久化及事务方案、查询/已读 API 与错误码、MQ 重试和恢复策略；当前草案不得进入联调。
- 记录校验：执行 `python3 -` 内联脚本，确认三份文件存在、模块报告为 48 行、交接 JSON 可解析且必需字段/未实现状态/提示词 ID 正确；这是记录格式检查，不是产品测试。

## 2026-10-23 13:30—13:31 文档岗问取与 M0 提交准备

- 实际询问者：文档岗；实际派工提示词为 `ROLE-messaging-M0-COMMIT-v1`，要求“实际产物路径、业务实现/执行状态、尚未冻结的上下游接口、日志与提示词位置”。随后补充只基于既有交接短答、不开展新设计或实现。
- 本岗已回传的资料短答原文：“实际产物为 agents/messaging/WORKLOG.md、reports/modules/messaging.md（48 行）、records/handoffs/messaging.json。业务未实现，MQ/数据库/服务未启动，模块测试、联调、独立验收均未运行；仅做记录格式检查。未冻结接口为调度升级事件/业务幂等键、后端/数据库原子持久化与统一通知模型、前端/后端列表及已读契约、部署侧 MQ 确认/重试/恢复口径。日志位于上述 WORKLOG；ROLE-messaging-BOOTSTRAP-v1 位于 WORKLOG/handoff 并关联 agents/messaging/TASK.md，实际原始派工在总协调消息；本轮 ROLE-messaging-M0-COMMIT-v1 将随问答与 GitHub 正文留在本岗目录。”
- 重新读取本岗任务/交接及当前协作规则，核实分支 `codex/team-bootstrap`、暂存区为空、已有 HEAD `dbd6d0a0b4a6f706a8f096b0cdb36b0d5ecfcc0f`。本岗旧记录无“当前无 HEAD”表述；首次文件不存在及报告 48 行均保留为当时事实。
- 已执行 `gh issue view 5/6 --repo HJY147/t44-dev-trace --json ...`，确认 #5 为消息岗、#6 为调度岗；未读取测试 Issue 或测试内部资料。
- 已保存并执行 `gh issue comment 5 --repo HJY147/t44-dev-trace --body-file agents/messaging/github-stage-comment.md`，结果：https://github.com/HJY147/t44-dev-trace/issues/5#issuecomment-6358168111。
- 已保存并执行 `gh issue comment 6 --repo HJY147/t44-dev-trace --body-file agents/messaging/github-interface-question.md`，结果：https://github.com/HJY147/t44-dev-trace/issues/6#issuecomment-6358168434；仅询问既有升级轮次/稳定幂等键口径，尚未收到确认。
- 本轮追加两份评论原文；修改者为本岗 AI。提交范围限定为本岗日志、模块报告、交接及上述两份评论，不修改产品代码，不冻结业务接口，不发布审核通过状态。
- `ROLE-messaging-M0-COMMIT-v1` 的作用是记录真实文档问答、GitHub 留痕与阶段提交，关联上述五份产物；不计作业务提示词优化或用户人工改码。


## 2026-10-23 消息应用实现阶段（ROLE-messaging-APPLICATION-v1）

- 总协调明确覆盖 M0 的仅设计限制，基于冻结 v1/D001/D004 授权业务实现；操作者为消息岗 AI，不冒记用户亲改。
- 独立 worktree `.agent-worktrees/messaging`、分支 `codex/messaging-runtime`、base `12f7141026376763086e41a5b4db9ac1e82cfa33`；未使用根索引。
- 读取根规则、implementation-layout、冻结 OpenAPI/persistence-contract、实际 application/api 签名、DB README/delivery 及必要开发测试夹具；未读取独立验收资料。
- 查阅 Pika 官方现行 BlockingConnection 文档及 1.x 实现；锁内同步安装既有 requirements.lock 至本 worktree venv，实际 Pika 1.4.4；未修改依赖锁或 marker。
- 已实现零参 NotificationFacade、Pika 持久拓扑/confirm/mandatory、手动 ACK、坏消息 DLQ、租约 publisher、升级 fallback/普通事件 retry，以及独立 CLI 进程。API 业务门面沿用调用方事务、统一鉴权/幂等/审计，不改任务状态、不建通知模型。
- 实际调度岗来讯确认 outbox event_type=2/schema_version=1 与 ledger/recipient 快照，本岗回复只从权威 DB 事件读取接收人及级别，broker 仅传事件标识。
- DB 对接：GitHub 首次 POST 返回 EOF（失败未当成功）；保存 `persistence-runtime-question.md` 后重试成功，Issue4 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6360793043。根确认将调度 DB 补 recover_confirmed 原子恢复；本岗仅预留注入，不越权补 SQL，也不静默跳过缺失能力。
- 首次本地基础自测 13 通过。首次真实 MySQL 自测 7 个夹具错误：capacity=[] 违反冻结 CHECK；仅修本岗合成数据，失败摘录留于 mysql-run1-failure.txt，未放松约束。复跑 7 通过见 mysql-run2.log。
- 本轮 `PYTHONPATH=backend .venv/bin/coverage run --source=t44.messaging -m pytest backend/tests/messaging -q --tb=short`（配置本地 ignored 凭据路径与 t44_test）24 通过、3 真 Rabbit 因无 AMQP 配置跳过：16 基础/SQLite/fake 通道/进程配置，8 真实 MySQL（含 HTTP 与并发通知 CAS）；见 module-run4.log。
- 局部 coverage 85%（226 statements，35 misses），见 coverage-run4.log；不是全产品覆盖率。Ruff check 通过，CLI --help 实际可运行。
- 真 Rabbit 测试已编写实际 mandatory return、真实连接关闭后 redelivery、重复投递、终态 fallback 后迟到消息及新事件恢复、DLQ；未本地执行，CI 缺 AMQP/DB 直接 fail 不 skip。fake channel 结果不称真 MQ 故障结果。
- 当前缺口：DB confirmed 超时恢复门面尚未进入本分支，默认 worker 依赖此能力，缺失时不能宣称完整运行；真实 Rabbit/托管 CI/独立验收/性能未验证。
- 本轮提示词摘记见 agents/messaging/prompts/ROLE-messaging-APPLICATION-v1.md，实际派工原文来源为总协调消息；关联本岗代码、测试、记录及 PR，不计人工修改条目。
- 额外运行既有 contracts 开发回归：25通过、1失败、1跳过，失败原文见 api-regression-run1.log。test_missing_notification_dependency_returns_real_503 使用默认自动发现组件的应用，消息门面已实现后返回200而非503；已向根报告要求BE显式注入缺失组件维持故障断言，本岗未改外岗测试。


## 2026-10-23 16:40—16:43 恢复接线与实际进程验证

- 第一阶段已本人岗 AI 提交推送 b5a16e6273eaeff5768aa20c977d42fbecbb9aca；draft PR20 https://github.com/HJY147/t44-dev-trace/pull/20 已 attach_artifact。PR首次创建EOF，查询无现存PR后重试成功；无重复创建。
- Issue5实际阶段评论 https://github.com/HJY147/t44-dev-trace/issues/5#issuecomment-6360951760，原文 runtime-stage-comment.md；保留当时24通过与待恢复状态，不重写为后续结果。
- DB真实回复并交付 1602f3597408d3b477dd9ef55a33145565556e12，本worktree cherry-pick 后为76000e2afd726ce065067721e26fd33515ea61bd；未自行修改DB路径。实际默认recover_confirmed已调用，缺失通知补fallback/完整事件仍confirmed/重复恢复为0的真MySQL用例通过。
- publisher增加空闲连接心跳服务与失效channel关闭重连；列表对当前active membership加FOR SHARE至调用事务结束，新增真MySQL验证撤权等待当前读事务结束，后续列表为空。
- DB明确其恢复回归已结束、seed使用独立t44_bench，不与本岗t44_test进程探针争用；未清空他岗或非项目库数据。
- runtime-process-run8.log：实际子进程 `python -m t44.messaging` + 真MySQL + 实际拒绝TCP端口，专属event持久fallback后SIGTERM退出0，输出不含探针AMQP口令；仅证明不可连接时的降级与退出，不证明真实Rabbit投递成功。
- module-run9.log：28通过、3本地真Rabbit未执行；17基础/SQLite/fake/配置、11真MySQL（含默认恢复、通知CAS/撤权并发与真实子进程）。coverage-run9.log局部84%（237语句/37未覆盖）；新增代码后与首轮85%不同，均保留为各次事实。Ruff通过。
- 根通知主应用规模已超5100，后续共同真实重构，不能改计数分母/删故障恢复凑数；本岗不宣称全产品代码规模达标。
- 当前缺口：本机无Rabbit，3个真实broker用例待有配置CI；外岗旧依赖缺失夹具回归仍待BE显式故障注入修正，原失败保留。全产品门禁、独立验收与正式性能尚无本岗结论。
- run10最终复跑1失败/27通过/3本地Rabbit未跑：共享测试库旧pending累计，新event未落入首个默认50条批次；原文module-run10.log保留。仅将该dispatch测试批次设为夹具事件数+1并断言本次普通事件attempts>=1，不改生产批次/不删共享数据，run11复跑28通过/3本地未跑。未把批次未含新event误诊为生产降级失效。
- 根补充要求真实查Actions39925978579/39925904582：均b5a16e6。实际下载run原始ZIP字节、元数据；关键step原字节gzip及全部SHA保存在本岗ci/。两run的真实Rabbit三项均实际通过（contracts integration段三点、fault段两点；coverage全套三点），不是仅“代码已写”。整run失败：BE旧依赖缺失夹具、FE缺test:coverage；coverage 269pass/1fail，不能称全产品门禁通过。细节见ci/AUDIT.md，已真实消息交根。
- 真实Rabbit成功只绑定首阶段b5a16e6；当前DB恢复/心跳等后续快照需新CI。没有改原日志尾空白/换行或覆盖失败，无测试私有资料。


## 2026-10-25 规模结构候选（ROLE-messaging-SIZE-20261025-v1）

- 根实际派工基线396b646，独立worktree messaging-size-20261025/branch codex/messaging-size-20261025；不派生agent，不使用root索引。先写agents/messaging/tmp806_newscope/DESIGN.md的静态调用图和15–50可信预算，再开始固定cloc计数。
- 只读取指定cloc2.10工具（实际SHA与bf592724...d83一致），没有读取其他runtime/credentials或独立资料。计数复用未修改source_count.py.classify，仅归档已提交application文件；基线5875，消息357。
- 真实结构改动：通知三条路径共用当前active成员/项目范围的共享锁查询，复用既有page，计数共用同一范围；Broker四种IO错误清理/脱敏收口，保持connect/publish/get/heartbeat独立错误码与close特殊语义。CAS、收件人、read/handled、owner确认、降级恢复、重试和DLQ未删。
- 为避免格式收益，新逻辑保留原展开调用风格；当前原始diff净11物理行，待提交快照cloc正式确认。没为100目标改私有API成locals/动态dispatch、迁生产代码或制造不必要sharedhelper。
- 首次pytest未指定backend配置而0收集（exit5），before-tests.log保留；补-c backend/pyproject.toml后原17项模块开发用例通过。首次新用例ruff有4个C408，原lint-run1.log保留，仅修本岗测试literal，不放松规则。
- 新806性质/故障22项在未修改396b646的归档backend包上通过（before-properties.log有实际导入路径），候选现有+新用例39项通过/23integration未运行。覆盖9组read/handled筛选、分页与全范围计数、项目拒绝优先级/share锁、4类错误脱敏与清理、False NACK、DB重投及Unicode/StatementRejected死信继承边界。
- 未跑真实MySQL/Rabbit、全CI/云或正式验收，不读取凭据；已有历史通过不外推本候选。调度仅静态只读，已向根交精确跨岗候选，未越权实现。
