# N07 第二轮：保行为的结构预算及两项小原型

操作者：审核岗位 AI；这是架构方案和静态证据，不是生产实施或独立验收。
来源基线：`d9e971a631a970d59bdc96923f184c820f6de484`，总协调给定产品字节标识
`935ab5b93bea788672c2b4a088c79cfeed848954`。独立分支
`codex/source-budget-deep-plan-20261025`；worktree 位于项目内
`.agent-worktrees/source-budget-deep-plan-20261025`。

**结论：生产源代码变更 0，生产实际节省 0。主指标仍为 6335，距 5100 缺 1235。**
本轮找到了复用现有 Schema 投影器的净 5 行候选；另一个真正去重复的扫描初始化
公共工厂，计入完整 helper 和 import 后净 0。以下三条有边界的工程路线均不足补齐
1235；它们的估算不能当成已实现收益，不能据此批准规模门禁。

## 1. 输入、计量与隔离

- 当前主口径引用总协调已发布的
  `records/metrics/20261025-post-role-fix-source-count.json`：6335 行、66 文件，
  `within_range=false`，commit=d9e971a。只提取其中 application 摘要与来源哈希到
  `tmp/813_source_budget_deep_plan/baseline.json`，不重新运行包含测试根的完整计数器。
- 固定计数器 `scripts/metrics/source_count.py` 未改。小原型单独下载官方 cloc 2.10
  release asset，实际 SHA-256 `bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83` 与计数器常量完全一致。
- 仅阅读产品、需求/规格、前轮公开架构报告、指定主计数与协作规则。未读取
  tmp817/818/829/814、private、.runtime 或独立测试内容；未运行应用、SQL、套件、
  覆盖率、压测或密集扫描。下载的 cloc 工具不提交为产品源。
- `git diff --quiet d9e971a -- backend/t44 frontend/src frontend/index.html` 实际返回 0。
  临时文件保留在本 worktree 的 `tmp/813_source_budget_deep_plan`；没有修改活动 SUT。

## 2. 已有抽象决定了剩余预算

不能把“Schema 驱动”再次作为一个未经核算的大额节省承诺：

| 已有接口 | 当前实际职责 |
| --- | --- |
| `api.py::validate_request/create_app` | 冻结操作表驱动路由、参数、请求与响应验证，保留严格 JSON、输入安全和错误优先 |
| `services/common.py::model`（44–46） | 仅 3 行，按 Schema properties 投影，统一 wire 转换 |
| `services/common.py::page`（77–92） | 通用分页、过滤与 count，多个业务已复用 |
| `services/application.py::dispatch`（39–61） | 四种任务子资源集合已共享适配 |
| `persistence/schema.py::build_metadata` | 从冻结 DDL 生成 SQLAlchemy 元数据，没有第二份手写列清单 |
| `frontend/src/contract.ts/forms.ts` | 操作、表单与校验已消费共享契约；大部分映射已经是一行数据声明 |

`RowsGateway` 的 299 行包含标识符/SQL 表达式拒绝、谓词 allowlist、失败事务标记、
savepoint、界限检查、锁参数、批量同形检查和专用查询。把这些改成更短的裸 ORM
调用会减少保护，不属于本任务的保行为路线。迁移的严格 CHECK 语法与 MySQL 反射
适配也不因引入另一个 Schema 库而自动消失。

## 3. 路线 A：复用既有响应投影与分页，保持模块 owner

**接口及文件。** 保持 `model(name,row,**extra)` 的原接口；将
`scheduling/facade.py::EscalationFacade.event`（28–56）的直接字典投影交给它。
业务模块仍负责 disposition、收件人、扫描 UUID 和 handled_count 的求值，公共层
不访问数据库、不决定权限。通知列表若继续优化，只为 `common.page` 增加显式
`order_by` 可选参数，由 `messaging/facade.py::list`（42–61）传 `('-id',)`；保留
原查询默认顺序、两个额外 count、当前项目资格锁及全部 predicates。

