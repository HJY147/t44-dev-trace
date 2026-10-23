# 数据库模块报告：通用基础

## 当前范围与状态
- 岗位database；实际派工ROLE-database-FOUNDATION-v1；独立树.agent-worktrees/database，codex/database-runtime，起点bc0cd349fcf854f48f4179e1f131e5c2dd8a7e68。
- 字段无关Engine/UoW/受限CoreGateway基础已实现；18表ORM、迁移、业务仓储、API联调仍未实现。
- C1–C4技术复审闭合是总协调派工时转述，非本岗复审结论；Q002人的字段/错误码取舍尚未收到，未进入模型或迁移阶段。
- 已读本树AGENTS、implementation-layout及persistence-contract；未修改共享规范/依赖锁，未读取或联系独立测试。

## 实际产品产物
- backend/t44/persistence/engine.py：MySQLSettings及延迟连接Engine工厂、池/超时/回收、每新连接UTC/严格模式/READ COMMITTED。
- uow.py：注入Engine的SqlAlchemyUnitOfWorkFactory，每次独立Session；单次上下文正常commit、异常rollback、总close。
- gateway.py：可信固定TableBinding列策略与CoreGateway；参数绑定值、标识符allowlist、拒SQL表达式/未知字段/空where写，不提供rawSQL入口。
- errors.py与__init__.py：脱敏内部异常/稳定导出；README说明组合根注入、生命周期、调用与验证边界。
- backend/tests/persistence/test_foundation.py：SQLite临时玩具表及mock连接测试，无项目ORM/DDL依赖。

## 行为与接口确认
- backend已直接确认MySQLSettings/create_mysql_engine、可调用SqlAlchemyUnitOfWorkFactory、CommitUncertain接口，由组合根注入；当前未接API。
- 任何驱动执行失败使UoW只可rollback；调用者吞掉错误也不提交先前部分写。查询在事务内取尽并关闭结果，不外泄游标。
- commit确认丢失保留CommitUncertain；cleanup rollback/close不能证明服务器没提交，也不覆盖该异常，未来服务沿原幂等key恢复。
- 基础层不承担项目权限/状态机/CAS/审计/幂等/图锁；这些仍只有specs/database设计，未虚构占位成功仓库。
- 独立Session不等于永久独占物理连接；池可复用关闭事务的连接，未来独立审计需单独注入工厂/Engine并实测。
- 固定TableBinding只能由可信内部配置构造，禁止从HTTP用户输入创建表/列策略；值中的SQL文本作为普通绑定值保存。

## 真实执行与验证
- Python3.12.10；只读backend独立树requirements.lock，以uv --system-certs --require-hashes安装；SQLAlchemy2.1.6/PyMySQL1.2.3，未维护第二份锁。
- 首轮pytest 15 passed；新增并行Session/连接、执行失败及进入中断资源关闭后，最终18 passed（run3，0.16s）。
- 首轮Ruff退出1，七项为SIM105、导入排序、嵌套with风格；原日志保留，修复后run2/run3均All checks passed。
- 测试真实覆盖SQLite提交/回滚/资源归还、捕获约束异常后整事务回滚、值注入/标识符拒绝、mock初始化失败脱敏。
- 额外故障注入先真正commit再抛ack异常，确认行仍存在且保留CommitUncertain；不把rollback清理说成未提交。
- 日志foundation-test-run1/2/3.log、foundation-lint-run1/2/3.log；foundation-validation.json记录环境、依赖锁SHA、源码SHA与验证边界。
- SQLite只执行测试夹具玩具表DDL；未连接MySQL，未执行specs/database/schema.sql或迁移，不能称MySQL约束/事务/CAS或独立验收通过。
- 未运行API联调、覆盖率、性能、独立验收；本轮模块测试与正式验收分开。

## 过程、交接与后续
- 实际Issue阶段说明 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6359431821 ，本地正文foundation-stage-comment.md。
- 实际prompt归档agents/database/prompts/ROLE-database-FOUNDATION-v1.md；操作者为AI，不记用户亲改。
- 文档岗M1已真实问取，本岗原文回答基础进行中/无MySQL/未提交事实，保留在WORKLOG；完成SHA/PR另行补送。
- 下一步先确认Q002与字段/错误码冻结，再另行派ORM/迁移/业务仓库及真实MySQL验证；消息/调度门面适配尚未实现。
