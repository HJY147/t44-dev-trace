# 实际派工 ROLE-backend-APPLICATION-v1

来源：总协调 /root 实际消息；本岗不替换模型，不读取独立测试私有资料。

用户已真实回复Q002“采用推荐方案，继续开发”；D004/U006已存。v1规格冻结commit ae60dc3（codex/team-bootstrap，已push），manifest records/spec-freezes/v1.json；OpenAPI仍31paths/38ops，只有版本/状态元数据改1.0.0，业务语义不变，真实validate通过。开始ROLE-backend-APPLICATION-v1完整实现，不再停基础：在你干净独立树先merge ae60dc3保留领域代码，自己索引和原分支PR16；若产品scope扩展重写PR标题/正文。负责全部冻结API/严格JSON Schema请求+响应、auth/argon2/opaque sessions/撤销、DI组合根、状态/排期/依赖/评审证据与发布预案/经理决策业务门面、CLI账号与迁移/seed适配、统一审计拒绝、idem/CAS编排；生产代码要紧凑实际可用，目标全产品有效3500–5100行，不凑数。数据库即将开始18表+持久门面；你必须直接和database明确可编码的Python接口并在Issue3/4留真对接，优先几分钟内定最小接口（new session/UoW，参数化rows/get/insert/update/locks等或同等方案），别只写接口文档。所有SQL/模型/迁移属DB；后端通过其门面业务编排，不能私建第二套存储。已实现SqlAlchemyUnitOfWorkFactory与CommitUncertain保持，失败审计新事务；身份/项目先于重放、锁序按冻结持久契约，成功变更+审计+outbox+idem结果原子。调度/messaging owner稍后接真实接口，请留可注入规则/通知门面并实际对接；你拥有review-template.json（八段十项，版本化扩展），scheduler拥有escalation规则。维护68包hash锁如新增依赖先实际必要性。API和CLI无占位成功，无JWT；env遵守部署README。测试放backend/tests/backend，真实契约测试放backend/tests/contracts且维护pyproject markers；全后端行覆盖分母为全部t44，不能拿domain98%代替。先真实完整应用，单元/契约/业务异常验证，MySQL/Rabbit集成待root整合GHA执行，别标mock=实库。原失败保留处理，不降需求/断言。每阶段自己commit/push至PR16，attach已存在不重复创建；完成给SHA/commands/真实缺口。禁止接触独立测试私有资料。若容量报错从代码恢复，不换模型。

补充：可merge本地整合6afd13fd56d51f27b83ee9847b4e2b0dbd26cc73；DATABASE_URL、T44_DATABASE、AMQP_URL、T44_SESSION_TTL_SECONDS，/api/v1保留；根随后提供本项目官方MySQL8.4.11独立实例用于真实验证。数据库/消息/调度仍由各责任岗交付，不修改其目录。

改进理由：从已采用领域基础推进完整冻结应用；用统一事务和实际HTTP校验约束漂移，不把代码存在或自测冒充独立验收。