**预算。** 事件投影已实测整文件 **205→200，净 5**，新增导入名已计入。通知分页
共享还需保留调用、额外计数和公共层参数，可信额外预算 0–8；其余适配器只允许在
owner 确认后核算 0–7。因此本路线暂定 **5–20 行**，其中只有 5 是临时原型实测。
不能再把 Project/Member/Iteration/Task 的两行 wrapper 当作数十行待删重复：迁到
新 registry 后仍需记录名称、转换和依赖，可能净增。

**静态证据。** `projection.py` 使用当前 `EscalationEvent` 的 11 个 properties，
将候选 `model` 调用展开为字段表达式；字段及顺序与原 `wire(dict)` AST 完全相同，
函数中此前所有语句 AST 相同，候选语法 compile 通过。证据
`projection-verification.json`、`projection-before-cloc.json`、
`projection-after-cloc.json` 和前后完整产品文件快照均保留。

**界限及验证。** 这是对 RowsGateway 返回完整普通 dict 的静态字段等价证明。
不证明缺字段/恶意 Mapping 的异常求值时序、动态 monkeypatch、HTTP 响应、真实
数据库行为或性能。实施需 BE/调度 owner 执行事件创建/重复/通知缺失/终态降级、
分页排序及 Schema 响应回归，并以新源码 SHA 做 CI、审核和独立验收。此候选无需
改变业务决定，但不能由本 AI 自批其生产实现。

## 4. 路线 B：显式域适配描述，保留类型与守卫

**接口及文件。** 可将 `workflow.py` 的 command 构建（177–204）、三类 Gate 的
纯字段构建（96–107、131–139、151–160）、Context 与 Position 的纯字段构建
（162–176、205–208），交给领域边界中的私有 `CommandCodec.build(action,body)`
与 `ProofCodec.*`。描述只绑定已被服务验证的值；不能读取 HTTP 请求、自行查库、
把用户任意字段灌入 dataclass，或重排 81–95、109–130、140–150、215–218 的
归属、版本、D008、状态/经理和人力守卫。

**净预算。** 上述只是约 78 物理行的构建表面，不是 265 行 workflow 都可替换。
完整 registry 仍要声明字段别名、reference 组合、枚举转换、bool 计算、常量和
默认值；再加通用组装器、调用和导入，合理替代成本约 58–103 行。因此保守预算
为 **净增 25 至净省 20 行**，尚无完整原型证明正收益。此范围是工程估算，不能
并入生产主指标。只有完整原型含全部校验后仍净省，才值得 owner 接手。

`domain/commands.py` 53、`domain/models.py` 177、`services/codes.py` 82 与
`workflow.py` 265 合计 **577**；即便不合法地把四文件全删，仍达不到 1235。
这只是一个严格的局部上界，不是全工程不可压缩的证明。

**人的真实架构取舍。** 当前独立语义 Enum/冻结 DTO 与数字存储码是刻意的边界。
保持它们，通用 factory 不能凭反射自动删掉类型、正计数器、真实 bool、不可变
集合和状态合法性检查。若人选择共享一套规范化 IntEnum/DTO，同时由固定模块
门面隔离传输与数据库，可进一步消除一部分 Enum 映射和重复声明；但要明确接受
领域类型与共享契约的耦合，并逐项列出兼容接口。这不是 AI 可偷偷完成的“等价
改写”。把声明挪进当前排除计数的 JSON、动态生成类再称少源代码，也不计作收益。

**验证需求。** 命令构造的参数顺序和独立类型身份、非法 flags/counter/集合拒绝、
七态九动作、阻塞返回、证据门禁、当前轮次/SHA、D008 及更早错误优先、CAS、
审计和人力锁序，均需新准确源的针对性检查及 CI；旧绿结果不能覆盖这一改造。

## 5. 路线 C：持久记录创建策略共用，事务边界各自保留

**接口及文件。** 新的 persistence-owned 纯
`scan_run_values(*,run_key,rule_version,rule_snapshot,rule_hash,cutoff_at)` 只返回
初始化行，由 `ScanStore.start`（20–52）和 `EscalationFacade._run`（70–104）各自
执行原来的 insert/savepoint、重复恢复、规则冲突检查和事务。它不能私自 commit，
不能把两种错误类型合并，也不改变锁、UUID 或 cutoff 规则。

