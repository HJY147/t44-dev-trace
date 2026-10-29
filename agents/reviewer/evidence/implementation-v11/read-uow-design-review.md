# validateContractPayload单UoW候选限定设计意见

Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-V11-IMPLEMENTATION-v1。

本岗已静态读取后端尚未应用的specs/changes/contract-validation-read-uow-rfc.md，SHA256 **8cdfc9b29bf7ed36022ef54d6d3dac4df8b03f06228cdf22da9c939b827d818a**，及agents/backend/drafts/contract-validation-read-uow.patch。依据生产4c20的Runtime/Identity/UoW/Rows/API，未编辑产品、应用patch或运行候选。后端随后正式提交设计-only父节点3187bc6615a821f1123ef10f64d99b7a39a9862d，RFC内容hash不变；总协调已准入该候选实施，实施源码另轮复审。

限定结论：**无本轮设计阻断，可交总协调决定实施准入；不是产品审批或性能通过**。候选仅validateContractPayload：同一自有UoW中普通RC authenticate→validate→fresh now到期复核→原dispatch，with退出后原status/wire返回。原try/except在with外，Rejected/PersistenceError先rollback/close后才独立拒绝审计；全部写、claim、幂等、锁、outbox、其他17只读/login/logout路径保持。

成功8/9/9→4/5/5 SELECT及2→1次acquire是源码可推导的预测，尚未实测；COM_PING、连接初始化SET、commit/rollback和poolreset不在before_cursor_execute账本，不能换算确定往返总数或延迟收益。补丁8增1删、净+7物理行，不属于规模减量。连接跨本地JSON/Schema校验CPU持有，可能抵消并发收益，必须同源实测。

撤销提交后新请求仍实时数据库鉴权并拒绝；每个RC SELECT各自语句快照，不声称跨表原子授权点。已在途读鉴权后允许完成，取消第二次普通鉴权会少一次观察中途撤销的机会，RFC已明确此语义。新鲜时间检查仅保证复核点有效，不保证发送瞬间不跨到期；初始auth仍先于输入错误，validate已失败时原参数错误优先。users.active仍首次检查，未来新增账号停用入口须重新审查。

曾提session/member S锁后，经根协调与本岗指出冻结仅写路径强锁线性化，收敛为默认无锁；应保留这一真实讨论，不说发现安全漏洞，不说用户亲改。若将来又增加锁，必须另审session→project→members→tasks，不可在member后追加project锁。

实现后最少需要：三category冻结响应及零成功写、真实SQL/连接计数；session和无受保护任务reader成员两种撤销的“先提交再新请求”与“旧读已鉴权暂停期间撤销真提交”两时序；明确允许旧读完成且新请求拒绝；非法JSON/壳/候选、服务主体/撤销/过期优先级；fresh now跨期；主UoW已关闭后拒绝audit独立Session持久化与audit失败503。事件屏障证明时间，不靠sleep推断，且不读取独立用例。后续新源CI/必要定向MySQL及协调短对照完成再复审。
