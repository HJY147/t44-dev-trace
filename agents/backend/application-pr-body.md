冻结v1的研发流程应用：在纯领域状态机基础上实现38个HTTP操作的严格请求/响应适配、opaque身份会话、项目/成员/计划/依赖、评审/发布预案及经理决策，并通过数据库岗UoW统一幂等、CAS、审计和outbox原子提交。账号/迁移及会话撤销由CLI提供；成功data在提交前校验冻结Schema。

当前为draft、持续实现：25项TestClient＋SQLite HTTP自测通过，Ruff/格式/Bandit通过。首次自增元数据故障由DB修后合入，短幂等键测试输入和初始静态检查失败均保留。数据库基础及冻结/整合SHA按协调者指令merge保留。

未完成：消息/调度门面接入、seed owner交付、真实MySQL HTTP/Rabbit联调、全部t44覆盖率、性能和独立验收。领域106测试/98%只代表domain，不代替整产品。此PR不声明审核或验收成功。

Agent-Role: backend
Prompt-Ref: ROLE-backend-APPLICATION-v1
Refs: #3 #4
