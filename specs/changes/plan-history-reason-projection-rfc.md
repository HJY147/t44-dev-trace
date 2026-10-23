# Issue 28：计划历史理由的只读投影设计

状态：设计提案；未准入生产实现、未部署、未执行HTTP/MySQL回归。基点为 `982623381e9cfa1d6a7bad1de222e160503cbf08`，分支 `codex/backend-plan-reason`。本文件是内部实现设计，不修改14项冻结规格、DDL18表226列、API版本/路径/字段或历史审计。

## 问题和实际来源

公开问题是“所检查任务的历史视图漏显已保存理由”，不是理由丢失。依据仅Issue28、已明确公开的v2阶段报告、当前源码与前端真实协商；未读独立私密脚本/SQL/截图，未连接其数据库。

- `Projects.schedule_diff`把原文reason、evidence、changed_by、changed_at及完整前后plan写入schedule_changes；task分支才向audit before/after追加schedule_version和五项计划。`Runtime.audit`随后在同一成功事务保存这些差异。
- `Business.listProjectAuditEvents`当前只序列化audit_events，不关联schedule_changes。AuditEvent没有自由文本顶层reason，reason_code是机器错误码。现有after条目允许 `{field: string(1..100), value: string(0..2000)}`，最多50条，足以承载理由。
- `changeTaskPlan`及action9返工调用task分支；`changeIteration`调用iteration分支，仅修改该迭代，没有批量改任务计划，也没有自动为任务生成历史。旧iteration审计只有通用version差异，没有iteration_id、plan_version和完整plan。
- 前端已在Issue28确认：通用RecordView虽不截正文，但Diff.field未中文映射，value会走通用日期/操作名格式化。需要另阶段识别理由条目、标题“原因与决定依据”、按原文纯文本呈现；不能声称后端加条目后现UI已正确。

## 数据出口与新写入（候选，未应用）

保留现GET `/api/v1/projects/{project_id}/audit-events`、原过滤/排序/分页和AuditEvent结构。唯一出口是该条审计的after数组多一个 `{ "field": "reason", "value": "用户原文" }`。不使用reason_code，不加reason_source/缺失状态字段，不把说明文字伪装成用户理由。before不伪造“上一次理由”。

在现有schedule_diff共享生产点向c.after追加一次reason；任务改期、返工、迭代修改均使用原c.body.reason，与schedule_changes/任务或迭代CAS/成功audit/outbox/幂等完成快照同一事务。失败/重放不能新增audit或重复理由。新iteration理由只属于iteration audit，不向同迭代任务扩散。新事件的reason已有输入上限2000字符，完整保存含换行/引号/中文/日期样式文本，不trim、不摘要、不HTML执行。

原幂等结果快照/已保存审计不回写；旧成功重放也不补写reason。历史GET投影由当前数据独立构造，不改变旧HTTP写响应快照，不宣称重放等于再次执行写入。实现必须沿用现有鉴权、锁序、CAS、成功原子和独立拒绝审计。

## 旧任务历史：可核对关联的全部条件

设审计a、候选schedule_changes行s。先判定a是成功(outcome=1)、human(actor_kind=1且actor_id非空)、task_id非空的计划操作：`changeTaskPlan`；或`transitionTask`且before.state=7/after.state=2的返工。其它transition、失败审计、createTask、非计划操作不参与。状态7→2仅作识别既有action9，不增加状态出口。

同时满足下列条件才把s.reason追加到**响应副本**，任何一项不符都不投影：

