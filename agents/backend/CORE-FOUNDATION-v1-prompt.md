# ROLE-backend-CORE-FOUNDATION-v1 实际派工

来源：总协调向backend岗位的实际任务。以下原文归档，不是用户提示词演进或用户亲改代码。

> ROLE-backend-CORE-FOUNDATION-v1：现在可进行不依赖未采用字段的真实后端基础，用户D001已采用七状态业务规则；Q002字段/HTTP错误取舍仍待用户回复，契约/DDL技术修复正在复审，故本轮不实现API路由、不接DB、不迁移、不联调或宣布冻结。独立树 `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend` branch codex/backend-core，已建于bc0cd349fcf854f48f4179e1f131e5c2dd8a7e68。先读本树AGENTS/implementation-layout/已修contracts及business-rules。
>
> 本轮负责真正可复用的Python包基础和已采用业务域状态机：backend/t44/__init__.py、domain/、必要纯协议/配置加载基础、backend/pyproject.toml、带全部依赖hash的requirements.lock、backend/tests/backend/domain*。同步FastAPI/SQLAlchemy2/PyMySQL/Pika/APScheduler路径已定；采用argon2-cffi+opaque token，不要JWT。为MySQL8.4 caching_sha2_password核对官方PyMySQL文档并包含需要的RSA/cryptography extra。依赖锁同时支持本机Mac/CI Linux Python3.12，uv compile --generate-hashes等实际生成，不能手造lock。与deployment确认pytest contract/integration/fault及JUnit/JSON报告插件实际命令。Node不归你。
>
> 核心状态机使用集中Enum与明确领域命令/决策，七状态九动作按D001，拒绝非法边、阻塞/解除必有原因环节/依据、依赖开始/回开发/返工守卫；角色、证据/轮次守卫用明确注入的纯上下文/协议，不import ORM，不给客户端直接set_state通道。输出领域决定，由以后事务门面应用；领域错误先内部语义，不伪装成已确认HTTP契约。写有价值的参数化自测覆盖所有合法边/非法跳级/阻塞返回/缺证据或依赖，不做只断言常量等镜像测试。真实安装、Ruff与模块pytest可本机跑，记录真实结果；不把它称为HTTP/集成/独立验收或全项目覆盖率通过。禁止占位成功API或为了preflight通过造stub。
>
> 只在本worktree显式add本岗路径+日志/报告/handoff/真实prompt，commit footer Agent-Role backend、Prompt-Ref ROLE-backend-CORE-FOUNDATION-v1、Refs #3。可push本岗分支建base codex/team-bootstrap草稿PR并attach；不merge main不发reviewer成功，不联系独立测试。完成基础可先commit并结束，我在字段取舍及规格冻结后派完整业务实现。

总协调实际澄清：依赖仅start、unblock到develop、rework三处检查；reject_review不新增依赖守卫。评审失败按现行设计退开发、发出review cycle推进/清批准效果；上游后来回滚不自动改下游状态。

部署岗实际答复：markers为contract/integration/fault且strict；领域单元不冒充这些标记。JUnit为pytest内置 `--junitxml`；JSON由coverage CLI输出，无需pytest-json-report/pytest-cov插件。CI工具pytest9.1.1、coverage7.17.0，本岗已纳入真实依赖锁。

数据库岗实际对齐：MySQLSettings/create_mysql_engine、可调用SqlAlchemyUnitOfWorkFactory及CommitUncertain独立于领域包，由其基础模块负责；本岗不实现或连接这些组件。
