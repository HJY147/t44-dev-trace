# T44测试结果技术报告

本M7增量的业务应用仍为bc5aef9c62393134582affb7a690acb33ac2b833；后续组合6ec8d3c93f4ff5283d3db62ae7993e66c4c54ca2的76个应用包文件经根逐字节核为等价。独立黑盒始终绑定原bc5，不移植为6ec重跑。本报告区分模块/开发CI、真实HTTP专项审核、synthetic Docker、独立公开阶段和正式性能；结论仍是最终验收未通过。AI文档岗读取公开证据，没有重跑产品或访问独立私密用例/日志。

## 1 版本与同源开发CI

| 证据 | 准确对象 | 实际结果与含义 |
| --- | --- | --- |
| 最新产品push CI40031843354 | 6ec8d3c，应用包字节等价bc5 | static/contracts/coverage/frontend成功，只计该push一次；不与旧510相加 |
| Python全源 | 44个Git源文件，与覆盖率文件集合完全相同 | 510 tests，0 failure/error/skip；行2638/2957=89.21%，分支659/824=79.98%，排除0 |
| 前端全源 | 20个TS/Vue文件，集合准确一致 | 89/89，0 failed/pending；行364/390=93.33%，分支821/932=88.09% |
| 自动PR事件 | 同6ec的40031848266 | 与push不同事件，不重复累计用例或当新实验 |
| Docker 40031843200 | 同6ec源 | 成功；4worker、2project/40task；不是40项目正式压力 |

来源[6ec组合回执](../../records/validation/composite-6ec8d3c-ci.json)；[旧bc5组合回执](../../records/validation/composite-bc5a-ci.json)作为历史保留。全量source inclusion明确，不通过改变根目录/排除文件/压行满足覆盖率或规模。分支覆盖率按原分母报告，不和行覆盖率混淆。

## 2 各模块与跨模块测试

| 模块 | 已存在的开发测试入口 | 本轮可证实边界 |
| --- | --- | --- |
| 状态域 | tmp/backend/backend/domain/994_transitions.py | 纯状态/效果/非法条件；不是DB提交证明 |
| API/业务/幂等 | 986_http.py、985_mysql_http.py、987_faults.py | TestClient和真实MySQL HTTP、角色/结构/版本/事务；单个fault wrapper不是物理断网 |
| 持久/迁移 | 988_mysql.py、989_rows.py、993_foundation.py、956_schema_semantics.py | 真实SQL/UoW、DDL语义及bounded pairs；Rows66含48，两个MySQL目标重叠不累加 |
| 调度 | 973_extensible_rules.py、974_application.py、990_runtime.py、991_rules.py | 规则扩展、candidate/CAS、持久游标/续扫；不当正式负载 |
| 消息 | 976_process_mysql.py至980_delivery.py | 真MQ/进程、确认/重试/坏消息/fallback；不等于全收件人本人已读 |
| 前端 | 982_client.test.ts、983_application.test.ts、895_session_lifecycle_probe.test.ts | session、拒绝恢复、literal reason、缺失提示；当前全89而非各历史数字之和 |
| 部署 | 971_credentials.py、972_compose_application.py、997_ops.py；873_native_runtime.py阶段1 | 合成/结构守卫与Linux真实Docker分别；旧0a6有限周期成功及新capture窄修见第6节，不混版本 |

入口名称在[M6追踪矩阵](../../docs/reports/M6-traceability.md)绑定准确Git源码，执行以原回执为准，文档岗只静态核对，未新增或运行用例。

## 3 会话与理由的真实红绿链

初次退出清理开发39绿后，895原探针1红2绿：A旧POST在B登录后返回403，旧卸载表单的父refresh清掉B上下文。7df先设计，9560修api错误路径及组件存活/session检查；原895不改三绿，开发全51绿，专项准确SHA限定关闭。当前89含后续容量/理由，不与51相加。

理由界面15红7绿的目标原失败后，c79目标22绿；完整89包含65继承+24理由组件案。新合成42项目通过真实872浏览器驱动，7次写入、1440/390两宽度六图；2000字符末尾和HTML字面显示与API hash一致。缺失/模糊/非计划/返工/迭代中的部分边界只是组件夹具，不能冒充都经过真实浏览器。详见[前端公开回执](../../agents/frontend/plan-reason-validation.json)。

