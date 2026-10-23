Agent-Role: database
Prompt-Ref: ROLE-database-FOUNDATION-v1
Refs: #4

实现字段无关的MySQL Engine、可注入UoW工厂和受固定TableBinding约束的CoreGateway，供后续业务持久层复用。正常退出提交、异常回滚并关闭Session；被捕获的驱动错误使事务只可回滚，提交确认丢失保持CommitUncertain，不将cleanup rollback误称为未提交。连接初始化固定UTC/严格SQL mode/READ COMMITTED，值参数绑定，拒绝非法标识符、SQL表达式值及空条件写入。

验证：Python3.12.10，使用后端维护的带hash锁安装SQLAlchemy2.1.6/PyMySQL1.2.3等依赖；18项本岗模块测试通过，Ruff通过。原始首轮Ruff七项风格失败及后续修复结果均保留在agents/database。SQLite仅测试玩具表的通用事务与资源释放，mock仅核对MySQL连接初始化/脱敏；未连接MySQL或执行项目DDL，不代表MySQL约束、隔离、CAS或验收通过。

Q002人的字段/错误码取舍未收到；本PR没有18表ORM、迁移、业务仓储、API联调、成功/拒绝审计或消息调度实现，不修改共享锁文件。工厂/异常接口已与backend直接对齐；后续业务操作须等用户取舍与规格冻结。当前为draft，未声明reviewer放行或合并。
