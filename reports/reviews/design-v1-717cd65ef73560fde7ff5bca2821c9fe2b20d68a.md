# 他岗契约与DDL设计审核 v1：不通过

## 1. 审核对象与基线

`Agent-Role: reviewer`；`Prompt-Ref: ROLE-reviewer-DESIGN-v1`。对象为PR #13 / Issue #12的他岗产品设计，head **717cd65ef73560fde7ff5bca2821c9fe2b20d68a**，base **1996d44425e09930b5ba3ae5391b728980241f55**。`gh pr view 13`实测该head且为draft。后端设计提交b893353c9bcf45e833f70f56bf6f72025f611271、数据库提交3c0d55ec854102c84d8a7b7e364ba0b34a2b819c已纳入此head。

以`git show <head>:<path>`读取提交内容，核对12份设计/基线文件与工作树字节相同。主要内容SHA-256如下；本结论不把未提交草案冒充提交。审核岗自身M0提交4b3d6e5及其协议/报告不属于本轮他岗设计放行范围。

| 文件 | SHA-256 |
| --- | --- |
| specs/contracts/openapi.json | 81b8ee7ea1af0937e42f72adff800313545c21b255b0ecdbaea784464b703ba8 |
| specs/contracts/README.md | 53ca560a31a8d1effc7a54c38dab47e7b29b9bb0cd47a33e09b84465e064f2de |
| specs/backend-design.md | 61163ed6b77cad7bce99f4fadd4533ca750f7304c0f2baf80ea7e9823a572ac4 |
| specs/database/field-dictionary.md | e1cf73fa3dd4c81369bd719789cb563e5c416c4494adea2fc804073448d83414 |
| specs/database/schema.sql | 73c265461d375e9314ed706f8faf1af2480f0167b13dc93c089967eb4ce067cb |
| specs/database/persistence-contract.md | 7b32344024aec51fd2d7c7af95ed4af40b7a3b23ee2b3e9df8580883da81a54b |

## 2. 需求映射

依据本地原始T44、requirements/business-rules v1及D001/D002/D003。D001是用户采用业务规则；D002、D003是协调者技术/质量约束，不冒称用户逐条原话。

| 要求 | 本轮设计依据及判定 |
| --- | --- |
| FR-01 / AC-01 | contracts/README:12,19-31,45-73及38操作Schema已定义三类输入输出/错误；C1—C4仍阻断冻结 |
| FR-02 / AC-02 | field-dictionary、schema及逐表表格见第4段；字段/类型一致，非全部设计已通过 |
| FR-03 / AC-03 | backend-design:31,36；reviews八段、版本化清单、必需通过项有证据，权限防自评；静态方向符合 |
| FR-04 / AC-04 | backend-design:42-52,91；persistence-contract:30-39；project锁串行查环、开始前编辑、计划前后差异已设计 |
| FR-05 | backend-design:34-36,48-50；persistence-contract:24-28；改期清空旧批准，评估绑定排期/交付轮次，经理实际决定 |
| FR-06 / AC-05、06 | backend-design:40-52,65-91；七状态/九动作、阻塞原状态、解除依据、CAS与成功审计同事务已设计 |
| FR-07 / AC-07 | persistence-contract:63-85；最高级、排期去重键、事件计数原子提交及同事件fallback/consumer去重已设计；C2需修 |
| FR-08 | backend-design:7-21及implementation-layout；注入门面/进程边界明确。产品CI待实现，不因本阶段没有产品代码而要求假覆盖率 |
| AC-08、09 / 安全与维护性 | contracts/README:75-89明确三类真实测量入口、分组P95和≤1配置+1模块的版本扩展方向；HTTP/性能/人日/覆盖率未验证，属于后续阶段 |

## 3. 范围与责任边界

只审核上述已提交设计以及需求/决定/目录约定；没有修改设计、实现或断言，不操作根Git索引，不读取或联系独立测试。报告和本岗日志/交接为新增证据，首次失败报告保留，后续修复另用新SHA复审。owner负责修改，总协调整合；本岗不修被审实现。

## 4. 接口与18表逐表设计判定

静态检查识别18表、35个FK、59个CHECK；字段字典与DDL逐列名称/类型/空值/默认完全一致；FK列类型一致且全部引用显式PK/UNIQUE键，AuditReason41项与API ErrorCode一一对应且无重复。该检查是文本结构核对，不是SQL解析器或MySQL执行证明。

