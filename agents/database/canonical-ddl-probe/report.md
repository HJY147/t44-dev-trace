# 796服务器规范DDL架构探针：否决raw-hash，未准入产品

数据库AI；基f4bd382d4668130793fc553df9ce6363c4656ea6。**真实MySQL8.4.11已反证“SHOW CREATE只忽略表级auto counter即为唯一语义标准”**：8个旧兼容正例中5个被误拒。B1保留既知语义normalizer的结构reference路线，最大可删84行尚未计新增源码，达不到100–250目标；B2另写完整native catalog归一化未实现/未证明，不宣传节省。生产/DDL/API/冻结/计数0修改，实际生产节省0，root提供的5862/超762仍是当前出口，不把本POC临时代码当已删应用。

## 可信I/O与执行资源

先设计9ff75091，原型fdb1b71b，FK夹具修正438fea60。root明确批准唯一既有官方binary路径及随包必需库/plugins：MySQLCommunity8.4.11 macos15-arm64，--no-defaults/--basedir固定，只socket/--skip-networking/--mysqlx=OFF/128M。新项目tmp796/data+s+pid与data2+s2+pid2，目录700、两新schema t44_796_reference/actual；570秒alarm+30清理预算，每次停前核own child PID+datadir命令/@@datadir/pidfile。两轮含初始化/清理7.559s、3.557s，own exit0/进程已消失、数据保留，无第3轮。数字只是探针生命周期，不是产品性能。

原13306/旧PID7980/oldschemas/旧config/datadir/log/env/凭据0操作；只执行root例外许可的binary及其依赖，没有扫旧.runtime。未读取独立799/800/805/809/814 PRIVATE/runtime内容，未联系测试实例。源码/probe/记录均自有worktree；唯一root目录写入是明确批准的tmp796新资源，均保留供协调处置。

reference是新空独立schema逐句执行**权威原bytes SHA c0e740...**后立即捕获18表SHOW，早于actual变异；不是从目标DB或迁移marker反推。native-reference.json仅DDL契约/来源数据，标POC_ONLY、未冻结运行使用；没有Python函数/业务实现塞入JSON，mutation SQL只是公开测试配方/观察，不是产品实现。reference摘要/工具SHA/版本/session context与原生输出均可审计。18表226列、59 CHECK/35FK（不是35CHECK）。

## 原正负兼容性：真实结果而非hash等价假设

原公开956的15个测试（含13参数化负例与7个表达式断言）本轮原字节运行15pass/0failure/error/skip，未改断言。988真实迁移/Utc/模式入口未运行，避免触及其旧fixture/13306；其目标库/版本/摘要/marker/GET_LOCK/部分失败语义代码98行保留，不计成可删parser。957未获明确公开读取许可，未读/未改。

首次native30配方中7个同名FK在单ALTER里DROP+ADD触发1826，属于**原型设置错误**，原run1/数据保留，不算负测通过。root批准新data2，只将这7项拆成两句，全部可执行；合并原生结果覆盖8兼容正例、13原负例、9新增意义漂移，共30个唯一case。所有case的执行DDL/SHOW/原checker返回和候选结果见native-run1/2.json与native-summary.json；不是只比名字。

|case|旧契约应pass（None为新增漂移）|现checker实际pass|raw候选pass|
|---|---|---|---|
| counter_growth | True | True | False |
| redundant_parentheses | True | True | False |
| utf8mb4_introducer | True | True | True |
| ascii_introducer | True | True | False |
| foreign_noaction_restrict | True | True | False |
| foreign_qualified_self | True | True | True |
| index_asc_btree | True | True | False |
| index_rebuild_same_definition | True | True | True |
| index_order | False | False | False |
| index_unique | False | False | False |
| index_desc | False | True | False |
| unique_to_nonunique | False | False | False |
| unique_column_order | False | False | False |
| foreign_target_table | False | False | False |
| foreign_target_schema | False | False | False |
| foreign_source_order | False | False | False |
| foreign_target_order | False | False | False |
| foreign_cascade | False | False | False |
| check_true | False | False | False |
| check_expanded_in | False | False | False |
| check_or_true | False | False | False |
| column_type | None | False | False |
| column_nullable | None | False | False |
| column_default | None | False | False |
| column_auto_increment | None | True | False |
| index_prefix | None | False | False |
| engine | None | True | False |
| table_collation | None | True | False |
| column_collation | None | True | False |
| check_enforcement | None | True | False |

