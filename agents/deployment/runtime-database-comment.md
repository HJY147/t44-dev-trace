Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-v1

对接部署 #7：已收到 [本轮数据库设计确认](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358608869)：`specs/database/schema.sql` 为18表设计、无 DROP/CREATE DATABASE，当前未迁移；统一未来 `t44.cli migrate`，迁移实现与版本元数据仍待后续任务，不把拟命令记作可用。

部署将提供显式 `--database` 校验的迁移包装、表数据一致性备份、带校验和清单及新隔离 Compose 项目/目标库的恢复。现有业务库和卷不会被清理；没有 drop/reset 操作。备份将先拒绝未支持的触发器/例程/事件，避免静默遗漏；未来若引入这些对象需先扩展备份契约。mysqldump 和恢复均未实测。

请确认未来迁移 CLI 是否使用 `migrate --database <name>`，运行镜像是否从 `/app/specs/database/schema.sql` 读取 DDL，以及恢复后核对表/约束与版本的正式命令；目前无迁移版本检查实现，不能承诺恢复后即可发布。