| 表（schema.sql行） | 设计判定及证据 |
| --- | --- |
| users（7） | 静态通过：统一INT PK、ascii_bin用户名唯一、active TINYINT、Argon2id形状附加CHECK；完整hash解析/拒绝审计由持久入口承担（persistence:43） |
| service_accounts（21） | 静态通过：服务稳定ID独立、name唯一、active受限；不冒人类经理 |
| auth_sessions（31） | 静态通过：actor二选一FK、32字节摘要唯一、过期约束、个人scope空；撤销/共享会话锁已有文档设计 |
| projects（59） | 静态通过：统一PK/创建者FK/版本范围；创建经理同事务、项目图锁锚点（persistence:33-39） |
| project_members（73） | 静态通过：project/user唯一、roles_mask/active最小整型、软撤销历史；最后经理与活动负责人守卫（persistence:37） |
| iterations（92） | 静态通过列/约束映射：同项目唯一键、时间关系、capacity数组、季度小时/计划版本；全局时间域仍受C3阻断 |
| tasks（115） | 静态通过列/约束映射：同项目iteration/owner FK、四计数、阻塞字段成组、工时范围、同任务批准引用后补FK；全局时间域受C3阻断 |
| task_dependencies（167） | 静态通过：两端同项目FK、边唯一、禁止自边及反向索引；环由持有project锁的DFS防并发双向加边 |
| reviews（184） | 静态通过：version恒1、八段/10..100项形状、轮次/SHA/模板hash及同任务引用；模板精确覆盖/非自审/必需证据由服务校验 |
| release_assessments（211） | 静态通过：四风险形状、终态评审字段成组、同任务预案版本唯一；不可变文档/单次审定及当前排期/轮次守卫（persistence:26-27） |
| decisions（253） | 静态通过：同task/cycle/type唯一、同任务评估FK、按交付/回滚/返工的必填载荷CHECK；manager及已审预案版本由服务校验 |
| schedule_changes（286） | 静态通过：task/iteration二选一、同项目FK、版本前后+1、完整before/after及理由证据；全局时间域受C3阻断 |
| audit_events（312） | 静态通过：未知目标attempted字段无FK、已解析目标复合FK、数字原因映射、接受/拒绝成组；独立拒绝连接且不伪造更改（persistence:57-61） |
| idempotency_requests（342） | **不通过，C1**：scope唯一、owner租约/处理中与完成形状合理，但未给原请求ID的持久来源，无法完整落实重放溯源语义 |
| outbox_events（366） | 静态通过：稳定event ID、租约/confirm/fallback状态CHECK、任务复合FK、领取/恢复索引；网络调用在短事务外，fallback终态（persistence:77-84） |
| escalation_events（400） | 列/唯一/FK静态通过；**API映射不通过C2**：task/排期/级别唯一，rule版本不绕过去重，scan UUID映射有说明，但收件人输出域不覆盖全部合法成员 |
| notifications（425） | 静态通过：event/recipient唯一、事件三列FK、版本、read/handled分开及处理证据CHECK；fallback/consumer锁同一outbox且不覆盖已读处理状态 |
| scan_runs（458） | 静态通过：INT PK与BINARY16 UUID唯一、规则快照/hash、游标/心跳/终态时间；不是仅靠内存续扫 |

以上“静态通过”只表示所列设计层核对无阻断，不能替代领域实现、真实约束负向验证或迁移许可。

## 5. 业务正确性与四项阻断

**C1｜P1｜重放原请求ID没有持久来源；owner：database＋backend。** `openapi.json:19190-19227`要求Meta.original_request_id；README:24,41-43及backend-design:85要求回放原快照并重建meta。但DDL:342-364没有original_request_id/request_id或原审计关联列，field-dictionary:394明确response_body不含旧meta。createProject、Member、Iteration等成功data也不携audit_id，不能可靠从审计表反查原request_id。即使Schema允许null，也没有规定“重放时如何给原ID”，不能永远填null冒充可追溯重放。须持久保存原ID或明确快照内部封装/审计关联，并同步列字典、契约及恢复语义；不存Token/完整旧敏感meta。

**C2｜P1｜全部经理的合法收件人集合可能超出响应域；owner：backend，database/协调者对齐。** persistence-contract:67选择owner及所有active经理，成员接口/DDL没有项目人数上限；`openapi.json:22078-22102`却限制recipient_ids最多100、handled_count最多100。一个owner加100名不同经理是当前模型允许的集合，但完整事件响应必然不符合Schema；本岗Schema-only构造101收件人的合法形状事件，实际得到recipient_ids/maxItems错误。不得静默截断、漏通知或伪造计数。须选择并统一人数约束/错误，或扩大/分页表达，覆盖创建、历史查询与计数。

