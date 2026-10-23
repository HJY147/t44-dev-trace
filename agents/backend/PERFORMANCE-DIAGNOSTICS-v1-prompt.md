# 实际派工 ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

来源：总协调 /root 实际消息，原文：

ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1（实际派工，当前仅准备阶段）：原三批正式负载已于10:52:33Z全部停止，前两批独立岗已报告原定延迟阈值触发；正式数值/缺陷报告尚未宣布发布，root也未读取现有黑盒文件。现在选用根 records/prompts/ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1-proposed.md 的目标/隔离/交付约束；补充本条为实际dispatch，原文件保留proposed历史，不把事后重述/不同任务硬凑六版。先同步根最新397bd79（含DB94b、FEb485、文档6b4、你的3ee，精确父产品43f51570）。阶段A只做源码/官方资料分析和诊断工具准备：逐层区分排队/CPU/SQL锁与连接池/验证序列化开销，先列剖析函数与真实输入输出，不推定瓶颈。可创建唯一 tmp/backend/955_perf_profile.py（955专属你，全局下一个954）及短跑方案，但暂不运行：root正等待独立正式报告发布，DB岗也在实库漂移验证，会竞争同机资源。root将新建t44_profile并提供中性账号；不触及dev/acceptance/perf或不可变API，不读未发布黑盒文件/私有脚本，不联系测试岗。先交准备checkpoint（清楚实验尚未运行），或等root补充已发布报告/环境后继续阶段B。不得删鉴权/撤销、锁/CAS、幂等/独立拒绝、outbox或契约校验来提速；代码规模仍5866超5100，不压行/改计数/搬逻辑配置。真正优化等证据定位后再写，保留原始基线/失败、模块报告/handoff/实际prompt和GitHub交流。

阶段差异：根proposed文件保持历史。实际dispatch明确只授权阶段A准备，覆盖proposed“正式报告已发布后才执行”的准备准入；阶段B实际运行仍须根继续派工/给已发布报告和隔离环境。不同任务不当同任务提示词演进，不凑六版。

## 总协调实际续派：正式报告发布后先业务修复

独立v1现已正式发布，允许你仅阅读 reports/independent-tests/v1-blackbox-report.md 和v1-blackbox-results.json（不要读其私有证据路径/脚本）；两文件root已核对publication_status=final_published，报告SHA edde6aa85653cc697c31d51f7c01d909a399cbc04d4cd40c577c4ed5706c99f8，结果SHA e88a2b30c2823c9fa5f6fd3a6eeaf5d960bc266edce8da98064dcfe519049e0d。优先级调整：先修IAT-v1-01..05中冻结规则明确的业务/契约缺陷（profile955准备可暂交但不先大优化）。root核实frozen createReleaseAssessment.description明确“创建...并清空旧上线批准引用”，IAT01真实违反；createTask的CAPACITY_REFERENCE_INVALID明确“任务人力...不匹配其迭代容量记录”。IAT03 task_id0审计503；IAT04 public审计只version不能重建计划（内部schedule_changes已有值不代表外部可见）；IAT05 evidence空应EVIDENCE_REQUIRED、contract-validations顶层附加字段PARAMETER_INVALID而候选payload非法CONTRACT_INVALID。请先按原契约独立复现，补开发回归，保持CAS/事务/幂等/冻结11不动；检查新评估B后旧A审批能否又激活、重放创建是否反复失效等邻接路径，勿扩大未定义业务。容量赋值等若发现真实契约范围歧义先列给root，不擅改冻结文件/发明错误码。新必须回归脚本可复用986/985；955继续专属诊断，全局下个954如需新文件先报备。修复IAT01可先小checkpoint并CI，再做其余；不读未公开独立用例，不联系测试岗。性能三批P95=3035/1908/5506ms，零稳态失败、吞吐均达标；公开报告含负载模型/同机背景限制，阶段B剖析在业务修复checkpoint后继续，最终独立复测另建无历史实例。
