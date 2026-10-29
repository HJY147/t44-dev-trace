Agent-Role: backend
Prompt-Ref: ROLE-backend-APPLICATION-v1
Refs: #3 #4

Q002已由用户采用，冻结1.0.0后实际开始应用编码，不再把旧foundation限制当本轮状态。

已实际合入8095b6ee5ccc7d7f4f8729d581c56be1227d55c4并对接：`with factory() as uow; g=uow.gateway`；rows/get/insert/update/delete/count、Pred和savepoint均由数据库岗实现；API只编排白名单字段，不写SQL、ORM或第二存储。账号CLI将内存Argon2id hash传给`initialize_user(factory,username=...,display_name=...,password_hash=...)`；迁移/合成数据仅适配数据库岗migrate/seed入口。真实MySQL迁移由DB另报，不冒称本岗已执行。

应用已写session→idem→project（需要时）→members按user_id→tasks按id的统一编排，成功业务/audit/outbox/idem完成快照同UoW；拒绝主UoW退出后开新UoW。完成时保存本次实际完成者request_id，重放用response_request_id；不保存旧meta或凭据。现为代码和首轮HTTP自测阶段，尚无全产品通过结论。

首个TestClient+SQLite真实网关流程在createTask遇到循环FK主键autoincrement识别缺陷，已直接告知DB；DB确认显式ignore_fk修复并补生成ID测试。此为实际发现，原失败保留（瞬时自测会话脱敏），尚待合入修复后重跑。SQLite不能证明MySQL锁/约束，后续真实MySQL另记。

请DB在下一SHA交付迁移、hash-only账号及自增修复；backend据此继续HTTP全链，规格语义不变、不降低断言。
