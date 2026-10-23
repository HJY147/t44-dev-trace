# 实际派工 ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

来源：总协调 /root 实际消息，原文：

ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1（实际派工，当前仅准备阶段）：原三批正式负载已于10:52:33Z全部停止，前两批独立岗已报告原定延迟阈值触发；正式数值/缺陷报告尚未宣布发布，root也未读取现有黑盒文件。现在选用根 records/prompts/ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1-proposed.md 的目标/隔离/交付约束；补充本条为实际dispatch，原文件保留proposed历史，不把事后重述/不同任务硬凑六版。先同步根最新397bd79（含DB94b、FEb485、文档6b4、你的3ee，精确父产品43f51570）。阶段A只做源码/官方资料分析和诊断工具准备：逐层区分排队/CPU/SQL锁与连接池/验证序列化开销，先列剖析函数与真实输入输出，不推定瓶颈。可创建唯一 tmp/backend/955_perf_profile.py（955专属你，全局下一个954）及短跑方案，但暂不运行：root正等待独立正式报告发布，DB岗也在实库漂移验证，会竞争同机资源。root将新建t44_profile并提供中性账号；不触及dev/acceptance/perf或不可变API，不读未发布黑盒文件/私有脚本，不联系测试岗。先交准备checkpoint（清楚实验尚未运行），或等root补充已发布报告/环境后继续阶段B。不得删鉴权/撤销、锁/CAS、幂等/独立拒绝、outbox或契约校验来提速；代码规模仍5866超5100，不压行/改计数/搬逻辑配置。真正优化等证据定位后再写，保留原始基线/失败、模块报告/handoff/实际prompt和GitHub交流。

阶段差异：根proposed文件保持历史。实际dispatch明确只授权阶段A准备，覆盖proposed“正式报告已发布后才执行”的准备准入；阶段B实际运行仍须根继续派工/给已发布报告和隔离环境。不同任务不当同任务提示词演进，不凑六版。
