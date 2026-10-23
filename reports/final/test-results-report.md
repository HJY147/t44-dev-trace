# T44测试结果技术报告

当前应用固定bc5aef9c62393134582affb7a690acb33ac2b833。本报告区分模块/开发CI、真实HTTP专项审核、synthetic Docker、独立公开阶段和正式性能；结论仍是最终验收未通过。AI文档岗读取公开证据，没有重跑产品或访问独立私密用例/日志。

## 1 版本与同源开发CI

| 证据 | 准确对象 | 实际结果与含义 |
| --- | --- | --- |
| 产品push CI40023062800 | bc5aef9，产品后端bcb/前端c79 | static/contracts/coverage/frontend成功，只计该push一次 |
| Python全源 | 44个Git源文件，与覆盖率文件集合完全相同 | 510 tests，0 failure/error/skip；行2638/2957=89.21%，分支659/824=79.98%，排除0 |
| 前端全源 | 20个TS/Vue文件，集合准确一致 | 89/89，0 failed/pending；行364/390=93.33%，分支821/932=88.09% |
| 自动PR事件 | 同bc5的40023068752 | 与push不同事件，不重复累计用例或当新实验 |
| Docker40023062786 | 同bc5源 | 成功；4worker、2project/40task；不是40项目正式压力 |

来源[组合回执](../../records/validation/composite-bc5a-ci.json)、[原件索引](../../records/validation/bc5a-artifact-index.json)。全量source inclusion明确，不通过改变根目录/排除文件/压行满足覆盖率或规模。分支覆盖率按原分母报告，不和行覆盖率混淆。

## 2 各模块与跨模块测试

| 模块 | 已存在的开发测试入口 | 本轮可证实边界 |
| --- | --- | --- |
| 状态域 | tmp/backend/backend/domain/994_transitions.py | 纯状态/效果/非法条件；不是DB提交证明 |
| API/业务/幂等 | 986_http.py、985_mysql_http.py、987_faults.py | TestClient和真实MySQL HTTP、角色/结构/版本/事务；单个fault wrapper不是物理断网 |
| 持久/迁移 | 988_mysql.py、989_rows.py、993_foundation.py、956_schema_semantics.py | 真实SQL/UoW、DDL语义及bounded pairs；Rows66含48，两个MySQL目标重叠不累加 |
| 调度 | 973_extensible_rules.py、974_application.py、990_runtime.py、991_rules.py | 规则扩展、candidate/CAS、持久游标/续扫；不当正式负载 |
| 消息 | 976_process_mysql.py至980_delivery.py | 真MQ/进程、确认/重试/坏消息/fallback；不等于全收件人本人已读 |
| 前端 | 982_client.test.ts、983_application.test.ts、895_session_lifecycle_probe.test.ts | session、拒绝恢复、literal reason、缺失提示；当前全89而非各历史数字之和 |
| 部署 | 971_credentials.py、972_compose_application.py、997_ops.py；873_native_runtime.py阶段1 | 合成/结构守卫与Linux真实Docker分别；native完整周期仍待实际执行 |

入口名称在[M6追踪矩阵](../../docs/reports/M6-traceability.md)绑定准确Git源码，执行以原回执为准，文档岗只静态核对，未新增或运行用例。

## 3 会话与理由的真实红绿链

初次退出清理开发39绿后，895原探针1红2绿：A旧POST在B登录后返回403，旧卸载表单的父refresh清掉B上下文。7df先设计，9560修api错误路径及组件存活/session检查；原895不改三绿，开发全51绿，专项准确SHA限定关闭。当前89含后续容量/理由，不与51相加。

理由界面15红7绿的目标原失败后，c79目标22绿；完整89包含65继承+24理由组件案。新合成42项目通过真实872浏览器驱动，7次写入、1440/390两宽度六图；2000字符末尾和HTML字面显示与API hash一致。缺失/模糊/非计划/返工/迭代中的部分边界只是组件夹具，不能冒充都经过真实浏览器。详见[前端公开回执](../../agents/frontend/plan-reason-validation.json)。

后端0549最终18目标为11 SQLite HTTP（含1既有完整Plan回归）和7真实MySQL HTTP。中间12/16/18重复运行相互重叠；无效sort=-id夹具造成的失败已区分并修正，不能充产品bug。Canonical字形和无关重复字段的AI草稿失败保留。新写原事务/回滚、旧页本页精确投影有目标验证，不能保证所有存量历史都可重建。

