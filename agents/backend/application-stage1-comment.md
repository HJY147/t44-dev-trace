Agent-Role: backend
Prompt-Ref: ROLE-backend-APPLICATION-v1
Refs: #3 #4

Q002用户采用及1.0.0冻结后已进入实际应用，不再停纯域基础。`backend/t44/api.py`注册全部38操作，`services/`实现鉴权/opaque会话、项目/成员/迭代、任务/排期/依赖、评审八段十项、上线预案独立审核和经理发布/回滚/返工；统一Runtime编排session/idem/项目图锁/members/tasks、CAS、成功审计/outbox/完成快照同UoW及失败后新UoW拒绝审计。无生产SQL/ORM或第二套存储，依赖数据库岗真实gateway。

真实TestClient＋SQLite网关25项HTTP自测通过（含完整业务流、请求/响应Schema、数值规范化重放、旧版本、撤销/越权、依赖环、UTC边界、改期批准失效和审计/出箱注入故障）。首次实际发现DB自增元数据问题已由DB修复合入；短幂等键测试输入错误已修，原失败留存；Ruff/format/Bandit最终通过。422路径使用`/字段/下标`，不回显原input，Token/口令/完整body不写审计。前端仍需实际网络联调，未声称其已发生。

当前仅阶段1：通知/升级owner门面和seed尚未全部交付，缺失依赖明确503，未造占位成功。MySQL HTTP、Rabbit、全部t44覆盖率、性能和独立验收尚未执行；原domain98%仍仅领域范围。后续继续实现/联调并推送同一PR16，规格冻结不等于产品通过。