**C3｜P2｜API时间域超出所选数据库的承诺支持范围；owner：backend＋database。** `openapi.json:18721-18727`允许四位年份，实际Draft202012Validator＋FormatChecker接受`0001-01-01T00:00:00Z`及一份开始/结束有序的完整TaskCreate。持久契约:10及任务/迭代表仅承诺DATETIME(6)。[MySQL 8.4官方时间类型手册](https://dev.mysql.com/doc/refman/8.4/en/datetime.html)明确DATETIME支持范围从1000年起，较早值不保证可用。当前没有统一可存时间域及相应422定义；需收窄共享类型/语义验证并同步只读契约校验，考虑扫描时间运算边界。此结论是契约/文档支持域不一致；**没有执行MySQL插入，未声称已测得驱动失败**。

**C4｜P2｜错误注解与可触发行为不一致；owner：backend。** README:28,41规定GET及只读契约校验不走幂等。提交中12个GET（例如getProject）及validateContractPayload的`x-business-error-codes`仍列IDEMPOTENCY_CONTENT_CONFLICT/IN_PROGRESS，GET responses又不提供409。`/dictionaries`明确不返回项目业务数据、没有project参数，却在403（openapi:1157）声明可触发PROJECT_ACCESS_DENIED，另有未说明触发条件的RESOURCE_NOT_FOUND。README:47“已按操作收窄”尚不成立。须逐操作对齐注解、实际响应码及可触发条件，删除不适用分支或提供真实语义，不能为了AC-01制造假的错误用例。

其他已具依据的设计：成功任务/CAS/审计/outbox/幂等完成同事务，拒绝先回滚释放连接再独立提交，503不假称留痕；会话→幂等→需要时project→成员→任务→子记录固定序；图变更project锁串行；MQ模糊confirm、late consumer与fallback锁同一event，UNIQUE(event,recipient)且保留read/handled；新增评审项/升级level走版本化数组而不是固定DDL枚举（README:87-89、persistence:70-85）。这些是静态设计成立的依据，运行正确性仍待后续验证。

## 6. 已执行证据与边界

- `git show 717cd65...:<path>`＋SHA-256比较：12份提交文件与已审工作树内容一致；包含数据库三件，完整哈希见第1段。
- 根`.venv/bin/python`对**该提交**OpenAPI执行`openapi_spec_validator.validate`：通过；31路径/38操作。规范有效不表示业务分支有效，C4就是规范校验无法识别的语义矛盾。
- Python只读结构核对18表列字典、FK列类型/唯一目标及41错误码映射：未发现漂移；不是MySQL执行。
- Draft202012Validator＋FormatChecker只做Schema例值核对：101收件人事件因maxItems被拒；0001年完整TaskCreate被接受。没有HTTP请求或产品测试结果。
- `gh pr view 13`在发布前后反复核对base/head/draft；随后实际发表[Issue缺陷摘要](https://github.com/HJY147/t44-dev-trace/issues/12#issuecomment-6358801740)及[PR COMMENT](https://github.com/HJY147/t44-dev-trace/pull/13#pullrequestreview-5624655316)，Review回执commit_id与本head一致。对该完整SHA实际发布`reviewer/stage=failure`，target_url指向Issue摘要；status ID 57066080416。命令/退出码/原返回见`agents/reviewer/evidence/design-gate-717cd65.json`。没有APPROVE、success、合并、push或Git索引操作；实际合并阻断实验由总协调后续执行，不在此冒称已验证。
- 未运行DDL、SHOW CREATE TABLE、事务/权限/并发/MQ故障、HTTP契约、覆盖率或性能。它们是后续实现阶段的验证项，**缺少这些运行结果本身不是本轮四项缺陷的依据**。

## 7. 十项清单与门禁判定

| 项 | 本轮设计判定 | 证据 |
| --- | --- | --- |
| 1 身份与版本 | 通过 | 完整SHA、PR远端head、12文件内容比较；自有M0排除 |
| 2 需求与范围 | 通过（设计映射） | 第2段；用户与协调者决定分别归类 |
| 3 接口兼容 | **不通过** | C1—C4，合法状态不能完整表达、错误语义不一致 |
| 4 数据库兼容 | **不通过** | 18表逐表核对；C1缺持久源、C3支持域待统一 |
| 5 状态机 | 通过（静态设计） | backend:40-52，四计数/批准失效及运行时拍板守卫 |
| 6 权限与数据边界 | 通过（静态设计） | 当前成员范围、manager不越权、非自审、会话撤销锁；运行未验证 |
| 7 事务与并发 | 通过（静态设计） | persistence:30-61，成功/拒绝独立边界、固定锁序及查环 |
| 8 幂等与故障 | **不通过** | 原子/去重方向具依据，但C1重放溯源、C2全部接收者表达仍阻断 |
| 9 测试证据真实性 | 通过（范围真实性） | 规范/静态命令有真实结果；明确未执行产品测试，无虚构通过 |
| 10 门禁与可合并性 | **不通过** | 四项设计阻断；本轮不能放行。产品CI/运行结果待后续，不以缺代码要求假覆盖率 |

## 8. 结论与迁移前提

**717cd65ef73560fde7ff5bca2821c9fe2b20d68a的契约/DDL设计不通过，不能据此冻结或合并。** C1—C4由责任岗修复后给新完整SHA；本报告原样保留，新版本另出复审报告，不把“以后会修”记为本版通过。

迁移前需完成设计修复与新SHA逐表复审、契约/字段冻结；再由另行授权的迁移阶段选择明确的空schema、MySQL8.4、UTC/严格模式、启用FK/CHECK及备份/恢复措施，执行真实DDL并核对SHOW CREATE TABLE/信息模式。这里建立迁移前提，**本轮没有执行或批准DDL**。产品CI、HTTP/事务/并发/故障和性能验证按后续阶段真实取得，不能由本静态报告替代。
