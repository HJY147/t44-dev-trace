Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-REPAIR-839-v1

公开839发现后的后端准备与最小候选：先ca18de9范围、6c1a00b设计，源码5cc856d6fa94b1fdde32605543b53822f9747f00（branch codex/backend-performance-repair-plan，基root6d02/C应用），未合入/未部署当前云C。

唯一生产改动为Workflow按纯域实际需要加载依赖：START/REWORK/UNBLOCK回DEVELOPING保留，空前驱不发IN空集SELECT；BLOCK/其它不消费该上下文的命令不做业务层依赖读。Runtime图边/项目X/成员S/有序任务X完全不动，3次实时auth/2UoW、原版本/角色/证据/D008错误优先、CAS、成功audit/outbox/COMPLETE及拒绝退出后独立audit保留。合法数据前提与删除无用途SELECT后的故障触发点差异在design.md明示。

旧C上3个新真实SQLite/TestClient+SQL事件结构目标3红，不称业务漏洞；候选后23个目标绿（含未改原859全部前驱交付），另2个受控反激活持久边界+未改原85611共13绿。36个不重复开发目标/0失败或跳过，Ruff按原backend配置绿。首次工具配置误选失败保留。实际任务/依赖SELECT：BLOCK 4/1→3/0，UNBLOCK回pending 4/2→3/1，START空集4/2→3/2，仍含原Runtime锁前缀。SQLite不证明MySQL锁/竞争，计数不证明延迟收益。

精确cloc原固定工具/口径计6316，净+6，超5100为1216；云C原6310/超1210历史不变，没有可信1210行等价删除方案，不压行/改分母/删安全或功能。15冻结hash全匹配。product40087756354首次状态in_progress，完整CI和独立源码复核待项。

具体DB对接：现成RowsGateway已经足够，本候选不要求改全局empty-IN/SQL/池/DDL；已与DB owner确认其离线838配方不是本业务/RC/收益证明。下一阶段必须先由root/部署取得同次两层upstream与资源/DB锁字段再判断502；不得直接调timeout/pool/worker/去鉴权。仅指定839公开MD核SHA，未读其他独立材料/未向tester发送开发信息，没有外部HTTP/SQL/服务/云/负载运行。

报告与所有本岗原件：agents/backend/performance-repair-839/report.md、design.md、validation.json、dependency-before/after/adjacent.log/xml。作者/改码/开发测试为后端AI；当前仅分支候选，不取消原公开失败、不声称600秒性能或整体验收通过。
