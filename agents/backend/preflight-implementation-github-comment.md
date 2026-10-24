Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

A实现及caller窄修正已在本岗工作树完成，待产品checkpoint和精确CI；仅runtime.py生产改动，B/C与14冻结文件保持。新写prepare共用authorize普通读→原validate→原session S claim的首UoW，原主事务不变；原authorize(call)和claim(call)薄包装保留真实scanner/既有DB调用，prepare直接调私有_claim，不重复开事务。

真实验证时序完整保留：旧5dcb上新增目标两批14结构红/11语义pass；精确原A25项通过（11 SQLite HTTP+14真实MySQL）；其后原988/974 caller遗漏2项AttributeError失败；root窄修正后这2项及5账本通过，但同次原CAS1项因跨场景查询共享actor全部历史而失败（7pass1fail）。本岗985已按该场景两个实际幂等键查询，不预筛状态，再保持恰2COMPLETE和两条response_request_id对应实际HTTP；plan先→CAS后2项真实通过。没有清表/降低原成功、拒绝或竞争断言，也未改DB988或scheduler。

真MySQL/t44_test证明BLOCK/UNBLOCK/改期/升级SELECT,DML,控制分别22/5/2、24/5/2、20/6/2、26/7/6（经理2、新run1），原三次实时鉴权/SELECT不减，新写2UoW/checkout/commit；完成重放9/0/0与1UoW。实际app连接READ COMMITTED、校验期间与claim后session/member撤销、独立拒绝新Session审计、真实commit后受控模拟ACK丢失恢复均有开发证据。ACK注入不是网络设备故障，lease过期是隔离fixture控制，不停共享数据库。

修正后runtime有效270→276(+6)、物理289→297(+8)，旧-1节省结论撤回。root最新组合基准6102仍超5100，A再增6；不改计数口径/以格式凑数。Ruff/格式/Bandit及14hash核对通过，原失败日志保留。当前未有新源完整CI、独立代码审核、性能/源码规模通过；未启动930/955、服务或正式负载。证据preflight-validation-summary.json及各阶段原log/xml。