1. a.project_id等于已授权路径项目，s.project_id等于它；s.task_id=a.task_id，s.iteration_id为空。禁止按当前task所属迭代、标题或相邻时间寻找。
2. a.before/after中的schedule_version、version各恰一条，值是既有生产者的规范正整数字符串。schedule to=from+1且等于s.from_version/to_version；task version也恰+1且before.version=a.expected_version。两种version不能混用；不要求task.version等于schedule_version，不查当前task版本替代历史。
3. a.actor_id=s.changed_by；a.created_at与s.changed_at在UTC下精确到DATETIME(6)相等。没有时间窗口/毫秒取整/最近一条；不能仅凭actor+time关联。a.evidence与s.evidence的结构和值也完整相等，不拉取证据链接。
4. 两侧计划的五个字段 `planned_start/planned_end/estimated_hours/buffer_hours/delay_contingency` 各恰一条；与对应s.before_plan/after_plan的**完整**五键快照逐项相符。比较遵循现生产者 `str(plan(...)[field])`：UTC时间已有六位Z字符串、小时由quarters/4生成如`8.0`；不宽松强转/四舍五入/忽略应急说明。历史导入若采用另一种等价数字/时间拼写，也保守不投影。s的快照缺键、额外键、非法类型或任一相关audit重复字段都拒绝匹配，不能只比较日期。
5. s.reason为非空白字符串、长度≤2000；a.after没有已有reason且追加后条目数≤50。已有恰一条合法reason优先原文返回，不替换/不查关联；已有reason重复/非法不“修好”原审计，保持原记录和原响应校验规则；重复field本身并不违反现Schema，不能谎称Schema会替我们消歧，前端也不得从多个reason任选一个当唯一理由。
6. 候选结果恰一行；若持久层返回相同pair多行、跨项目/跨pair或其它结构违约，作为持久层故障处理，不能挑第一条。s的唯一键(task_id,to_version)及from+1约束是已存在证据，不新增DDL。

必要性/充分性范围：以上是本提案采用的保守充分条件，并是投影算法的必要条件，不声称它们是所有真实历史的最弱数学必要条件。对于API按现有生产点原子写成、唯一约束有效的历史，task+排期版本唯一确定变更事实，actor/time/完整plan/evidence交叉核对可防止串接另一操作；schedule_version返工也递增不复用。不具备audit_id/request_id外键，因此对任意手工导入/伪造且字段完全相同的历史，不能证明请求级密码学因果，也不承诺全部旧记录可恢复；不为提高恢复率放宽规则。发现数据矛盾保持缺失或明确故障，不从“看起来接近”推断。

## 迭代/批量/缺失边界

旧changeIteration没有足够公开关联信息，且schedule_changes无audit_id/request_id；即使同一操作者同一微秒，也不能定位iteration，故不投影。任务页按task_id过滤，本来不会拿到task_id为空的迭代审计。若某客户端依次批改多个任务，按每条独立task+schedule pair核对；不存在可复用的“迭代批改总理由”。未来真正批量API不在本次范围。

没有候选、字段不完整/不符、旧格式、after已满50条，均原样返回该audit且没有reason条目，不改变items/total/顺序，不制造空理由/占位理由。前端在**相关成功计划记录旁**提示“此历史记录未提供可核对的变更理由”；不能给所有审计加警告。相关范围：成功changeTaskPlan；成功transitionTask且明确7→2；项目总历史若展示成功changeIteration也可同样标缺失，但不得称它是任务改期。无法识别返工的残缺旧transition不猜。该提示是UI，不写进after.value或数据库。

## 分页、批读与数据库岗位接口提案

保留page/page_size≤100及原sort/total语义。先用现过滤/顺序读取当前页≤100条audit，再提取需要核对的去重(task_id,to_version)≤100。页count仍原条件。0个pair不执行补充SQL；有pair只增加**一个**参数化只读批次，不逐行查库，也不扫描整个项目历史。只在原GET自有UoW内执行普通非锁定读，不新增S/X/跨事务身份缓存；只读RC不同语句快照的既有语义保持。历史行不可变、两表同事务提交，投影不是新写事务。

提议DB owner在RowsGateway提供固定有限入口（本轮仅需求，不由后端绕过gateway写SQL）：

`task_schedule_changes(project_id: int, pairs: tuple[tuple[int, int], ...]) -> list[dict]`

