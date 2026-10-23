# 实际基础实现派工原文

派工ID：ROLE-database-FOUNDATION-v1；发送者AI总协调，执行者数据库岗位AI。不是字段/错误码人的审定，也不把AI改码计作用户亲自修改。

> ROLE-database-FOUNDATION-v1：技术复审C1–C4已由reviewer初步确认闭合，仍在其本人归档；Q002字段/错误码人的选择未收到，故本轮只做不依赖具体业务字段的真实数据库基础，不写18表ORM、不执行DDL、不迁移、不接API联调。独立树 `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/database`，branch codex/database-runtime，base bc0cd349fcf854f48f4179e1f131e5c2dd8a7e68 已建。读本树AGENTS/implementation-layout/现行persistence-contract。
> 只拥有 backend/t44/persistence/、backend/tests/persistence/ 及本岗日志/报告/handoff/prompt。实现可复用 SQLAlchemy2 Engine/UoW 工厂及参数化持久门面基础/纯接口：连接池、每连接UTC/严格SQL mode/READ COMMITTED、独立Session生命周期、正常commit与异常rollback关闭、只接受参数绑定与固定安全标识符的内部仓储入口。组件由构造函数/组合根注入，不在业务函数偷偷建连接；定义稳定类/方法供backend/未来消息调度调用并与backend直接对齐。暂不要引用不存在ORM或做占位成功的repository，具体字段操作等人审/冻结后实现；空壳接口不算实现进度，重点是真正连接生命周期/事务关闭及安全边界逻辑。
> 有价值的本地单测可用受控SQLAlchemy SQLite验证通用commit/rollback/独立Session与资源释放，或mock驱动验证MySQL connect初始化SQL/敏感连接串脱敏；必须明确这些不是MySQL约束/事务/CAS实测，不用SQLite假称MySQL通过。不能把测试换成只验证常量、只为凑覆盖率。backend正在本独立树外编译 pyproject/带hash锁，Python3.12+SQLAlchemy2/PyMySQL[rsa]；本树可建.venv实际安装对应依赖跑模块测试，别改其锁或共享文件。参数化方案需防标识符注入，不搞万能rawSQL业务接口。
> 只在本树显式提交本岗基础/自测/日志/handoff/本轮实际prompt，footer Agent-Role database、Prompt-Ref ROLE-database-FOUNDATION-v1、Refs #4。可push分支建base codex/team-bootstrap草稿PR并attach，不merge main不发reviewer成功；不联系测试，不读独立私有用例。完成返真实产物/SHA/验证边界，后续收到用户取舍与规格冻结才进入模型/迁移/仓储实现。

总协调实际追加：提交确认丢失须区分CommitUncertain；随后rollback不能声称未提交，未来上层映射503并沿原key恢复。执行前/中明确失败rollback关闭，所有路径归还资源，直接与backend确认工厂/异常名，不扩展字段。

产物对应：persistence Engine/UoW/受限CoreGateway与README、SQLite/mock模块自测、原始失败及成功日志、本岗工作日志/报告/handoff。设计取舍：先实现不受Q002影响的真实资源生命周期；不是补空壳业务仓库或虚构MySQL通过。
