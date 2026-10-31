# P18 本地完整流程：原性能指标FAIL，combined exit1

**本轮原指标因人工fixture延迟实际CLASS_P95 FAIL，不能称本地性能PASS或全部回归PASS；不证明真实产品P95。** 原400/60+600完整执行、初态修复、全部400后置、清理及失败退出封存分别留下证据。原P17真实NP不改写。Linux/cgroup/真实APP SQL鉴权未验证。

准确QA身份仍为base9cf/postfeff/compiledff95/BOOT7e9b，effective binding af93a6ffd956c0a2ae86362a6a0e13db9be589e8cfde7335195020cc3a7401b7；源/入口/key自初始物料冻结后未改变。

## 实际完成的完整轮

2026-10-31T11:30:49.756126Z启动，原warmup实际60.000秒、steady实际600.000秒；原工具观测673.7215205秒（含后置/收尾）。本地TLS fixture在测量阶段transition与escalation POST明确注入2.5秒延迟，用于观察长时生命周期、原指标负例和非零失败封存，未排除这些慢请求。原四类P95：query4.496ms、transition2527.887459ms、contract4.402917ms、escalation2529.936375ms；transition/escalation超过270，原metrics FAIL、combined exit1如实保留。十分钟完成桶15587、15638、15735、15694、15684、15926、15845、15854、15938、15782。

全部182268个exchange（warmup15785/steady158083/postcheck8400）记录错误0，HTTP200=147704、202=34564。所有400客户端首BLOCK都由state2迁到3；后置400最终快照、400完整审计、8400个验证job。40秒预算未改：post exchange窗口13.526477375秒，steady_end到全部owner排空13.665105167秒；未发生post deadline，pool/writer均停止。

182916条raw完整认证，plain824761978B、compressed84009566B。14文件84892925B备份认证解密/逐文件SHA通过，cipher SHA8b27119fae2fda194d5eafb4d125b33a033fe53f143d5fd803449f756bac5f46。即使combined exit1也完成封存回收，不把非零等同于丢弃证据。原result SHA89f826dc1ff20dae2f589e7e14144a97b434fdb8f46ed2b4b1bf98a763ab0dba。

## 初态和第二次准备

本地fixture沿用原400/800映射，受控混合200个state3/from2与200个state2。实际新producer c7e77/ebbf9经真实本地TLS执行200次合法action3+权威GET新CAS，另200个state2零写；没有手改成2绕producer。实际bcec pure domain state_machine/models原字节在handler内决定BLOCK/UNBLOCK；SPEC从冻结OpenAPI加载，角色/依赖等trusted context为合成，不冒完整FastAPI/MySQL。归一化之前的重复BLOCK负例由domain拒绝，fixture adapter映射409 STATE_CONFLICT（该负例为直接adapter调用，不是生产HTTP负例）。

完整轮同服务保留真实尾态330个state2、70个state3；随后独立local-r30posttools19-smoke/new workspace/新producer幂等域，合法UNBLOCK70个、330个零写，400任务再次准备为2并全部首BLOCK2→3。通用runtime入口短预热设置为3秒，仅为第二轮起步状态回归，不是第二个完整600秒测量，也未改生产BOOT RUN18。该短回归后置400/400、raw完整、全部worker退出。没有在两阶段之间手改残留状态。

最初本地fixture接线曾丢Meta.server_time，原schema在0.127秒正确拒绝；失败原raw/备份保留，修正仅fixture响应字段后使用独立本地前缀。本失败不归咎producer/产品，不将其计成完整轮。

以上只有本地真实TLS合成服务及冻结pure-domain路径，不是现场性能或Linux资源验收。未调用原服务器SSH/云/SUT，未通知用户开机；后续现场启动由总协调依据整包审核与用户要求负责。
