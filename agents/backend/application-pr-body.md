冻结v1的研发流程应用：实现38个HTTP操作的严格请求/响应适配、opaque身份会话、项目/成员/计划/依赖、评审/发布预案及经理决策，并通过数据库岗UoW统一幂等、CAS、审计和outbox原子提交。账号/迁移及会话撤销由CLI提供；成功data在提交前校验冻结Schema。

当前为draft、分阶段交接：27项HTTP自测通过（26 SQLite＋1官方MySQL8.4.11）；真实MySQL覆盖登记、并发CAS、独立拒绝审计、diff/outbox/幂等完成来源及提交评审。真实Uvicorn loopback服务和4项TCP烟测可用。Ruff/格式/Bandit通过。首次自增元数据故障由DB修后合入，短幂等键测试输入及初始静态检查失败保留。MySQL fixture同时支持CI的DATABASE_URL＋T44_DATABASE显式校验，已以本地真库实际跑URL环境分支；不等于GitHub Actions已通过。

未完成：消息/调度门面接入、seed owner交付、Rabbit联调、全部t44覆盖率、全流程MySQL、性能和独立验收。领域106测试/98%只代表domain。按总协调安排先交付可运行API阶段，随后恢复完整整合；此PR不声明审核或验收成功。

Agent-Role: backend
Prompt-Ref: ROLE-backend-APPLICATION-v1
Refs: #3 #4