后端0549最终18目标为11 SQLite HTTP（含1既有完整Plan回归）和7真实MySQL HTTP。中间12/16/18重复运行相互重叠；无效sort=-id夹具造成的失败已区分并修正，不能充产品bug。Canonical字形和无关重复字段的AI草稿失败保留。新写原事务/回滚、旧页本页精确投影有目标验证，不能保证所有存量历史都可重建。

原42243组合504绿仍漏历史证据true与数字1比较。专审唯一真实HTTP反例红，原[失败报告](../reviews/21-42243eb23aedf0edda7541ad83fd87ec3d17b616.md)和[COMMENT5634370911](https://github.com/HJY147/t44-dev-trace/pull/21#pullrequestreview-5634370911)永久保留。ad6设计先行、bcb窄修后，6新参数案+1既有HTTP回归七绿；同一原HTTP反例在bc5一次绿，[限定复审](../reviews/21-bc5aef9c62393134582affb7a690acb33ac2b833.md)及[COMMENT5634448127](https://github.com/HJY147/t44-dev-trace/pull/21#pullrequestreview-5634448127)仅关闭HISTORY-EVIDENCE-01，不改旧报告/断言，不宣称完整审核放行。

此图保留M6的HTTP审核反馈历史；图内当时“独立v3待发表”是原cutoff状态，当前独立进展见第5和第7节，未重画旧图。

![M6历史质量反馈](../../docs/reports/diagrams/m6-quality-feedback.png)

## 4 独立v2明确公开的八阶段

全部固定4c20f32b71635016815420472b9d4bb4fa850df0；八阶段16文件逐项来源见[M6清单](../../docs/reports/M6-source-manifest.json)。每份结论均NOT_ACCEPTED_INCOMPLETE；不将不同阶段HTTP、子项或重叠观察相加成为完整用例总量。

| 已发布阶段 | 实际观察 | 未完成或失败 |
| --- | --- | --- |
| API | 38操作均有成功响应，1596 HTTP，14执行函数已有断言通过 | 含setup/只读函数；551条件及AC整体未验完 |
| 受限故障 | 4子集通过、1原消息捕获BLOCKED、setup通过；513 HTTP | 不是全部SCANS/MQ/TX，选择性故障和中批未证明 |
| 待完成API补充 | 788 HTTP/355只读SQL，6子项通过 | 1原冻结断言失败、1自前置阻塞；范围歧义非新确认bug |
| 收件人 | 286 HTTP/28只读SQL，2子集通过 | MQ原捕获/重复/fallback竞态仍不完整 |
| 首批UI | 1失败、1阻塞、8未跑或部分，无整例通过 | V2-UI-001/P2退出后DOM留旧项目名 |
| 容量依赖UI | 859事件、274响应，8拒绝对应真实审计 | V2-UI-002通用拒绝文案、003旧理由未显示；无整例通过 |
| 时间输入 | 19功能子项及1setup通过 | 不是19个完整原场景，其他冻结范围保留 |
| 安全呈现/键盘 | 局部呈现与键盘事件，新增确认缺陷0 | UI09/10仍PARTIAL；7原driver错误保留，非全站无障碍或安全结案 |

UI001/002/003对应开发修复和窄审在新版中有证据，但不篡改原4c结论，也不称独立新版复测已通过。本岗没有跟报告中的私密ref、入口或原截图读取。

## 5 独立v3公开黑盒封存

本轮只读取明确发表的[stage04功能与浏览器](../independent-v3/stage04-functional-browser.md)、[stage05运行故障](../independent-v3/stage05-operational.md)、[stage06正式性能](../independent-v3/stage06-formal-blackbox.md)及同名JSON；不跟私密引用、案例、驱动、原始输出或密钥。原冻结b6fd0a830319df10076a6fd8a7342153c0eb6661先于接触SUT，精确应用为bc5。阶段01/02的环境stdout解析阻塞、26功能NOTRUN及600秒未开始是早期真实状态，保留在M6历史稿；不能继续当作当前无产品执行。

| 范围 | 当前明确发表的整例结果 | 仍有的限制 |
| --- | --- | --- |
| 功能 | 26原整例中25个不同整例通过，已过不重跑；F08原断言不符保留 | F08错误优先级规范未决，确认产品缺陷0不等于26全过 |
| 真实浏览器 | 6/6整例、15原业务判据通过 | 只原六流程，无人工验收、完整读屏或视觉对比度符合性结论 |
| 可执行粗故障 | 4/4整例通过，前三例40030191650，最后O04由40031510946续跑 | 恢复true仅该次恢复，不替代精确切点证明 |
| 正式性能 | 原三整例完整执行、0通过/3未达 | 第7节列P95、失败与采样门槛，不用吞吐抵消 |
| 额外功能观察能力 | 3项预声明规范/安全能力阻塞 | 重叠空证据错误子类、hash-only持久边界、全局会话撤销观察未证 |
| 精确故障切点 | 5项能力阻塞 | 提交前、提交确认丢失、发布确认ACK丢失、消费提交后ACK前、幂等拥有者租期恢复 |

F08同时遇到旧上线评估基线过期与改期后旧批准失效：原期待ASSESSMENT_BASELINE_MISMATCH，实际RELEASE_APPROVAL_REQUIRED。冻结资料未定两者优先级，原失败断言和未到达的后续语句都保留；不擅自改期待或补业务优先级凑绿。动态10701重复通过子断言不是整例或分支数。38操作触及、130/551同操作/状态/错误码组合被观察，余421未观察；同组合不证明背后每个条件覆盖。

六浏览器范围包括登录退出/历史返回、项目和外人边界、阻塞/解除、容量移除拒绝、审计历史/最新版本、全新会话键盘。阻塞/解除各真实200流转，容量拒绝实际422且完整计划未变，页面显示核到北京时间分钟精度。这是独立AI自动化，不是学生亲验。四粗故障涵盖提交后API重启、MQ故障降级恢复/迟到重复、MQ重复消费、20个超期任务与调度重启重扫不重复升级；没有用停整库替代五个精确切点。

stage06封存时原4白盒/4交付物范围尚未执行；root之后通知这部分已开始执行，但未开放发表结果。本稿不读取未发布原件、不计为8项已测通过，也不称黑盒全系统验收。

## 6 开发集成 原生演示和本机预览

6ec同源Docker实际4worker、2项目40任务、19表隔离恢复行数与checksum相同，scanner completed2；共享flock第二扫描器exit1是预期拒绝。它是开发者小规模Linux集成，不能代替独立正式数据或native完整验收。

[native有限周期](../../agents/deployment/native-application-validation/README.md)归档5ef1bde、实现0a6da88、应用bc5。唯一修正fresh run2 driver0/cycletrue/cleanuptrue：四API worker、回环18088与UI5178代理、两次60.303070秒扫描周期、scoped会话轮换撤销、最终全停。run1 exit1/cleanupfalse保留；16事件26通知发生于首轮，二轮只复核已有ID/manager10通知，不声称二轮新发布。阶段1的回环含127.0.0.1及::1、cookie前置失败和短nocookie窗口局限保持。

随后专审c688发现NATIVE-CAPTURE-TIMEOUT-01：首次communicate超时后，mock清理子命令最终rc0被旧capture错计成功。原反例是无真实进程/信号的合成红，不是原run2曾超时。7f4845e先设计、b238978窄修、cc6a211封档，永久保留timed_out与实际rc；五合成边界rc为0/7/0/-15/null，超时后rc0仍失败，未确认清理也失败。cd3e4c2的[限定复审](../reviews/34-cc6a211bb1692460ffba09f7ee764c64545602ee.md)及[COMMENT5634940377](https://github.com/HJY147/t44-dev-trace/pull/34#pullrequestreview-5634940377)只关闭该P2。原inline未存独立脚本，本次仅同事件/原断言的语义重建一次绿，不称命令或输出字节相同；新b238没有完整cycle，旧5ef不通过及0a6周期历史不变。

[最新本机预览](../../docs/ui/latest-preview-update.md)公开封档2e58381绑定bc5只读85文件archive，源hash前后一致。原API/Web身份核对后退役，127.0.0.1:5173代理18080启新API四worker/Vite；仅API+Web，无MQ/scanner、DDL/迁移/seed/reset。907一次1440/390 smoke记录20请求（2登录/18GET）、0业务写、0错误响应事件/页面错误，四图由前端AI实看。驱动不逐条记成功状态，不能称20×200，也不是容量/reason重新独立验收或持续部署；私密账号说明未读。

## 7 正式性能 规模和最终出口

**v3三组正式整例均未通过冻结判据。** 每组独立空环境，经原公开HTTP准备并只读核40项目、6000任务、9000依赖、15000评审/决策合计，15秒预热后完整600秒稳态，无超时；400活动VU采样min/max都400。先冻H8为21dee8c842e593a0fd5e3e7b589a16d75497c1e6，环境实现cf685d7。数值来自[stage06公开JSON](../independent-v3/stage06-formal-blackbox.json)，原始帧SHA/CSV/分位数/吞吐/失败由独立岗重算，本岗没有读取原始私密载荷。

| 组及运行 | 目标P95毫秒 | 目标成功吞吐每分钟 | 组内失败 | 稳态采样数 | 整例 |
| --- | ---: | ---: | ---: | ---: | --- |
| 任务流转40030195416 | 9512.069 | 5301.6 | 1021 | 5824 | 未达 |
| 契约校验40030199950 | 3086.148 | 11149.8 | 0 | 5909 | 未达 |
| 升级接口40030202604 | 8272.364 | 2291.3 | 2 | 5786 | 未达 |

P95门槛270ms三组都失败；吞吐门槛1000/分钟三组都达到。采样门槛至少5900，流转/升级不足，契约达到；活动VU400与实际in-flight不同，三组in-flight范围分别399至400、391至400、391至400。失败为组内全部操作：流转1021次结构化503；升级1次配套改期503与1次202不满足有效新增事件判据；契约0。CSV未留具体错误码/正文，根因未知，不推定DB、代理、worker或发压端瓶颈。实测未达只描述本次提供环境，不泛化所有环境的逻辑结论。

P95采用稳态起始目标请求的全部尝试（含失败），nearest-rank ceil(0.95×N)；吞吐仅成功且在截止内完成的目标响应，迟到不计，预热排除。升级202是可靠受理，不是消息端到端送达延时。每环境6个合成human账号、400独立任务上下文按角色共用凭据，不是400真人。初始15000为合成评审、决策0，任务主要待受理/待评审且项目同形，满足冻结尺寸不覆盖所有生产业务分布。

三组同次只测到原引擎4逻辑CPU、平台、load、进程内存限制/RSS等；同次容器CPU/内存限额、实际worker数、MySQL/Nginx连接配置、物理共置和其他流量均unknown。O04后续快照不回填：该次api-processes观察exit1、null且observation_complete=false，4CPU/可见内存/MySQL151/Nginx1024也只属于O04，不是三正式运行设置。0/null/max不解释成无限物理资源，Unix socket不证明物理同机。环境ready/最终恢复true不抵消性能失败。

原v1三组400VU/600秒P95 3035/1908/5506ms也保留失败，不与本轮合成重复次数或改当已优化。短ABBA、开发诊断、空库能力和2项目Docker不能代替正式测量。固定[cloc原件](../../records/metrics/source-count-strict-evidence-combination.json)与6ec回执仍6307有效代码，目标3500至5100，超1207；不得改计数根/排除/压行冒达标。

整体仍需F08业务规则裁定、未验能力/错误条件、后续明确发表白盒与交付物、正式性能及规模处理和最终准确头审核。学生研究正文本人写，真实人工12修改/3幻觉识别/5上下文映射无完成证据。文档岗只整理公开事实，M6/M7排版QA不证明软件或学生作业全部通过；[M7来源和范围](../../docs/reports/M7-source-manifest.json)绑定本版证据，M6测试原稿可从126df历史恢复。
