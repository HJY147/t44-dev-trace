# MySQL v1迁移

统一CLI调用 `t44.persistence.migrations.migrate(engine, expected_database=...)`。真实SQL作为可随Python包发布的 `t44/persistence/schema_v1.sql` 资源，SHA-256必须等于冻结的 `specs/database/schema.sql`；SQLAlchemy Core元数据也由该资源生成，避免第二份字段列表漂移。

迁移只支持MySQL8.4和明确匹配的项目数据库。用连接级命名锁串行；空库初建，成功后再次调用核版本/摘要和字段/索引/约束并返回already_applied，不DROP/覆盖数据。意外非空库或未完成记录直接阻止，部分DDL失败不宣称可事务回滚。`t44_schema_migrations`是唯一额外技术版本表，不是第十九张业务表；记录version、冻结摘要、处理中/完成和时间。迁移不关闭FK/CHECK、不在API启动时自动执行。