原42243组合504绿仍漏历史证据true与数字1比较。专审唯一真实HTTP反例红，原[失败报告](../reviews/21-42243eb23aedf0edda7541ad83fd87ec3d17b616.md)和[COMMENT5634370911](https://github.com/HJY147/t44-dev-trace/pull/21#pullrequestreview-5634370911)永久保留。ad6设计先行、bcb窄修后，6新参数案+1既有HTTP回归七绿；同一原HTTP反例在bc5一次绿，[限定复审](../reviews/21-bc5aef9c62393134582affb7a690acb33ac2b833.md)及[COMMENT5634448127](https://github.com/HJY147/t44-dev-trace/pull/21#pullrequestreview-5634448127)仅关闭HISTORY-EVIDENCE-01，不改旧报告/断言，不宣称完整审核放行。

![真实质量反馈](../../docs/reports/diagrams/m6-quality-feedback.png)

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

## 5 独立v3当前只知的公开状态

[v3冻结收据](../../records/acceptance/v3-case-freeze-receipt.json)证明先冻结后接SUT；[runtime binding](../../records/acceptance/v3-runtime-binding.json)绑定bc5。它们本身不是执行结果。root随后明确发布590673c的stage01环境MD/JSON：H run40024056400环境ready且最终恢复true，控制stdout与driver对JSON的假定造成前置阻塞，26功能整例均NOTRUN，产品通过0/失败0。0产品失败绝非验收通过。

后续H2纯mechanical IO/浏览器传输且源码/断言不变是tester公开声明；文档岗与root未读取私密载荷独立核验。正式性能由原冻结独立入口准备代表数据与测量，当前无新发表结论。新结果只有经明确发布后才增补，不能依环境ready或CI绿预填。

## 6 Docker与原生演示

同bc5 Docker实际4worker、2项目40任务、19表停写备份/新隔离库恢复行数与checksum完全一致，18业务表226字段复核，scanner completed2。共享flock第二扫描器exit1是预期负向检查，不作run失败；Docker是synthetic Linux集成，不是native桌面完整周期、异机灾备或正式性能。

native阶段1公开30d66/实际7e94258：run2认证、回环和正常停机通过，EPMD为127.0.0.1及::1，root接受该技术澄清；run1 false但cleanup true和cookie前置失败保留。曾有短nocookie窗口及后续防泄露守卫，仅按公开局限解释。阶段2已有3e05设计、bc5源绑定及控制器开发；13465cc检查点时尚无API/consumer/scanner/UI完整真实周期回执，后续owner勘误/守卫失败不能当应用失败或通过。

## 7 正式性能 规模和最终出口

原独立v1三批400VU/600秒P95为3035、1908、5506ms，均高于270ms；吞吐/稳态零失败的通过与P95失败分开。没有新正式通过；短ABBA、开发诊断、空库能力或2项目Docker不替代代表数据正式测量。

固定[cloc原件](../../records/metrics/source-count-strict-evidence-combination.json)和bc5组合回执记录有效源6307，目标3500至5100，超1207。history有效代码92→96净+4，物理净+6不是有效代码，不能改统计根或压行称达标。

整体出口还需新独立完整矩阵、性能、规模、最终准确头审核及学生正文/真实人工材料。root历史JSON合并KeyError/误stage被diff gate阻止的[流程记录](../../records/validation/reviewer-history-merge-resolution.json)是AI协作失败，不是产品bug或学生识别幻觉。M4 Word QA也只证明当时技术稿排版，不证明软件通过。

## 8 MD检查点后的明确公开附录

原13465cc的应用/技术快照不回改；以下来源各自绑定公开提交，不改变bc5生产源。2e2bffa发布独立v3 stage02两文件：H2的functional、operational-faults和三formal入口共五段都在账号初始化控制stdout歧义前置阻塞，环境ready/最终恢复true；26功能整例、4故障整例、3正式组仍未完成，600秒稳态未启动，无产品PASS/FAIL或性能结论。24项离线wire驱动检查不算SUT用例；H3机械修正的源码/断言未变是测试岗声明，未由本岗读取私密载荷核验。

部署岗后明确发布5ef1bde（主证据e142470、实现0a6da88、SUTbc5）的native有限周期：唯一修正fresh run2 exit0/cycletrue/cleanuptrue；4 API workers、回环18088与UI5178proxy，两实际扫描周期60.303070秒完成、scoped会话轮换撤销与最终停机/受保护监听器旧基线核对。首轮run1 exit1/cleanupfalse保留；16事件26通知实际发生于首轮，二轮只复核既有ID与manager10通知，不能写二轮重新发布了这些消息。它证明该有限本地应用生命周期，不证明浏览器全业务、独立、正式性能、云或产品最终验收。

[独立stage02公开回执](https://github.com/HJY147/t44-dev-trace/blob/2e2bffa/reports/independent-v3/stage02-driver-binding.md)与[native阶段2公开入口](https://github.com/HJY147/t44-dev-trace/blob/5ef1bde/agents/deployment/native-application-validation/README.md)仅引明确公开材料，未跟随任何私密ref。
