# T44概要设计与详细设计报告

版本：M2可审工作稿 v0.2。**非最终验收。** 本稿描述冻结1.0.0与集成checkpoint `265d89bd004de626a025d7efe7102fe68b5b2dd3`的实现；新联调证据按准确SHA另补。公开稿不含私密封面个人信息，日期留空。图表在M2补画，不追溯声称开发前已全部形成。

Agent-Role: documentation
Prompt-Ref: ROLE-documentation-M2-QUALITY-v1

## 1 设计依据与演进

需求见[SRS](requirements-report.md)。早期规范在717cd65被判C1–C4不通过，修复后bc0cd34限定技术复审通过；用户D004采用后，`ae60dc37fdaefecaca33e734a354add6ba9ebe29`冻结1.0.0并派完整实现。M1仍待Q002的历史commit不改写；当前不再把Q002列为待采用。冻结只证明设计准入，不证明软件测试/性能/独立验收通过。

本报告分“概要设计：模块/进程/边界”和“详细设计：数据/函数/协议/时序/异常”，再给模块测试与联调修复。冻结11文件只读，真实结果、历史路径和后续tmp迁移见[M2收集](../../docs/reports/M2-collection.md)。

## 2 概要设计

### 2.1 候选方案和选择

| 维度 | A Vue+FastAPI+MySQL+RabbitMQ+APScheduler | B Vue+FastAPI+自部署Supabase PostgreSQL/Auth+MQ/调度 |
| --- | --- | --- |
| 性能可验证性 | 直接SQL/事务/锁路径可测；当前采用 | 多组件调用和自定义状态/通知仍需测，无本项目对比结果 |
| 成本 | 自建鉴权/运维，单应用机加独立发压端规划 | 可复用认证能力，但自部署仍承担服务器/备份/安全；没有实测成本优势数据 |
| 可维护性 | 对应责任岗和门面边界明确，故障注入可定位 | 组件/版本联动更多，通用CRUD仍不能绕过状态机 |
| 取舍 | 任务书单机/单体及项目技术基线采用A | 保留比较，不宣称B不能实现；不使用平台宣传替代测量 |

[独立architecture.md](../../docs/architecture.md)补齐两组候选比较的时间、性能/成本/可维护性依据及Java/Spring补充候选；本节为概要摘要。

8vCPU/16GB应用机等规格仍是规划，不是已购/已压测或达标保证。项目不拆业务微服务，不做多地域，不因多进程改变单体分层定位。

### 2.2 模块、进程和部署边界

```mermaid
flowchart TB
  UI[浏览器 Vue业务页面] --> Nginx[Nginx 静态文件与同源api代理]
  Nginx --> API[FastAPI API进程 配置4 workers]
  API --> Services[Business门面与Runtime事务编排]
  Services --> Domain[纯domain 状态机与typed命令]
  Services --> Rows[注入UoW与RowsGateway]
  Rows --> MySQL[(MySQL 18表)]
  Sched[独立APScheduler进程] --> Scanner[Scanner与EscalationFacade]
  Scanner --> Services
  Worker[独立DeliveryWorker进程] --> Store[OutboxStore]
  Store --> MySQL
  Worker --> Rabbit[(RabbitMQ)]
  Rabbit --> Worker
  API --> Notify[NotificationFacade]
  Notify --> Rows
```

当前组合根`api.create_app`装配Runtime/Business，默认接消息与升级门面；API多worker不各自启动扫描器。`python -m t44.messaging`和`python -m t44.scheduling`独立运行，Compose配置不是已完整部署成功的证明；部署私密服务身份/共享锁和真实镜像构建仍按部署岗本轮证据核对。

| 模块 | 真实入口/职责 | 不越过的边界 |
| --- | --- | --- |
| frontend | src/api.ts、workspace.ts及业务组件；同源请求/错误/版本/幂等交互 | 不自行判权、决定状态出口或运行升级定时器 |
| API/Runtime/Business | api.create_app、Runtime.execute、Business.dispatch | 鉴权/Schema/幂等/事务/统一错误收口；不直接创建表或改他岗模型 |
| domain | domain.state_machine.decide及typed commands/models | 纯决策无IO，可信GuardContext由业务加载，内部Enum不等于数据库码 |
| persistence | Engine/UoW/RowsGateway、migrate/check_schema、OutboxStore/ScanStore、seed_demo | 参数化/锁/CAS/原子能力，业务合法边和证据语义由服务负责 |
| messaging | NotificationFacade、DeliveryWorker、PikaBroker | 通知列表/已读/处理、confirm/消费/fallback，不另建通知系统 |
| scheduling | EscalationFacade、Scanner.run/tick、build_scheduler | 版本化规则/最高级/扫描续扫；不绕Runtime直接改任务状态 |
| deployment/CI | compose.yaml、Dockerfiles、ops.py、product.yml和ci脚本 | 明确目标运维与真实检查，不伪造产品通过、不修改验收条件 |

