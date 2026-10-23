# 实际派工与追加原文

发送者AI总协调，执行者database AI。不是用户亲自改码，也不是事后优化版提示词。

> 开始ROLE-database-RECOVERY-SEED-v1，前端已释放槽位。根整合12f7141含你a83，前端新head bd13414b92ac56faea010463b03ab74b2a01e52c暂不需merge。你继续自己干净树/PR17。首要马上处理MQ实际Issue4 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6360793043：OutboxStore.recover_confirmed(*,confirmed_before,now=None,limit=100)->list[dict]。必须在同event锁内重新核recipient vs通知集，仅真缺失才补fallback并status3→4；正常完整消费不改status、不算恢复，迟到consumer已完成不误标，老的完整confirmed不能占候选limit饿死后续缺通知。保持冻结DDL不变、Rows/SQL责任你负责，consumer/fallback锁序一致。先实现+真MySQL并发回归+小阶段commit/push，把SHA+签名直接给MQ/root，不要等seed才交。
> 然后实现生产可复用seed_demo，root/BE CLI已有seed接线预留请实际与代码确认。约40projects/6000tasks/9000同项目DAG依赖/15000reviews+decisions，覆盖7态有代表性的分布、版本/证据/决策轮次/approved指针一致，当前active任务前驱已交付；人力计划容量/四视角预案/八段十项证据要有效，不能靠无效JSON填数量。全为明确合成演示夹具，证据引用标为synthetic，不能假称真人review/真实交付。请在专用新空t44_bench库跑真实生成和一致性核验（你可migrate该库，root先保留现在授权你此项目库；不要动acceptance或清空dev/test）。默认重复seed应拒绝/可幂等且不覆盖已有数据，密码只收hash，不输出/存明文。productionseed函数供CLI/压测使用，返回统计与种子/version/hash重现信息；大批量使用绑定参数/batches，不一行一事务。需要review-template或规则hash从当前真实配置/CLI参数取，不编造全0代替。
> 规模现已使用标准cloc2.10：整合12f7141（旧FE+未加完整MQ/扫描/seed）应用code4330；新FE增约512，完整可能超5100。请优先真正必要功能，识别当前仅为早期基础兼容保留且生产无人调用的CoreGateway/TableBinding、可选IdempotencyStore等重复代码；若确实仅测试依赖可移除冗余并将原安全/事务断言迁到真正RowsGateway（保持断言与覆盖意图，不为行数删功能/弱化测试）。不得minify、靠改格式/统计范围凑行数，先功能正确，最终共同做有依据重构。记录真实缺口/失败，必要测试后别刷次数。你已有CI双环境fixtures请保持不skip。完成每阶段自己commit/push PR17、Issue4真对接，给SHA/统计/环境/命令/未做项后释放槽位。禁止独立testing资料/联系，容量恢复文件不换模型。

实际公平性追加：
> MQ已观察共享t44_test大量旧pending会让仅首批50不含新event。不要仅凭夹具叫生产bug，但请做一个无网络的真MySQL可复现公平性案例：普通event失败retry next_attempt_at推进，有限batch、旧ID反复到期时，后来的升级event应最终被claim；当前claim pending默认id排序可能循环旧低ID。合理实现可按next_attempt_at,id（leased按lease_until,id）让重试排到队尾/就绪时间顺序，或分级优先，但先测真实反例、保持锁序和SKIP LOCKED/lease fencing、不改DDL/弱化测试；若证实就做小修复并给MQ实际SHA。优先不拖seed。

实际租约语义澄清（按此执行，不新增拒绝）：
> CoreGateway/TableBinding与可选IdemStore清理按实际无人生产调用推进，原安全/事务断言迁移保留。租约请先按冻结语义分清：主事务始终持有idem行锁，过期本身不能让第二worker并行；冻结要求提交前核owner_token，接管变token才fence旧worker。仅观察“过期但无人接管仍提交”不一定是缺陷，不要自动变更为租约一到立即作废。请把真实竞争反例/原条款给BE/root再定，避免为不同设计偏好加新业务拒绝。新owner已接管后旧token必须拒绝，这是必须验证的安全属性。

产物对应：1602f35恢复、8b60b71公平性真实反例修复、9aeb697生产seed/批量Rows/冗余清理及模块验证；后续文档只归档真实结果。改进理由是来自MQ实际接口缺口与总协调真实公平性审查，不构造虚假的同prompt六版或人工经历。
