# ROLE-database-LIVE-VERIFY-v1：本轮实际派工

来源：总协调真实续派消息；操作者为AI数据库岗，不记为用户亲自改码。

> ROLE-database-LIVE-VERIFY-v1：独立测试明确确认三批400VU/600s已全部停止，最后10:52:33Z，安静窗口现在结束。请恢复本机真实验证：先按你956的专库保护要求，在已创建授权的t44_review迁移，逐项实际改变保持同名的索引/FK/CHECK并验证拒绝、每例恢复、最终checker/repeated migrate正确接受，完整记录每次实际SQL目标/结果/原始失败（不泄露凭据）。再在明确新隔离t44_seed_verify_v2库验证新版seed默认40/6000/9000/15000真实MySQL及各约束/摘要/重复拒绝；该新库root马上创建授权，先做review库可并行root建库，不碰dev/acceptance/perf/旧seed_verify。你94b已合根，当前root全产品还含BE3ee和FEb485；可同步root后做，不能削弱956/957/975断言。完成必要范围即交接，不无故重复扩大测试；C-P4只在真实结果后标技术关闭，准确新root reviewer仍需复审。正常本岗worktree/报告/handoff/prompt/Issue4/PR17阶段commit。新测试脚本如需编号从955先报备，原956/975可追加。代码规模仍超限，不改变计数或为填缺口破坏结构。

> 新t44_seed_verify_v2已真实创建（existed_before=false）并授予同项目app@127.0.0.1，receipt records/validation/seed-verify-v2-database.json；仅该新库及专属t44_review可写，其他库不动。根最新完整合入43f51570e62e3160f7995c45bdddaf2f123242b3。严格原cloc实际stage7=5866，--require-range exit1，records/metrics/source-count-stage7.json；仍超5100，不改口径。你做必要live验证即可，不再为数字额外破坏结构。

执行范围：复用本岗956/975追加可复现保护与证据，不新增测试编号，不读改审核957或独立私有资料。仅两个明确新隔离项目库可写；原始失败与恢复操作均保留。