依赖从组合根注入工厂/门面；数据库连接、消息连接不在领域函数内部随意构造，网络等待不占业务事务锁。具体签名与源文件在[M2追踪](../../docs/reports/M2-traceability.md)。

## 3 详细设计

### 3.1 状态与稳定编码

SRS状态图完整列出七状态九动作及阻塞原态返回。`services/codes.py`显式映射API/持久状态1..7、动作1..9、角色/责任环节及41个审计错误；不得依赖Enum声明顺序。`Workflow.transitionTask`把冻结码转换为typed命令，调用`domain.decide`，再在当前UoW持久化结果。

| 版本/证据 | 写入与失效规则 |
| --- | --- |
| task.version | 每任务关联成功写CAS+1；同键重放/业务重复升级不增 |
| schedule_version | 改期/返工+1；升级唯一键与上线评估绑定它 |
| delivery_cycle | 返工+1，旧交付/回滚批准不用于新轮 |
| review_cycle | 评审拒绝+1；返工重置1，旧评审保留但无效 |
| review对象SHA/模板 | 评审不可变、匹配当前对象及轮次；最低非owner守卫不证明真实作者 |
| assessment.version/排期/交付轮次 | 文档不可变、一次审定；改期撤销旧预案批准，不撤销同轮代码评审 |
| notification.version | 已读/处理CAS，只改通知，不改变task.state |

### 3.2 核心ER和存储约束

```mermaid
erDiagram
  PROJECTS ||--o{ TASKS : contains
  TASKS ||--o{ TASK_DEPENDENCIES : task_id
  TASKS ||--o{ TASK_DEPENDENCIES : depends_on_task_id
  TASKS ||--o{ REVIEWS : evidence
  TASKS ||--o{ RELEASE_ASSESSMENTS : risk_plan
  TASKS ||--o{ DECISIONS : human_decision
  RELEASE_ASSESSMENTS o|--o{ DECISIONS : optional_assessment
  TASKS ||--o{ OUTBOX_EVENTS : persistent_intent
  OUTBOX_EVENTS ||--o| ESCALATION_EVENTS : escalation_only
  OUTBOX_EVENTS ||--o{ NOTIFICATIONS : per_recipient
  TASKS {
    uint id PK
    uint project_id FK
    int version
    int schedule_version
    int delivery_cycle
    int review_cycle
    tinyint state
  }
  TASK_DEPENDENCIES {
    uint id PK
    uint task_id FK
    uint depends_on_task_id FK
  }
  REVIEWS {
    uint id PK
    uint task_id FK
    int delivery_cycle
    int review_cycle
  }
  DECISIONS {
    uint id PK
    uint task_id FK
    tinyint type
  }
```

图选择核心及通知关联，不声称只存在这些表；完整18表226列及FK/CHECK/索引见冻结字典/DDL。`UNIQUE(task_id,schedule_version,level)`约束业务升级一次；`UNIQUE(event_id,recipient_id)`约束通知记录一次；outbox与escalation可选1:1，普通变更事件没有升级ledger。决定的assessment引用可空，例如返工，图不把所有决定都画成必需预案引用。

真实MySQL8.4已迁移/重复校验18表，并有Rows/约束/并发局部结果；SQLite玩具表仅覆盖通用生命周期，不能替代MySQL证据。列级CHECK/FK不负责合法状态边、图环、角色或证据真实性。`cli migrate --database`有明确目标；不在启动时create_all偷迁移。

### 3.3 成功、拒绝与幂等时序