**真实原型结果。** 工具设计先提交 5ce6826 后才执行 `prototype.py`。两处构建
相同的 14 字段 payload，公共 helper 完整保留；把 helper 调用 AST 内联，并去掉
新增定义/import 后，**两个完整模块 AST 都与原文一致**。只做 AST compile，未导入
应用。固定 cloc 计入全部新层和导入后，两文件 **314→314，净 0**。
证据为 `verification.json`、`before-cloc.json`、`after-cloc.json` 和 before/after。

因此这个具体原型在“减少规模”目标下**淘汰**；共用初始化形状本身仍可作为将来
防漂移的维护选择。扩展到 outbox 时，业务事件与通用事件 payload、默认字段和
时刻来源并不相同；要保留参数/默认值、完整错误及调用，新层成本不能省略。
这条路线进一步研究的可信净预算仅 **净增 15 至净省 10**，不是 109+205 行都能删。

**人的真实架构取舍及验证。** 是否接受把 durable row 的默认策略集中由 DB owner
维护，是维护权责选择；不需要改变业务决定。若扩大为通用“版本化写入+审计”
协议，则必须由 BE/DB/消息/调度 owner 共同决定职责，不得用一个 helper 隐藏会话→
幂等→项目→成员→任务→关联记录的锁序，或成功/拒绝不同事务。实施后需验证重复
竞争、规则快照冲突、续扫、失败回滚、MQ 晚到/降级终态及精确数据库约束。

## 6. 是否足够及最小人类问题

三条路线的最乐观估算上界为 **20+20+10=50**，不是已证 50，也不是可直接实施
组合；即使全部成立，6335→6285，仍超 **1185**。唯一正向实测为临时净 5；即便
实施获准且等价回归成立，也只是 6335→6330，仍超 1230。前轮 namespace 净 33
没有在本轮实施或重复预支；本轮没有构造一条已证足够 1235 的架构路线。

需要人的最小明确选择是：**是否必须维持当前独立语义域模型与传输/存储模型的
隔离，还是允许共享规范化 DTO/枚举、同时保留模块门面和完整校验？** 若允许，先
由 owner 提交接口/错误顺序/锁序不变的完整预算原型，审查后再实施。即便允许，
本轮也不承诺它足以达标。若该边界必须保留，当前证据不足以授权大改凑数，N07
继续保持不通过；固定口径与既有功能均不能被 AI 静默放宽。

另一个可能改变约束的决定只能来自老师对任务书“有效代码”范围的明确原话及
总协调版本化记录；没有这个新决定，就保持现计数。本报告不请求删除功能、
移出 seed/migrations、把约束挪进不计数资源或压缩格式。

## 7. 过程真实性与交接

实际执行：产品静态阅读、AST 构造/比较、两次小范围 cloc、完整产品目录 diff。
未执行：产品单元/集成/HTTP/MySQL/MQ/性能/独立用例；未提供生产减少或发布批准。
本 AI 写了原型，不得作为后续生产实现的独立审批人。完整脚本及候选快照仅是
可审提案。未改计数脚本、规格、契约、DDL、产品和活动测试环境。

初次 worktree 路径误建于 Documents/ChatGPT，收到总协调纠正后用
`git worktree move` 保留分支及文件移回 Desktop 项目内，未删除他人工作。一次
`rg` 包含不存在的 requirements 目录而 exit 2，随后明确使用 specs/requirements.md。
曾创建一个纯静态映射子任务，因关键独立 operator 需要并行槽，立即中断并释放；
未接收其结论，不把它冒称独立复核。本阶段随后只由本岗完成。

本期 prompt ID 为 **P813-DEEP-PLAN-20261025**；改进点是先核抽象已存在的事实，再
给包含新层/校验/导入的净账，而非把文件/函数职责成本视作可删除预算。日志和
阶段 handoff 同分支交付；Issue #12 仅公开此岗范围及证据，不向独立测试岗发消息。

Issue #12 已实际发布本岗证据，comment 6396666903；只按精确 comment URL 回读，
正文逐字相等，未读取讨论时间线。元数据见 issue12-readback.json。阶段 1ea5d9f 已
push；后续本次回读记录作为另一个阶段提交，非产品变更。
