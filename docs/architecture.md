# T44 架构选择说明（M2可审工作稿）

Agent-Role: documentation；Prompt-Ref: ROLE-documentation-M2-QUALITY-v1。

本文补齐任务书第6节指定的`architecture.md`入口。它是自编设计说明，不修改冻结1.0.0规格，也不是性能验收。读者先看[需求SRS](../reports/final/requirements-report.md)，再看[概要/详细设计](../reports/final/design-report.md)的模块、进程、ER、事务和消息时序。

## 时间与证据归属

- 当前采用栈由已冻结的[实现布局](collaboration/implementation-layout.md)和[后端设计](../specs/backend-design.md)确立，实际依赖/进程见`backend/pyproject.toml`、`frontend/package.json`和`compose.yaml`；不是本次文档临时替换实现。
- M1设计报告`8cf92cb`已比较采用栈与自部署Supabase替代。现存资料不足以证明开发前已写出本文件，也不证明用户逐项批准过每个技术组件。
- 下面Java/Spring候选及三维度整理是M2为补齐任务书而追加的分析。没有运行替代实现，不追溯称为早期实测、学生本人设计或已批准的迁移决定。
- D001/D004是用户业务/字段错误码采用，D002/D003是AI技术编辑取舍；不将二者混记。

## 候选组一：同一Python业务层的持久与平台边界

| 三维度 | A：Vue + FastAPI + MySQL + RabbitMQ + APScheduler（已采用） | B：Vue + FastAPI + 自部署Supabase PostgreSQL/Auth + MQ/调度（比较候选） |
| --- | --- | --- |
| 性能 | 当前事务、图锁、CAS及outbox路径能直接绑定实际SQL与测试；265d89b托管整套通过。400并发指标仍未取得结论 | 需重做数据库方言、锁/迁移/事务与认证集成，再在同数据/硬件/负载下测；本项目没有B的P95或吞吐结果 |
| 成本 | 已有实现和责任岗；需要自行维护鉴权、MySQL、Rabbit与备份；未提供云价或采购结果 | 可复用平台认证/数据入口，但自部署并不免服务器、安全、升级、备份工作；重做v1迁移和验证增加本项目工作量，未实算货币成本 |
| 可维护性 | domain纯决策、Runtime事务门面、owner gateway和消息/扫描边界可定位故障；配置扩展和对应模块有证据 | 若选用须保持同样业务门面，禁止由通用CRUD绕过状态机；还要同步平台schema/认证与现有契约，当前没有对应维护验证 |
| 选择理由 | 适配已冻结MySQL字段/错误码/持久契约及现有实现；继续验证实际系统 | 保留为替代思路，当前不迁移；不能据此声称Supabase不能实现需求 |

## 候选组二：业务服务语言与生态

| 三维度 | A：Python 3.12 + 同步FastAPI/SQLAlchemy2/PyMySQL + Pika/APScheduler（已采用） | C：Java + Spring Boot + JDBC/事务 + Rabbit客户端/调度（M2补充候选） |
| --- | --- | --- |
| 性能 | API多worker，扫描/消息独立进程；业务事务之外等待MQ。已有真MySQL/Rabbit CI，未完成正式压测 | 需要实现相同状态/鉴权/幂等/CAS/独立拒绝审计和索引策略后同条件测量；不能由语言名或异步标签推断P95胜负 |
| 成本 | 已有真实hash锁、可安装依赖、源码/容器入口及调试记录；继续补全测试的投入可沿用 | 当前无Java实现，重做接口/DDL映射、构建、部署与相同测试；团队学习/迁移时间未测，不编造人日或内存差额 |
| 可维护性 | typed领域命令和显式持久码；门面DI按模块测试，Python可读性不替代类型/边界检查 | 可采用同样分层/DI/事务边界；需独立验证映射、事务传播和异常协议，不能把框架默认行为当作本业务已正确 |
| 选择理由 | 与冻结布局、岗位分工、现有代码一致，避免为报告比较改造产品 | 任务书允许Java；本轮仅补充可比较路线，不把未实现候选写成失败产品 |

两组均为本项目范围下的分析，不是通用产品排行榜。公平比较应固定40项目/6000任务/9000依赖/约15000评审决定、索引、机器资源、请求比例和400并发稳态10分钟，再测失败率/P95/吞吐和运维工作量；当前没有替代方案对照实验。

## 当前结构与实现索引

采用前后端分离、单体分层：浏览器→Nginx→FastAPI组合根→Runtime/Business→纯domain和注入UoW/RowsGateway。独立扫描进程经同一业务门面创建升级；消息进程使用持久outbox、confirm/消费及终态fallback；MySQL承担原子性与唯一约束。API多worker不各自启动调度器。图与交互详见[设计第2/3节](../reports/final/design-report.md)，不另画一个与实现不一致的架构。

| 设计约束 | 权威来源/当前入口 | 核查边界 |
| --- | --- | --- |
| 字段、主键、最小类型/枚举 | [字段字典](../specs/database/field-dictionary.md)、[DDL](../specs/database/schema.sql)、`backend/t44/services/codes.py` | 显式映射不能依赖Enum顺序；冻结11文件只读 |
| 迁移、版本、成功/拒绝事务、锁 | [持久化契约](../specs/database/persistence-contract.md)、`persistence/migrations.py`、`services/runtime.py` | 成功任务/证据/幂等/outbox同事务，拒绝独立事务；CommitUncertain明确503 |
| 扫描与幂等复杂度 | [后端设计](../specs/backend-design.md)、[详设伪码](../reports/final/design-report.md)、`scheduling/scanner.py` | 全扫描最坏O(NL)，事件查找O(K log(E+1))，通知展开O(ΣR)，不能冒称全程O(1) |
| 消息降级/恢复 | `messaging/worker.py`、`persistence/delivery.py` | 同事件/收件人唯一，消费提交后ACK；网络至少一次不等于网络恰一次 |
| 本模块测试与FR | [M2追踪矩阵](reports/M2-traceability.md)及tmp/ | 模块成功与托管整套、Docker、独立验收和性能分别记录 |

准确SHA265d89b的四产品CI已通过，整套317通过/零跳过、whole Python88.07%、前端92.21%；[归档回执](reports/M2-ci-snapshot.json)。正式性能、有效代码规模、完整Docker/恢复及最终独立验收仍以各自准确版本的公开证据为准，本文不提前宣告达标。