```mermaid
sequenceDiagram
  actor User as 项目参与者
  participant API as api endpoint
  participant RT as Runtime.execute
  participant Biz as Business及Workflow
  participant DB as MySQL经UoW和RowsGateway
  User->>API: action expected_version 幂等键 证据
  API->>RT: 结构化Call及validate
  RT->>DB: authorize与短事务claim
  alt 同键同内容已完成
    DB-->>RT: 历史data和response_request_id
    RT-->>API: 重放 新meta
  else 当前owner继续执行
    RT->>DB: 事务内重核会话 幂等锁 项目/成员/任务锁
    RT->>Biz: dispatch与domain守卫
    alt 合法且版本匹配
      Biz->>DB: CAS业务写
      RT->>DB: success审计 outbox COMPLETE快照
      DB-->>RT: 同一次COMMIT
      RT-->>API: 当前成功结果
    else 业务拒绝
      DB-->>RT: 主事务ROLLBACK并释放Session
      RT->>DB: 独立拒绝事务 审计及错误快照
      DB-->>RT: 独立COMMIT或审计失败
      RT-->>API: 约定错误或503且不谎称已审计
    end
  end
  API-->>User: Envelope与安全错误
```

`Runtime.execute/claim/complete/rejection/locked_scope`是实际入口。成功业务行、成功审计、应发事件、幂等COMPLETE及response_request_id同事务；拒绝先释放失败UoW，再独立提交拒绝记录和快照，不写task/成功outbox。提交确认丢失保留503 TRANSACTION_UNCERTAIN，沿原key恢复；cleanup rollback不能证明服务器未提交。C1修复的response_request_id是最终完成者来源，重放meta不复用旧凭据或把历史task快照当最新版本。

### 3.4 并发与依赖图锁

实际锁序为会话→自身幂等行→需要时project→成员按ID→任务按ID→子记录；`locked_scope`为依赖/开始/解除/返工等图一致性操作先锁project并锁前驱。图变更在同一项目锚下串行DFS，拒绝并发A→B/B→A形成环；任务更新带expected_version条件，仅一不同请求成功。不能在先拿task后再补拿project造成反序。

| 风险 | 机制 | 必须验证 |
| --- | --- | --- |
| 同版本不同键竞争 | task CAS和同事务证据 | 真MySQL多连接一次成功、拒绝不改现状 |
| 同键重放/异参/过期owner | scope唯一、hash、行锁/owner token、完成快照 | 不能租约到期即并行提交，提交不确定用原键恢复 |
| 项目成员撤销与在途写 | 会话/成员锁序与事务重核 | 权限过期不被长缓存绕过 |
| 并发加边与开始 | project锁、前驱按序、DFS | 自边/跨项目/环、依赖回滚后的开始/返工守卫 |
| 拒绝审计故障 | 独立UoW，503/audit_id=null | 不因主事务回滚丢拒绝，也不在存储不可用时声称已持久化 |

DFS为O(V+E)，检查D个前驱为O(D)，若应用另排序锁ID为O(D log D)；实际SQL计划/锁等待不能由复杂度代替。死锁/超时只有限重试完整事务并保留原key/hash。

### 3.5 扫描、outbox与降级

`Scanner.run/tick`加载真实版本化规则和原文hash，固定UTC cutoff并keyset分页；`EscalationFacade.create`经Runtime在锁内重验任务/排期/规则，只选当前最高档。20任务、重扫、改期与CLI退出后续扫已有调度模块证据；不是400并发性能结论。

```mermaid
sequenceDiagram
  participant S as Scanner
  participant RT as Runtime及EscalationFacade
  participant DB as MySQL
  participant W as DeliveryWorker
  participant MQ as RabbitMQ
  S->>RT: 候选 version schedule_version rule_version run_id
  RT->>DB: 原子事件 ledger 计数 审计 outbox
  DB-->>RT: COMMIT或已存在created=false
  RT-->>S: 确定结果后持久游标
  W->>DB: 短事务claim租约
  W->>MQ: 业务事务外publish mandatory confirm
  alt confirm ACK且无return
    W->>DB: 核token标confirmed
  else 失败或模糊确认
    W->>DB: 同outbox锁下补缺失fallback通知并置终态
  end
  MQ-->>W: 可能重复或晚到的delivery
  W->>DB: consume 同event锁 只插缺失通知 保留read/handled
  DB-->>W: COMMIT
  W->>MQ: basic_ack
```

`OutboxStore.confirm/consume/fallback/recover_confirmed`与`DeliveryWorker.cycle`对应图中入口。consumer/fallback共用outbox锁及通知唯一键；confirmed长期缺收件人会补待办，公平性修复避免完整事件挡住后续缺失项。普通business.changed失败重试，不伪造无收件人待办。confirm不是用户已收到；fallback终态同事件恢复不二提醒，新事件正常走MQ。