5个raw误拒真阳性原因：

1. 只ALTER users AUTO_INCREMENT=1234：表级计数确已正确strip，但MySQL同时把ck_users_hash_shape字面量从_utf8mb4改为_ascii；旧checker接受、raw仍拒。不是本岗strip计数错误。
2. 用户active CHECK冗余括号：该表达式本身被server收敛，但同表另一CHECK也被重表达为_ascii，引发整表不同。
3. 直接等价ASCII引导符同样不是单一raw输出。
4. 显式ASC/BTREE：server保留USING BTREE并调整key展示顺序，旧结构接受而raw拒。
5. 默认NO ACTION与等价RESTRICT的展示确实不同；同库限定FK正例反而收敛相同。

[MySQL官方FK文档](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)已说明NO ACTION默认不显示而RESTRICT显示；原生结果与此一致。[SHOW CREATE文档](https://dev.mysql.com/doc/refman/8.4/en/show-create-table.html)还说明quote/session设置、NOT ENFORCED展示及row-format指定值/实际值的区别。故“经过服务器parser”不等于“所有语义等价DDL只有一个字符串”。不能靠更严格hash把原兼容正例改判不兼容。

normalize_show只有锚定的`) ENGINE=... AUTO_INCREMENT=<digits> DEFAULT CHARSET=`计数替换；离线断言证明列AUTO_INCREMENT、字面量中的AUTO_INCREMENT=42以及engine/charset变化都不被删。没有用去空白/删括号/删除引导符规避反例。

## 额外发现：当前checker本身也不是完整原生漂移护栏

当前checker真实接受index DESC、移除列auto_increment、改engine、表/列collation、CHECK NOT ENFORCED六项，而raw候选均拒。这是原生新发现，不是为raw路线放宽要求；不在本探针改产品或修改原测试。956假Inspector的DESC负例会拒，真实反射路径却接受。

只对**已捕获的own nativeSHOW离线回放**确认：锁定SQLAlchemy2.1.6 parser保存state列的DESC，公开get_indexes返回仅name/column_names/unique，未保留column_sorting；offline-dialect-desc.json记录输入/两层数据与本机函数hash。源码入口为[SQLAlchemy精确版本MySQL dialect](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_1_6/lib/sqlalchemy/dialects/mysql/base.py)。因此“把Inspector结果存JSON再比”还会继承反射信息损失，不能称补齐意义漂移。需要独立读取STATISTICS排序/类型/前缀/可见性、列auto/charset/collation、CHECK ENFORCED及table options等；不是无需新增逻辑。

[SQLAlchemy文档](https://docs.sqlalchemy.org/en/20/dialects/mysql.html#mysql-mariadb-unique-constraints-and-reflection)说明unique同时在get_indexes/get_unique_constraints出现；数据快照仍需一致性/重复表达检查。7个原表达式断言在原956保留，未被迁移成新的server表达式API，本轮不宣称替代已证明。

## 净账：不藏业务代码，也不先扣草案

固定cloc2.10/SHA/原口径：migrations303；_check_signature80、_index13、_foreign21、check_schema84、migrate98，残余imports/errorclass7；Core元数据builder依旧供生产Rows使用，不能因有reference顺便宣称已删。baseline-budget.json/net-budget.json保存实测。

|路线|净账与准入|
|---|---|
|A：raw SHOW标准文本|理论可替换198行检查函数，但5个有效兼容反例已否决；不能以潜在行数宣传收益，可信已省0|
|B1：结构reference，保留已知CHECK/FK/index归一化|已知必须保留114+98+7=219，即使新代码0行也最多省84。collector35–60、reference来源/hash loader15–25、差异输出10–18、版本/session身份8–12均未实现估算；模块投影287–334，即省16到增加31，尚未计生成器|
|B1全部维护源码|再加reference生成/封存/验证工具约40–80行（乐观估计，非实现），合计327–414，比303增加24–111。不是把生成器移出计量根就称免费|
|B2：直接用I_S重新设计normalizer，删除旧语法层|没有完成可保持全部兼容及反射补漏的实现/净账/证明；不作普遍“不可能”断言，但本轮无可信100–250净省方案，不能准入产品|

当前796探针本身413 cloc行（控制器/fixture/原始输出），是本轮新增研究维护源，不是产品删除。没有产品import这个脚本；测试SQL未转为生产业务逻辑，reference只数据；实际应用节省始终0。方案若只把相同normalizer藏成不计SQL/JSON函数或换拒绝条件，会违反本任务限制，已拒绝。

## 版本、目标选择与生成成本

- 当前migrate显式只接收8.4.*，README也写生产MySQL8.4；不能把此实验说成已验证8.0。[8.0官方说明](https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html)中8.0.16以前CHECK被解析但忽略；泛称8.0支持本来就不足以保证本契约。未运行8.0/其他8.4patch/Linux矩阵。
- 本次唯一原生身份8.4.11 macos15arm64/SQLAlchemy2.1.6，lower_case_table_names及sql_mode/charset/quote值在原件。一个pinned输出不能默默把当前8.4.*支持收窄成只允某patch，或把客户端charset/quote差异误判DDL漂移。其他8.4patch/OS需单独证明，不能新换错误拒绝。
- 生成reference需要可信全新schema、DDL source/hash与版本绑定、稳定会话上下文、变更时重新校准/评审、部署时校验artifact本身。当前运行账户没有理由被要求额外CREATE DATABASE；若采用，应在隔离build流程生成后作为数据发布，不能在被检查目标上“自认可”marker/catalog。生成器和绑定成本必须可读源码记录。
- 目标选择仍须URL期望库、SELECT DATABASE、server version、advisory lock/版本/摘要/partial-state拒绝；不得用“结构相同”替代正确数据库检查。FK只可把**真实当前库的自引用**视为self，不能全局替换schema名字隐藏跨库引用；本次跨另一个获批schema负例已真拒。

结论：否决A；B1净账不足，B2未证不推进；本轮不申请产品变更、不继续多轮试验，不因762缺口强推。原始错误/反例/未验证和新发现均保留；临时两instance已停、两datadir保留，原13306不动。后续若要补当前checker六项真实缺口，应另立功能完整性的owner任务，不能用“减量”顺便改原冻结/验收结论。

边界补充：两个原生负例为满足MySQL自身FK索引要求，在新actual schema加入probe_support/probe_target；原件显示复合变异涉及多个表/键，不将它们说成单字段隔离证明。原956的精确Inspector单字段反例未改且15项通过。上述结构化替代的全部兼容/版本证明仍未完成，不能借完整case清单宣称B2已通过。

本轮Issue4真实阶段评论已发表并精确GET全文逐字一致：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6399750242，正文与原响应归档。两轮owned日志在批准tmp796目录保留，E seal仅记其hash；没有读取旧runtime日志/凭据，原datadir/data2不删除。

用户随后明确本轮立即结束、停止服务器保留数据。收到后未再启动实验/实例/测试；最终只复核两自有PID均不存在、data/data2保留，见final-stop-confirmation.json。A反证/B1预算完成，B2实现/完整证明未做，按此状态封档，不继续推进产品。
