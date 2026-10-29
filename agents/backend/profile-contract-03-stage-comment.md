岗位 backend；Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1。

工具245e56b9866b34d5c75b5d0670ba735a5ee75249（实际生产字节同4c20f32开发CI394pass）在2026-10-23T13:18:49.973332Z–13:19:57.093091Z仅t44_profile/18083/1worker执行短诊断。baseline1/8/32请求2277/3631/3282、E2E P95 5.444/33.143/149.208ms；timings2506/3418/3172、4.856/35.185/151.564ms；错误0。加3profile共18289主样本，另3sanity，逐项HTTP200/valid/无violations；9099服务记录request_id匹配、dropped/SQL错误0。

整体controller结尾断言错用bootstrap返回值，仍RuntimeError/exit1；三子服务均正常exit0、无遗留进程，窗口已释放。两行赋值修复只用原metadata离线检查，未重跑负载、未改原失败，不宣称修后整controller运行成功。

cProfile三样本inclusive合计execute35.007/rows27.158/authenticate24.111ms互相重叠，含等待和冷TLS，不是纯CPU占比。Runtime平均线程CPU2.081→2.553ms，连接获取/SQL游标墙钟随并发增长；尚无纯poolwait/DB内部锁因果证据。未修改pool、安全/事务/校验/冻结文件，未称正式400VU/600s/4worker或源码规模通过。

证据agents/backend/profile-contract-03-analysis.md、summary.json、raw-manifest.json、metrics.zip（38原始文件，私密fixture排除）、profile-offline-controller-check.json。原controller失败保持；后续由总协调据证据限定下一测量/优化，不自动再发负载。
