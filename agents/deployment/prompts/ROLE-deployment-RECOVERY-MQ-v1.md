# ROLE-deployment-RECOVERY-MQ-v1

本岗为这条实际新派工建立的归档标识，不称用户修订或同一提示词演进。

## 总协调实际派工原文

恢复固定部署岗，补独立tester提出的中性能力缺口；不得联系tester/读取其用例、脚本、结果、私钥或任何tmp/independent。所有项目内独立worktree/own index。现环境7c9e48e、受验68b3，SUT仍固定4c20f32b71635016815420472b9d4bb4fa850df0；不要跟root后端5dcb自动漂移。tester已完成R2/R3自己私密解密，报告尚未发布。能力需求：control recover目前成功stdout空，只能exit0/control-events；execution recovery_completed仅finally总体，无法逐次核对。请为CLI recover增加明确JSON逐次回执（例如recovery_completed、已恢复服务/时间/步骤退出信息），只有真实compose unpause/up --wait全成功才能true；失败保留非零+结构化false/稳定错误，不泄露原异常/凭据，不把finally被调用当成功。lease自动和finally既有行为不改、不扩大权限。再把实际MQ transport元数据加入中性context/协议：默认exchange=t44.events、queue/routing_key=t44.notifications、quarantine后缀，wrapper event_id/schema_version/event_type取真实outbox行；properties content_type application/json delivery_mode2 message_id=str(event_id) type t44.event.v1 mandatorytrue。root已向tester提供这些默认中性wire事实，不含业务预期，你应核4c实际compose/worker无override，不能猜。先必要本岗953保护自检，再一次有变更的environment-check真实验证新JSON回执/恢复及传输元数据（原请求可增revision，产品仍4c）；这是修复复核不是重跑旧整套Docker业务。保持旧失败/通过记录，新的回执单独SHA。新脚本需向root领号（当前918），可扩原953，不用为低风险文档造测试。用户已澄清SSH密码是误发，此项目无SSH目标，不使用/保存密码/连外部主机。需要本岗代码/实际prompt/日志/模块报告/handoff/Issue7+PR15留痕；交最终中性协议+capability run+完整实现SHA给root，root只把这些白名单传tester。先完成必要安全实现，不读其private-v2内容。

## 对应产物

仅deployment/acceptance中性能力、原953部署守卫和本岗记录；不造tester用例，不读取项目tmp/independent或其密钥/未发布结果。无SSH目标，不使用/保存密码。固定4c20f32产品源；新增逐次恢复JSON和MQ真实默认wire元数据，不改变产品/门禁/覆盖率或租期/finally操作范围。
