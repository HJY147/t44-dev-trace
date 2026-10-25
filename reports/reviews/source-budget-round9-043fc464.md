# N07 第九轮：大模块的语义去重与库替代核查

本岗为 AI reviewer，提示词 ROLE-reviewer-ROUND9-v1。准确基线
`043fc464acd327f6b7639e89dbe4f603fc524880`，固定应用口径 **5875行/65文件**，
其中后端4776、前端1099；距5100缺775。消息候选另经限定审核，整合后才可能5862，
仍缺762。本报告**没有产品实现、没有新的生产节省，也没有已证明足够775的方案**。
这不构成工程不可压缩的数学下界；只是本轮可复核的结果，不继续预支文件尺寸。

## 1. 实际核查方法

逐路径阅读 seed、migrations、rows、runtime、schema、engine、API、contracts、
domain、主要CRUD服务及调度facade；核对上两轮公开架构方案和DB已完成V2。
对准确已提交全部backend Python做只读AST扫描：精确相同的连续三个语句只有2组，
≥5个字面键的同形记录只有1组。分别是批量insert/update前置、依赖add/remove前置、
accounts/seed用户记录。已人工核对这些组。扫描不识别变量改名或语义等价，也不把
同键记录认作相同策略，因此不能以“只有2组”证明没有更大的重构空间。

工具 `tmp/802_review_size_round9/802_structure.py` 只git show既定应用源，不导入产品、
不读测试/私件、不连数据库。首轮工具SIM102静态失败保留，调整同一布尔条件并格式化
后Ruff通过；最终再扫输出与原输出cmp逐字相等（2组/1形状）。函数表中的lines是
AST物理跨度，包含空行/注释，**不是cloc有效行**；主数使用原classifier和已核hash的cloc。

## 2. 现有库是否能直接接管最大基础设施

| 当前文件/有效行 | 已用的库与必须保留的产品策略 | 本轮判定 |
| --- | --- | --- |
| seed326 | 已有context、表字段投影add、annotations、FK顺序批插入 | recipe不是未实施的整块预算 |
| migrations303 | 已用SQLAlchemy Inspector；另做字段/索引/FK/CHECK精确差异、锁、显式库和部分DDL保护 | Alembic不等价接管全部审计 |
| rows293 | 已用SQLAlchemy Core生成SQL/绑定值；保留表/字段/表达式allowlist、失败标记、savepoint及专用历史读取 | 没有第二套手写ORM可删 |
| runtime284 | 预检、幂等claim、主事务锁定、成功审计/outbox、独立拒绝审计、uncertain提交分类 | 重复调用不代表重复协议 |
| api244 + contracts56 | 已用FastAPI与Draft202012Validator；参数/严格JSON/错误优先/响应保护为适配策略 | 不存在几百行自写JSONSchema解释器 |
| schema117 | 从冻结DDL生成SQLAlchemy元数据，并提供SQLite测试变体 | 官方反射需要实际DB，不是离线DDL解析器 |
| engine93 | create_engine/URL/pool/events均直接用SQLAlchemy，额外约束是配置与MySQL会话保护 | 外包配置不能删除保护 |