- project_id/task_id为合法INT UNSIGNED正ID，to_version为现Version正整数；拒绝bool/字符串等非内部类型。最多100个输入pair；重复pair先去重，空集直接[]且无execute。非法输入沿StatementRejected，不形成新HTTP业务码。
- 固定schedule_changes表与列；项目谓词AND(task_id,to_version)精确tuple-IN或参数化OR，AND iteration_id IS NULL。**不是**task_id IN × to_version IN然后limit100；那会产生交叉行、截掉真匹配。
- 返回已按现codec解码的完整schedule_changes行，按(task_id,to_version,id)稳定排序。由于现唯一键每pair最多一行，硬上界为distinct pair数≤100；不靠任意LIMIT隐藏重复。结果重复/越界/范围违约应显式PersistenceUnavailable，不返回截断“成功”。唯一约束正常时无需额外SQL验证全库。
- 所有值绑定、标识符固定，不接受原SQL/锁参数/动态排序，不查另一个项目。DB SQL失败沿现PersistenceUnavailable/脱敏异常，主GET UoW先退出，再由原Runtime独立拒绝audit；不能把数据库失败降成“历史理由缺失”。不改原RowsGateway通用rows调用语义、迁移、DDL或其他业务存储。

账本：原audit页SELECT+COUNT=2条业务SELECT；本方案为2或3，最多1个补充execute，与page_size无N+1增长；鉴权SELECT/UoW不减、不改，不宣称性能优化。计划快照含长应急说明，行数/字段字符上界明确但不是很小的固定字节包；不truncate大值、不把全项目历史加载内存。无跨请求cache。

## 前端协作及样例

`agents/backend/plan-reason-design-examples.json`包含新持久reason、旧raw+匹配schedule+响应投影、错actor/时间/版本/计划/项目、reason缺失、旧迭代不可关联、50条满页条目等合成样例。它们是数据/设计例子，不是已实现matcher或真实HTTP记录。

前端须由frontend owner另实施：识别after中field=reason，标题“原因与决定依据”，value作为原文text（含2000字符、换行、以日期或操作名开头、HTML样式字符串）；不要通用日期/operationLabels变换。审计actor/time/证据/前后计划继续显示。已有重复reason条目可保留在原始明细中，但不能标成唯一可核对理由；相关记录仍提示无法核对。缺失提示按上节范围，旧列表总数/分页/所选task不变；不能假造API reason_status字段。

## 最小代码预算与准入后的红绿计划

本阶段产品净LOC=0，无未应用生产patch；以下是静态估算，不能冒充cloc实测或解决6108超5100：后端schedule_diff约+1..3有效行；页批量编排/严格配对与投影共约+55..80、替换现序列化约-12..18，后端净约+38..71；DB有限pairs入口约+18..30（由DB owner复核）；FE理由专用展示/缺失提示约+10..20（由FE owner复核）。总预估+66..121，范围反映未实现校验/复用选择；实现后按原统计口径报告真实净值，不压排版或省安全条件凑数。本次是正确性修复，非减少源码任务。

root准入并交付DB有限入口后，复用现986/985必要断言，暂不新增873脚本：

1. 旧源真实红：新task改期与返工GET缺reason；合成旧完整历史缺投影；2000字符和日期/操作名理由原文。保留版本/状态/前后五项/证据、成功原子和重放断言。
2. 新写成功：taskplan/rework/iteration的reason同成功audit/schedule事务；受控失败回滚不产生半条reason；相同key重放不新写/不重复条目；旧完成快照不补写。公开读响应原Schema通过。
3. 精确历史矩阵：每个条件分别失配；缺字段/重复字段/小时字符串差异/不同项目/相同时间另一task/相同task不同排期；无理由/超限/满50条均不猜不截；已有reason不被覆盖。旧迭代无可证关联不投影，项目历史不污染task历史，非计划/拒绝审计不标理由。
4. 真MySQL自有t44_test独立合成fixture：2条相同to_version不同task、交叉pair干扰行、100条页上界/多个分页排序、空pair0补SQL/非空1批SQL、返回最多100；跨项目鉴权先拒绝，无按行查询。匹配前后immutable audit原JSON/hash及schedule原值完全不变；DB批读故障仍503并独立audit，不假装无理由。不得清共享表/读独立库。
5. FE owner做纯文本/完整长文/定位缺失提示回归，并由总协调另排真实UI；本岗开发测试不冒独立验收。完整新源CI仅实现后按调度一次，本设计阶段不跑CI/负载/真实SQL/HTTP。

尚待：root设计准入；DB owner确认有限批接口；前端正式实现派工；随后真实红绿、精确新源审查/CI/独立复测。原A的437CI仅属于7584，不移植到此未实现设计；性能与源码规模缺口继续保留。
