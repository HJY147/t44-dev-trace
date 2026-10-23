# 字段无关持久化基础

本轮只实现连接、事务生命周期和受限Core执行，不包含18表ORM、迁移、业务仓储、状态机/CAS、幂等结果、审计或outbox领域操作。Q002人的字段/错误码取舍仍待回复；本模块不替代该决定。

组合根导入 `t44.persistence.MySQLSettings`、`create_mysql_engine(settings)`，在进程启动时构造Engine；进程关闭时调用 `engine.dispose()`。构造函数本身不连接数据库。SQLAlchemy连接池启用pre_ping、回收、超时、归还rollback；每条新物理连接设置UTC、严格SQL mode及READ COMMITTED。`hide_parameters=True`、禁echo，配置repr和URL默认显示隐藏口令。参数不记录；错误边界只给脱敏内部异常，调用者仍禁止记录原驱动异常/凭据。

`SqlAlchemyUnitOfWorkFactory(engine)` 可调用，每次返回单次使用的上下文管理器：

```python
# factory由组合根注入；binding只能来自已审模型的固定内部配置。
with factory() as uow:
    gateway = uow.gateway(binding)
    rows = gateway.find({"approved_filter_column": value}, limit=page_size)
    # 正常退出commit；异常退出rollback；两者最终close Session。
```

示例不定义任何实际业务字段。`TableBinding(table, readable, writable, filterable)` 只接受SQLAlchemy Core Table与不可变字段元组，校验schema/table/column标识符和列集合。此对象由可信程序配置注入，禁止从HTTP请求、动态表名或用户选择器构造。运行期值始终bindparam；未知字段、SQL表达式值、空where写入会被拒绝。`CoreGateway.find/insert/update_where`是内部基础，**不负责项目权限/状态/幂等守卫，不是产品可直接暴露的通用CRUD接口**。没有字符串SQL执行入口；查询结果在事务内取完并关闭CursorResult，不能将游标带出UoW。

显式 `uow.commit()` / `uow.rollback()` 结束该事务，后续gateway操作被拒；UoW不能复用。驱动执行失败会置rollback-only，即使调用者在块内捕获错误，也不能提交先前的部分写入。每个UoW拥有不同Session；池可在已关闭UoW间复用同一物理连接。未来独立审计要求由组合根注入独立工厂/Engine，本轮不冒称已经实现独立审计连接或持久化。

`CommitUncertain` 表示提交确认失败。随后rollback/close只清理本地资源，不能证明服务器未提交；未来服务层应沿原幂等key恢复结果，映射策略由后端负责。本轮SQLite故障注入先真正commit再抛异常，证明cleanup rollback不能把已提交数据撤回；还验证close错误不覆盖CommitUncertain。其他基础异常为 `PersistenceUnavailable`、`PersistenceIntegrityError`、`TransactionStateError`、`StatementRejected`，均不是冻结业务错误码。

本地复现（依赖从后端维护的Python3.12带hash锁安装，不在本目录维护第二份锁）：

```sh
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/persistence -q
.venv/bin/ruff check --select E4,E7,E9,F,I,UP,B,SIM --target-version py312 backend/t44/persistence backend/tests/persistence
```

测试仅在临时SQLite文件中创建/销毁玩具表验证通用commit/rollback、独立Session/连接归还和绑定值；mock验证MySQL初始化固定SQL/脱敏。没有执行 `specs/database/schema.sql`、没有连接MySQL、没有证明MySQL约束/事务隔离/CAS/并发或独立验收通过。MySQL真实连接初始化及故障恢复仍须后续实测。

设计语义参考SQLAlchemy官方[Engine](https://docs.sqlalchemy.org/en/20/core/engines.html)、[连接池](https://docs.sqlalchemy.org/en/20/core/pooling.html)与[MySQL dialect](https://docs.sqlalchemy.org/en/20/dialects/mysql.html)；实际安装版本记录于本岗foundation-validation.json。