官方SQLAlchemy文档说明Table反射通过engine读取实际数据库，且反射结果不保证重建
完全相同DDL；它不能直接替换当前导入时无需连接的冻结DDL→元数据路径。
[SQLAlchemy反射文档](https://docs.sqlalchemy.org/en/20/core/reflection.html#limitations-of-reflection)

Alembic当前官方文档明确：CHECK按名字检测是可选功能，同名表达式变化不检测。
因此直接以compare_metadata替换check_schema，会漏掉本项目要求拒绝的同名不同条件，
必须把相应checker留下；不能先扣掉303再忽略adapter/版本和锁状态成本。
[Alembic自动生成限制](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#detecting-check-constraints)

SQLGlot也不作为新提案重复报收益：DB owner本日已做精确30.24.0隔离候选，425组
对照无差异但净9、590次解析约13.4倍耗时，获root同意撤回。本岗只核公开记录，
未复跑该原型；见agents/database/size-optimize-20261025/github-issue4-comment.md。

## 3. Runtime/CRUD/域规则的系统性方案及实际重复

当前Runtime的authenticate在预检、认领/主事务和锁作用域重复出现，是防止校验期间
撤销会话、成员变化或旧owner租约更替的TOCTOU边界。scanner确实调用authorize；
988真实竞争开发用例调用claim和locked_scope，不能把这些当未用包装直接删。
成功审计/幂等COMPLETE与拒绝审计也分属不同事务，统一一个无条件装饰器会错放commit。

Projects/Tasks/Reviews共同的create、CAS、分页、wire与model早已在Call/common里。
依赖add/remove只剩3句完全相同前置，后续一个查重/查环/创建、一个归属/删除；评审与
上线评估的表面“load→guard→create→CAS”也有不同角色、baseline、最新性与错误顺序。
domain V2的decide只负责纯规则，workflow仍保留DB锁/人力安排/DTO快照/写入和历史，
不能为了统一gate把同一条数据库访问放进纯域层。

**可拆的较大方案是有序操作计划，不是直接写一个通用CRUD引擎。**
由BE owner先在新内部版本定义 `OperationPlan`：输入为已授权Call和transaction-local
gateway；输出为result和审计diff；每条step明确原资源/权限/版本顺序及失败码，所有
savepoint、CAS、audit/outbox/COMPLETE仍由现有owner完成。试点应选依赖add/remove和
createReview/createAssessment两对，完整保留每个guard和负面断言、计入计划声明与解释器。
只有两对整体有效行确实减少、执行顺序trace逐项相等后，再决定是否扩至其他操作。

本轮不提供虚构的净节省数字：目前只有共同“骨架”，没有足够多相同策略。解释器可能
比两个原方法更长。若试点净增或只是把guard搬到不计数JSON，应淘汰；不能把四文件
总585行或Runtime284行当作可删除额度，也不能把计划声明算成免费配置。

## 4. RowsGateway与seed的较大方案

**Rows的候选是统一批量写的字段校验，不是裸Session替代。** insert_many/update_many
有完全相同的table获取、空批次返回和_fields投影，但insert要求同形非空、update还要求
id与变化字段一致以及_pk绑定。抽一个纯 `_batch_fields` 会增加签名/调用/新错误位置，
只能先核算含helper的净账；对外库SQLAlchemy已在负责SQL构造，无法再免除这些项目
保护。专用task_schedule_changes包含类型/上限/行集合/重复/项目边界检查，它与普通rows
不是重复实现；用宽泛select替换会重开此前历史证据串联风险。

**Seed的候选是两段式FixturePlan→materialize，并非重做V2。** 现V2已共享context和
add投影；剩326行承担计数/manifest/空库拒绝/三独立身份/历史分配/状态/时间/关联指针。
若DB owner继续研究，应只把状态到“需要的review/assessment/decision数量与指针”的
纯计划作为独立typed block，再由同一个add/materialize输出；完整纳入新类型、计划表、
分支和遍历成本。保持所有CLI参数/返回字段、40/6000/9000/15000、同输入可重现、
必要状态、reviewer独立性、FK插入顺序、版本/时间/证据/指针和旧manifest拒绝；样本
算法另版本化，不回写V1/V2黄金。需要现有14项DB性质、完整规模和REST联调重新证明。

本轮没有该完整新计划原型，故净账为未证明。仅把214物理跨度的_populate拆成多个
函数不会减少有效行；新typed块若重复当前dict声明反而会增加。后续负责岗先交完整
prototype、before/after计数与负面性质，再决定是否实施，避免再将“recipe”直接报80–120。

## 5. 为什么没有实施一个“大额补丁”

以上是可以交给owner验证或淘汰的内部架构试点，不是充分的775行路线。当前最明确的
消息13已经另交root；新方案没有源码净账，就不写成已证明能达标，也不把估算加成
几百行。更换数据库/Supabase、删审计/错误/会话/DDL保护、删消息/调度/示例数据，或
把生成代码迁出统计根都改变了既定技术/功能或口径，不属于本次默许优化。

正式规模门禁继续失败。若root继续上述较大试点，先规定停损：完整可读原型连新层
与测试一起审核，固定主数有实际正收益且所有原行为通过才进入生产；没有显著收益就
保留失败记录并停止该路线，不在活动云版本上边改边宣称通过。性能缓存可等真实profile
确认构造成本后单独做，它可能增行，不能挪作规模节省。

## 6. 产物与诚实边界

消息限定审核已封6f2d8b72并发布Issue12 comment6398648719逐字回读。AST与成本证据
在agents/reviewer/evidence/round9；本报告额外产出为架构核查与候选接口，不是产品修改。
本岗没有跑新的全CI、真MySQL/Rabbit、云或独立验收，没有读取任何未公开验收材料。
文档/提示词岗可记录这个真实“候选收益不足→保留原门禁→先预算试点”的过程，不能
写成学生亲自发现、人工改码或已节省775行的经历；研究报告正文仍由学生本人撰写。
