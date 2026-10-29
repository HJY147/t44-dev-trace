Agent-Role: backend
Prompt-Ref: ROLE-backend-CORE-FOUNDATION-v1
Refs: #3

D001的交付流转此前只有设计资料。本次把七状态九动作实现为可复用纯领域包：typed command经当前角色、责任人、证据/轮次及三处依赖守卫产生不可变Decision，由后续事务门面应用。非法跳级、缺原因/依据、过期评审和未审预案会产生内部DomainViolation，不绑定待用户取舍的HTTP状态或库字段编码。

同时建立Python3.12项目及uv实际生成的跨平台hash依赖锁，含同步FastAPI/SQLAlchemy2/PyMySQL[rsa]、Pika、APScheduler3、argon2-cffi；没有JWT。接口与事实边界见 `agents/backend/core-interface-notes.md`。

验证：本机hash安装、项目wheel构建安装、pip check通过；Linux目标依赖解析版本与通用锁一致，未执行Linux运行。106项领域单元测试通过，Ruff/格式/Bandit退出0，仅领域含分支覆盖约98%；JUnit、coverage JSON及原始日志随提交保存。首次pip证书链失败和Ruff排序失败保留，未关闭TLS。

此PR为草稿基础阶段：未实现API、DB/迁移、事务/幂等/CAS/审计、MQ/调度或联调；没有HTTP、MySQL、独立验收或性能结果，不意味着Q002已采用、契约冻结或产品验收通过。无需为了部署preflight补占位成功接口。
