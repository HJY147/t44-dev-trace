岗位 backend；Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1（c83后内部设计续派）。

仅提交内部候选specs/changes/contract-validation-read-uow-rfc.md：validateContractPayload的一次普通RC实时鉴权、输入校验及原业务读取合为一个UoW，valid输入后fresh now复核到期。其余17只读、全部写锁/CAS/幂等/审计/outbox和冻结14件不改，不调pool或删Schema/授权。

逐源码核当前两次各4SELECT鉴权+category2/3各1task读，静态8/9/9可降4/5/5、2acquire可降1；预期尚未运行，COM_PING/连接初始化/commit不含在955cursor计数，不推定为纯poolwait。未应用补丁仅Runtime净+7物理行，生产实际0改动；不是减行或正式性能收益。

最初S锁备选经根/审核讨论后撤回，保留原普通读最低语义：各表语句快照、在途读允许完成、撤销提交后新请求拒绝，不能声称全授权原子快照。错误先退出/close主UoW才独立audit。body网络已读，但连接跨CPU校验可能抵消收益。RFC含986/985撤销新旧请求/两身份双时序、到期/拒绝事务专项计划，未编写/运行。审核岗逐字比对无新增设计阻断、根已准入后续实现；本提交先交设计/未应用patch，无生产改动。原controller失败与正式性能失败不改写。
