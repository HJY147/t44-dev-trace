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
