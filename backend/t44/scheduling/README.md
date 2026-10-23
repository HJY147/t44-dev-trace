# 扫描、升级门面与进程

基于 D001 三级窗口、D004 与冻结 v1；`EscalationFacade()` 为 API 零参组件，三个方法 `rules(g,c)`、`list(g,c)`、`create(g,c)` 返回冻结 `data`。create 不提交 UoW；Runtime 统一服务认证、幂等认领、任务/成员锁、审计、finalize 的 audit_id 和完成快照，202 只代表可靠提交。

`load_rules` 读取唯一 JSON 配置，校验冻结 EscalationRule（正整数 version、selection、显式起止/包含边界、priority、recipient_kinds、effective_at/decided_by），级别和优先级不可重复，窗口必须有效。解释器按最高匹配 priority 工作，没有固定三级 switch。默认仍只有采用的 24h/到期/24h 三档、60 秒。`select_window` 用 `now-planned_end` 避免年末加 24h 溢出，时间接受 UTC-aware datetime 或最多六位小数 UTC ISO 文本、1000–9999 年；不截断超精度。

配置的 decided_by=1 沿用冻结契约的**合成示例身份**，不声称数据库 ID1 就是实际用户或有人逐条批准配置例值；effective_at 对应 D001 采用时刻。正式部署须由初始化责任岗核对/记录实际身份映射。测试临时配置则明确映射本测试新建的合成经理 ID，绝不作为人类审批证据。D001 阈值由用户采用，配置结构及此示例映射为 AI 技术选择。

升级事务重新检查服务 scope、state1–5、expected_version、schedule_version、rule_version 与当前窗口；阻塞不停表，已交付/已回滚拒绝。快照 owner 与全部 active 经理（临期仅 owner）并去重。outbox(event_type2)、ledger、task.version/escalation_count、Runtime 审计/幂等快照同一事务；硬键仅 task/schedule/level。业务重复仍检查当前版本，返回 created=false 不加计数/版本；唯一冲突用 savepoint 回滚临时 outbox 后回读。事件与 scan_runs 均保存完整快照及原始 UTF-8 字节 SHA-256，不用 JSON 重排后的 hash 冒充原文。历史规则从持久扫描快照读取，配置原/新及操作者记录在本岗 application-rule-change.json。

`Scanner` 调用实际 `Runtime.execute(Call, validate_call)`，不造 JWT 或第二套事务。服务 token 的 project_ids 先经 Runtime 认证，扫描只处理其范围，每次升级再由 Runtime 重验会话/权限。ScanStore 提供 UUID run、固定 cutoff、keyset 页、游标/心跳/计数；确定成功、业务重复或已不符合后才推进，未知失败保留 running 供恢复。提交后崩溃但未写游标时，按 ledger 原 run UUID 在重扫推进时补计一次创建。run UUID 统一标准格式，避免大小写使计数出错。

周期 tick 恢复当前原文 hash 下心跳超过120秒的最多100个旧 run，再新开本轮；使用已确认 RowsGateway 的 hash+heartbeat 谓词在 LIMIT 前筛选，避免其他/旧配置记录阻塞恢复队列。不同原文的历史 run 不被静默改成新规则；可用原配置显式恢复或由运维审核处置。新 run 会从0重扫，业务唯一键保护旧升级。查询/升级与 checkpoint 是分开的真实事务，不声称一次 HTTP 就与游标原子提交。

初始化服务凭据使用后端现有命令（PROJECT_ID 必须是真实授权项目；此处是命令说明，非已执行的生产初始化）：

```sh
PYTHONPATH=backend .venv/bin/python -m t44.cli service-token --name scheduler --project-id "$PROJECT_ID" --token-file /private/scheduler-token.json
PYTHONPATH=backend .venv/bin/python -m t44.scheduling --token-file /private/scheduler-token.json
PYTHONPATH=backend .venv/bin/python -m t44.scheduling --once --resume-run "$RUN_UUID" --token-file /private/scheduler-token.json
```

环境为 `DATABASE_URL`/匹配 `T44_DATABASE`；token 文件可由 `T44_SCHEDULER_TOKEN_FILE` 提供，必须为私密 regular file（无 group/other 权限），每次调用重新读取以支持轮换；不打印 token。`--once` 执行真实扫描并输出持久统计；`--resume-run` 必须已存在且配合 once。`--rules`/`T44_ESCALATION_RULES` 可提供已采用配置。启动/once 配置或扫描错误退出1，成功返回0；定时回调失败由 APScheduler 记录并保留未完成 run，不能据进程仍在就声称扫描成功。

进程显式构造 BlockingScheduler：UTC、60秒默认、coalesce、max_instances=1；SIGTERM 等待运行回调退出。导入/API 多 worker 不启动 timer。单机用 flock（默认临时目录内按库命名，`T44_SCHEDULER_LOCK_FILE` 可指定）防同一锁路径的重复进程；单机 Compose 必须只运行一个调度服务，若分容器启动须共享锁文件路径。它不是数据库分布式租约，max_instances 也不是跨进程幂等；持久唯一约束兜底。

规则加载 O(C+R log R)，单纯判定 O(R)；每页 B 个候选，内存包含 B、配置及最大收件人集合。实际每次 create 还包含配置校验、收件人展开及数据库/审计/幂等调用；DB 索引查询、锁争用和网络代价没有被说成 O(1)。未做400并发/P95或产品压测。

验证：`PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/scheduling -q`。本机另显式设置 T44_SCHEDULER_TEST_CREDENTIALS/T44_SCHEDULER_TEST_DATABASE=t44_test；CI 必须给真实 DATABASE_URL/T44_DATABASE，缺配置 fail 不 skip。107项通过，其中22项真实MySQL8.4.11/ASGI-HTTP/CLI验证，其余含保留的77基础用例；实际进程突然退出后用正式CLI恢复20项、并发CAS、硬去重/savepoint、改期、终态排除、blocked计时、104收件人、原子回滚、冻结GET/202均有证据。规则扩展实验只变一个临时配置、解释模块不变，未将实验第四级启用到生产默认值。

仅本模块覆盖率83%（357语句/86分支；实际CLI子进程未汇入覆盖统计）；原始失败、XML/覆盖数据在 agents/scheduler/application-*。1项 CI 环境入口在本机真库通过，不冒称GitHub托管CI结果。消息通知 DB fallback 使用数据库岗真实门面已验证；本机无RabbitMQ网络，未做真实MQ、前端全链、独立验收或全局代码规模/覆盖率达标声明。