扫描伪码：

```text
持久start或resume run，记录cutoff和规则原文hash
for keyset_page:
  elapsed_us = 整数微秒(cutoff - planned_end)
  level = 最高匹配规则  # 不构造end+24h，不截断完整收件人
  Runtime执行版本重验和UNIQUE(task,schedule_version,level)
  新建则事件/outbox/计数/version/审计/幂等同提交；重复不再增加
  仅在结果确定后推进持久cursor
```

N任务、L规则、K事件、历史E、收件人R_i时，直接匹配O(NL)，索引去重通常O(K log(E+1))，展开O(ΣR_i)，分页内存O(B+R_max)；v1三档可视L常量。不能把整次扫描写O(1)。阻塞不暂停；rule_version不加入硬去重键绕过同排期同级一次规则。

## 4 各模块测试与集成证据

| 模块 | 已发布/实际收件范围 | 不能推出 |
| --- | --- | --- |
| frontend | 21交互测试、19源文件行92.21%；真实MySQL浏览器七态/改期/评审/评估/审计与1440/390 | 当前通知链尚需对应最新后端再验，非独立验收/性能 |
| backend | 纯domain106、实际HTTP/局部MySQL、TCP烟测；新收件报告全t44第二轮314通过/3本机Rabbit跳过、行87.78% | ec82已正式交接；265d89b四job CI成功另列，均非独立验收/性能 |
| database | 18表迁移/Rows/约束/Outbox/Scan/seed；SQLite/mock与真MySQL分批记载 | synthetic 40项目/6000任务等不是人类评审事实；不是压测 |
| messaging | 本岗28通过/3本地Rabbit未跑，11真MySQL；早期精确SHA上3真Rabbit托管CI通过 | 早期run不代表最新全产品CI；消费记录唯一不等于MQ网络恰一次 |
| scheduler | 最终107通过，其中22真MySQL/ASGI/CLI；20超期/重复/进程退出续扫 | 无本机Rabbit网络/400并发/独立验收结论 |
| deployment | 历史11安全+6守卫，当前23本岗guard/config及Ruff/actionlint；f052接线已发布，Docker job39932416571进行中 | 配置或修复commit不等于镜像构建/启动/恢复完成 |

每模块的入口、命令/原始结果、未跑项与FR对应见[M2追踪矩阵](../../docs/reports/M2-traceability.md)；不要相加不同版本测试数伪造一个全局总数。测试已由5e07887迁至tmp/999_递减路径；当前入口见映射，旧日志原命令不改写。

## 5 已发生的联调修复与尚缺结果

- 稳定码：实际错误/状态/动作/角色映射摆脱Enum顺序，反向映射和重排回归留证；不是新增v1枚举语义。
- seed规则：全量初测312通过/2失败/3跳过定位旧rule_version字段；数据库e06ac3b修复适配冻结规则metadata，二轮314通过/0失败/3跳过已由ec82最终交接确认，不抹掉初失败。
- 通知依赖：门面由缺失变为默认实现后，旧503故障用例需显式移除依赖；保留故障503并验证正常200，不把新功能当失败或降低断言。
- confirmed恢复/claim公平性：数据库先留真实失败、同例修复后复测，避免只轮到完整事件而饿死缺失通知；不以发布确认当消费成功。

main要求reviewer/stage/static/contracts/coverage/frontend；准确新head需重审，旧设计复审不放行新代码。正式400并发10分钟/P95/吞吐、有效LOC3500–5100（当前仍需压缩核算）、完整Docker集成/备份恢复和独立验收均按最终证据补齐。本稿和学生研究材料都不代替这些结论。

M2新CI证据：265d89bd004de626a025d7efe7102fe68b5b2dd3的[run39931640641](https://github.com/HJY147/t44-dev-trace/actions/runs/39931640641)四job static/contracts/coverage/frontend成功；归档[JUnit汇总](../../records/ci/39931640641/junit-summary.json)显示覆盖率整套317通过、0失败/0错误/0跳过，whole Python行2399/2724=88.07%，前端行308/334=92.21%，见[M2回执](../../docs/reports/M2-ci-snapshot.json)。这是准确SHA的托管MySQL/Rabbit证据，不代表独立验收、400并发性能、完整Docker或代码规模通过。
