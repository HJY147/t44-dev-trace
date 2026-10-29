Agent-Role: backend (AI)
Prompt-Ref: ROLE-backend-ACCEPTANCE-FOLLOWUP-20261025-v1

公开 F08 最小交接后的开发修复候选已经推送：`codex/backend-acceptance-followup-20261025`，准确产品源码 `935ab5b93bea788672c2b4a088c79cfeed848954`（基点 acae31a；协调者声明原产品字节为 C8）。原独立 F08 仍 FAIL，F11 仍 NOT_PROVEN，没有重判旧结果。

问题：有效 developer 无 manager 执行 action7，在批准引用失效时先收到评估/批准 409；源码的原批准失败槽先于 domain 的 state/manager 守卫，遮住了 OpenAPI manager-only 与 D008 不覆盖 state/role 的契约。新代码仅在这个失败槽先执行原发布状态5与既有 manager 检查，再沿原 D008 双失效/单批准失效错误选择；批准引用匹配、任务/请求评估版本与归属等早期检查、其它 action、Runtime 认证/幂等/事务/CAS/审计均不改。没有越权发布成功的证据，也不将本次开发后置条件填作旧独立 F08 已验证。

真实开发证据：新 `tmp/backend/contracts/816_acceptance_followup_20261025.py` 自造合法 HTTP 流程，旧源码4失败→候选4通过；原856必要邻接11通过，15唯一 SQLite 目标，零失败/错误/跳过。含 developer 在当前/过期评估时403、状态3先 STATE_CONFLICT、业务数据全不变、单条持久拒审计和同键重放不增审计。Ruff/format 使用项目配置通过。初始环境缺pytest与旧红保留；旧红长traceback中的自造内存临时token只保留本机0600原件，公开证据为精确脱敏派生及SHA，不发布凭据。

F11方案仅代码阅读：CLI 无 human-token 命令，service-token 为服务身份，不能替代。Settings 最短 TTL60；总协调未来可在获准同一 campaign schema、同准确源码的单独 auth-only ASGI/TestClient 进程以真实 login 签发 human，然后自然过期，不修改/重启冻结 SUT。HTTP JSON 仅 username/password，TTL 属进程配置；本岗未创建用户/token、未接运行数据。

报告及hash/AST/JUnit绑定：`agents/backend/acceptance-followup-20261025/report.md`、`verification.json`，证据另存 `codex/backend-acceptance-followup-evidence-20261025`，源码分支保持935ab5b。请求总协调/审核岗针对准确源码窄审，再组织 MySQL/完整 CI 和新独立复测。本岗仅约4.4秒串行低优先级 SQLite，未运行外部DB/live SUT/全量CI/负载，未改主树、.runtime 或活动C8；原规模超5100仍开放，未新cloc或声称节省。
