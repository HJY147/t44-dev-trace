# T44 软件开发大作业

本项目选题为“中小软件外包团队研发流程留痕与上线评估管理系统”，应用名“留痕”。[公开仓库](https://github.com/HJY147/t44-dev-trace)采用MIT许可证。已实现Vue业务界面、38项冻结API、MySQL事务与审计、RabbitMQ通知、独立APScheduler扫描和Compose部署工具，仍在审核、独立验收与规模优化阶段。完整集成见[draft PR #21](https://github.com/HJY147/t44-dev-trace/pull/21)；受保护main尚未发布该完整产品。

## 2026年10月29日工程检查点

最新协调分支为 `codex/resume-coordination-20261029`。完整事实、需求追溯与未达项见[工程检查点](reports/final/engineering-checkpoint-r29-20261029.md)及[本轮实测与保盘停机](reports/final/performance-r29-20261029.md)。下方10月24日及其他早期段落均保留为历史，不代表当前运行状态、代码规模或购买授权。

| 范围 | 已取得的证据 | 尚未通过的出口 |
| --- | --- | --- |
| 开发回归 | 准确源码0bffe0c5的[原生CI](https://github.com/HJY147/t44-dev-trace/actions/runs/40827655008)后端796、前端89全过，类型与构建成功；行覆盖2502/2773 | 不是独立功能或性能验收 |
| 代码规模 | 准确组合源0bffe0c5、65个应用文件、5880有效行；固定计数器和cloc未改 | 超5100上限780行，规模仍失败 |
| 云上开发短测 | 旧f7源码400并发8000请求全部完成，0失败/中止客户 | 三个正式目标P95仍343–636ms，超过270ms；约5.26秒不是600秒稳态 |
| 独立云轮次 | 唯一900秒窗口原始记录完整保留 | `NP_NO_RUNTIME_RESULT`，76字节证据头，无runtime结果，不能推断请求量或业务成败 |
| 云资源 | 两台原实例保留；04:59Z前分别核为节省停机、自动释放均“-”，原数据和卷保留 | 云盘仍计费，最终结算未核；本地准备可靠前不重启 |
| 过程材料 | [真实prompt及证据索引](docs/prompting/R29-process-evidence.md)、[本人自写素材入口](docs/reports/r29-student-fact-index.md) | 学生本人研究正文与真实人工材料仍须本人完成 |

后发两个局部重构经限定审核后合入0bffe0c5，实际净减7行；该准确源的新CI40827655008四job已实际通过，原ZIP及95件产物核验封存，旧7b15通过记录另留历史。独立测试工具模拟HTTPS复测单列，模拟结果不充作项目性能。截止按用户确定的11月28日安排；当前不新购云机器，也不以历史“尚无购买授权”的段落覆盖后续实际授权与操作。

## 10月24日及此前的历史记录

截至2026年10月24日08:03（北京时间），[独立黑盒封存](reports/independent-v3/stage06-formal-blackbox.md)为功能25/26通过（1项错误优先级未决）、界面6/6、可执行故障4/4通过；三类正式压力均未达标。性能、6307行超限及学生本人研究材料仍待完成，后续[限定白盒](reports/independent-v3/stage07-whitebox.md)与[交付物核查](reports/independent-v3/stage08-deliverables.md)已完成范围审阅，仍有部分证据和未达项，整体NOT_ACCEPTED_INCOMPLETE。

完整本机四小时演示已按原截止自然结束，`http://127.0.0.1:5178`已停止；[实际结束报告](agents/deployment/demo-natural-close-report.md)确认driver/post退出0、清理成功。该运行仍固定bc5，不是后续开发候选或正式性能验证。另保留 `http://127.0.0.1:5173` 的API/网页大数据预览，末次监听元数据核对见同报告。[醒来后查看项目](docs/user-guide/wake-up-review.md)区分入口及本机私密登录说明，账号未公开。

## 用户返回后的进展（2026年10月24日）

已按用户答复以11月28日为截止；用户打算自行购买阿里云，先参阅[性能指标与两台机器选购清单](docs/user-guide/aliyun-performance-machine-checklist.md)，尚无云资源购买或AI支出授权。新D008修复提交C=`0dfb55c2191200d947c5423fd9ee74bb0812cc5a`实际计数6310行（原6307+3）、超上限1210；[原规模审计](agents/database/source-budget-return/report.md)保留6307时点结论，尚无可信的千行等价删重方案。三组旧正式性能失败及H2有效并发未证实的结论保持。

858工具准备失败保留；857另行冻结、单次准入后的[短时自有stub校准通过](reports/acceptance/v5-calibration-857-public-summary.md)，10000请求无失败/P95约208.9ms含固定200ms等待，未测SUT或正式600秒。D008发布提示顺序已由用户选择，RFC/规格分别审查后在d530755建立[1.2新冻结](records/spec-freezes/v1.2.json)，之后才实现：同856用例旧3红8绿→新11绿，另4旧相邻目标通过。[准确C代码审核](reports/reviews/43-0dfb55c2191200d947c5423fd9ee74bb0812cc5a.md)未见新增实质代码阻断；[产品CI40060857352](https://github.com/HJY147/t44-dev-trace/actions/runs/40060857352)及[容器40060980119](https://github.com/HJY147/t44-dev-trace/actions/runs/40060980119)通过，后端522/前端89，代码已准入开发集成，main未放行。CI实际输入与限制以[协调准入收据](records/decisions/D008-development-admission.json)为准，不将旧F08追改通过。新独立854设计77个概念用例/0执行，尚须工具与环境冻结；855输入暴露及[提示词修订](records/prompts/ROLE-independent-release-INPUT-ISOLATION-ITERATION.md)保留。各旧稿和Word/ZIP保留准确截止，学生最终研究正文仍须本人完成。以下09:20是历史收尾快照。

## 2026年10月24日09:20收尾状态（北京时间）

最新C=`b66fa36a317145afec350d7f61ca374959b2eaf7`仅将Workflow依赖读取增加可信`project_id`谓词；合法冻结库中的等价范围已由[18b0271有限审核/准确PR42 COMMENT](https://github.com/HJY147/t44-dev-trace/pull/42#pullrequestreview-5636066453)核对。[完整CI40047832510](https://github.com/HJY147/t44-dev-trace/actions/runs/40047832510)与[Docker40047836840](https://github.com/HJY147/t44-dev-trace/actions/runs/40047836840)均绿（510BE/89FE）。root已按事前dde39 gate决定准入开发集成，最终以`records/decisions/dependency-query-development-admission.json`收据为准；没有合入连接池db87，也没有放行main。限定等价及开发CI不证明性能收益或完整验收。

5178有界演示固定bc5；四份Word保留各自M6/M7截止，不能称为C同源验证；演示截止北京时间11:49:43，不重启、不延长。固定口径6307行仍超5100，完整验收尚未通过。后发H2六次exit1，最终恢复5次true/1次false，有效400并发未证实，SUT性能INCONCLUSIVE、不排名，原v3失败保留。Pcal=`b69ac5e`的[公开stub校准摘要](reports/acceptance/v4-driver-calibration-public-summary.md)/[JSON](records/acceptance/v4-driver-calibration-public-summary.json)显示400用户即时响应仍有客户端延迟/超时；这不能归因原CI或SUT，不能修复H2测量有效性，没有补跑。阅读[M10](reports/final/M10-night-test-handoff.md)、[M11](docs/prompting/M11-quality-and-test-limits.md)及[M12末次技术附注](reports/final/M12-final-source-and-measurement-note.md)了解边界；固定Word不因此改版。

本次审阅包已实际生成：本机`.submission-private/coursework-review-bundles/T44-coursework-review-M7-4833be05807d.zip`，绑定源码`4833be05807df5a9d43176eb2ec5a610c7ac06b1`，共18个外层成员、四份固定Word及3745个内层源码文件。准确SHA和缺项以`records/validation/coursework-review-final.json`为准，实际重新打开/CRC/成员与Git核验见`records/validation/coursework-review-final-postcheck.json`。它是本机私密审阅包，未上传GitHub，不是最终提交或整体验收通过。

## 获取本轮审阅源码

完整源码在`codex/integration`。重新获取时使用`git clone --single-branch --branch codex/integration https://github.com/HJY147/t44-dev-trace.git`；固定审阅包另绑定完整commit，不把浮动分支当成已验收版本。先体验可按[五分钟导览](docs/guidance/M8-five-minute-tour.md)。

## 功能与运行

支持项目成员与角色、迭代产能和排期、任务依赖、七状态流转、八段十项评审、四视角上线风险和回滚预案、经理交付/回滚/返工决定、三级延期提醒、通知已读/处理和审计追踪。发布和回滚记录人的决定，不替人操作外部生产系统。

技术栈：Vue 3 / TypeScript / Element Plus，FastAPI / Python 3.12，MySQL 8.4，RabbitMQ，APScheduler，Docker Compose。单体分层，API、消息和扫描分别运行；不将多agent开发岗位当作业务微服务。

请按[单机运行与恢复说明](deployment/README.md)配置、构建、显式迁移、初始化账号和签发调度身份。凭据随机生成并私密保存，不提供可直接公开登录的默认密码。部署说明包含停写备份、新隔离目标恢复和SSH隧道访问步骤。

## 界面与设计过程

界面采用用户指定的米色、浅咖啡色、多圆角与玻璃层次。[OpenDesign来源与视觉规范](docs/ui/warm-glass/DESIGN.md)、[可点击原型](docs/ui/warm-glass/prototype.html)先形成设计提交326f971，再以840b1a8导入Vue；使用的是官方本地agent技能/模板工作流。可查看[实际桌面](agents/frontend/latest-preview-smoke/1440-workspace.png)与[手机](agents/frontend/latest-preview-smoke/390-workspace.png)截图，合成数据明确标记。

浏览器检查发现的既存空文本强转true另以7369400设计、75c3468修复及6212e5f证据留痕；[视觉审核](reports/reviews/warm-glass-840b1a88e6976f0ecfb0b0ba45676b208aae4d98.md)与[初值补充审核](reports/reviews/empty-value-75c3468de07303cc47b9afd0e4a169664743470e.md)分开记录。开发验证、审核和独立验收保持不同范围。

## 可核对的阶段证据

以下按各自准确提交保留历史证据，行内状态只适用于该次检查；最新状态见顶部收尾说明，旧结果不覆盖新版本。

| 范围 | 实际证据 | 边界 |
| --- | --- | --- |
| 候选默认配置CI（未合入） | `db87d30`的[product40039282322](https://github.com/HJY147/t44-dev-trace/actions/runs/40039282322)通过520BE/89FE；[Docker40039333270](https://github.com/HJY147/t44-dev-trace/actions/runs/40039333270)实际checkout为PR merge400a5，166相关文件与候选相等；[五ZIP与51原件](records/validation/composite-db87-pool-ci.json)已核 | 默认保留15/overflow0的两常量候选；[有限专审](reports/reviews/39-db87d30449356f3473b645a5c246dcc6c21d7cbe.md)无新增实质阻断，资源/partial override变化保留；H2已完成但有效400并发未建立，不给候选排名，未准入当前应用 |
| 前一已核集成工具CI | `4718482`的[product40034577627](https://github.com/HJY147/t44-dev-trace/actions/runs/40034577627)与[Docker40034577586](https://github.com/HJY147/t44-dev-trace/actions/runs/40034577586)成功；510BE/89FE，全44Python/20TSVue；[五ZIP摘要与51份原件](records/validation/composite-4718482-ci.json)逐一核验 | 该时点应用为bc5；此CI不覆盖后发连接池诊断、审阅包构建器及bounded serve工具，不将结果移植到后发代码 |
| 独立v3正式黑盒 | [stage06](reports/independent-v3/stage06-formal-blackbox.md)：3组各完整400VU/600秒；P95流转9512.069、契约3086.148、升级8272.364ms，均超270；组内失败1021/0/2 | 三组吞吐均达标，但整体原判据均未通过；两组采样密度也未达。资源同次缺失保留unknown、503根因未定，后续4白盒/4交付物范围另行核查 |
| 前一准确应用组合CI | `bc5aef9`的[run40023062800](https://github.com/HJY147/t44-dev-trace/actions/runs/40023062800)四job成功：后端510项、全部44文件行2638/2957=89.21%、分支659/824=79.98%；前端89项、全部20文件行364/390=93.33%、分支821/932=88.09%；[完整原件及源对应](records/validation/composite-bc5a-ci.json) | 新后端严格历史证据匹配bcb0、前端字面理由c79；新文件均纳入分母、无排除。是开发CI，独立v3另行执行、正式性能和规模仍待达标 |
| 前一准确应用容器演练 | 同一`bc5aef9`的[run40023062786](https://github.com/HJY147/t44-dev-trace/actions/runs/40023062786)四API worker、真实扫描、19表恢复行数/checksum完全相同，18业务表226字段复核通过 | 合成2项目40任务；预期第二scanner flock拒绝exit1保留，不是租云、正式负载或独立验收 |
| 历史理由开发与审核反例 | [UI003实际证据](agents/frontend/plan-reason-validation.json)验证新42项目的旧理由投影/桌面手机各2000字原文；[42243原审核不通过](reports/reviews/21-42243eb23aedf0edda7541ad83fd87ec3d17b616.md)发现bool/数字证据误等，原HTTP红保留；先勘误后bcb0窄修 | 原42243 CI504绿未挡住语义缺陷。[bc5限定复审](reports/reviews/21-bc5aef9c62393134582affb7a690acb33ac2b833.md)原反例复查绿；不得把旧0549浏览器结果移植为新后端完整验收 |
| 本地完整服务有限周期 | [公开5ef归档](https://github.com/HJY147/t44-dev-trace/blob/5ef1bde/agents/deployment/native-application-validation/README.md)绑定控制器0a6/SUTbc5：run2实际cycle/cleanup成功、真实60秒扫描与凭据轮换，首轮16事件26通知；二轮仅复核既有ID | 全部自有服务已停。原run1失败保留；[原专项审核](reports/reviews/34-5ef1bde95e511c14dcff7b5fa0af2449de83836c.md)发现超时可误记成功P2；b238窄修和[cc6复审](reports/reviews/34-cc6a211bb1692460ffba09f7ee764c64545602ee.md)仅关闭该项，新代码未重跑完整cycle，不把原run2成功当全面放行或持续在线/云部署 |
| 前一组合CI | `8323692`的[run40016165656](https://github.com/HJY147/t44-dev-trace/actions/runs/40016165656)四job成功：后端437项、全43文件行2558/2878=88.88%、分支612/778=78.66%；前端65项、全19文件行353/379=93.13%、分支783/894=87.58%；[原件与适用版本](records/validation/composite-832-ci.json) | 后端A产品153b9c8、前端容量说明3628ee1，完整分母无排除；开发CI不等于独立复验、正式性能或规模达标。另一次自动PR触发的同head CI状态单列，不重复计测试 |
| 前一同源容器和恢复 | 同一`8323692`的[run40016165658](https://github.com/HJY147/t44-dev-trace/actions/runs/40016165658)真实Linux/Compose、4 API workers、19表恢复行数与checksum一致；18业务表226字段复核通过 | 2项目40任务的synthetic演练；不是已租云、正式性能或独立验收。共享flock第二扫描器预期exit1，原件保留；原6ba记录不覆盖 |
| 会话隔离修复与限定审核 | [原3c审核](reports/reviews/26-3c160c57c56af47eea2c524d93340a679eeb441b.md)实际1失败2通过，发现卸载旧表单错误回调会清空新会话项目；补设计后9560修复，[babc复审](reports/reviews/26-babc60f275ec780bcd3044be455acfddc4a49e60.md)原探针3通过；[新预览烟测](agents/coordinator/demo-session-fix-smoke/results.json)20请求无业务写 | 仅关闭SESSION-R1限定问题；未把旧CI39通过当全面保证，没有证明服务端越权，也不冒称新独立验收 |
| 容量错误解释修复 | [UI002开发证据](agents/frontend/business-feedback-validation.json)9业务目标红、4退路原绿→13通过；[c56限定审核](reports/reviews/30-c56a5a5485ccd80bbd6d34ed81a4fd073edb430e.md)自行复核13目标；自有合成项目桌面/手机4次真实422后数据未变 | 确认修改仅forms/OperationForm；实际E2E仅两种操作，其他解释是组件案例；原独立v2缺陷保留，等待新实例复验 |
| 写预检事务优化 | [7584限定审核](reports/reviews/29-7584cd31f0abfd6727d552b5fef31a9303247d58.md)和[原件核验](records/validation/backend-preflight-ci-coordinator.json)确认3次实际鉴权/原SQL/锁序保留、正常写事务3→2 | 先前遗漏scanner/旧claim调用方真实2红已修正，原25绿不覆盖它们；无新延迟收益结论，A有效+6而非最初估计-1 |
| 集成CI | `0448fecb`的[run39945098961](https://github.com/HJY147/t44-dev-trace/actions/runs/39945098961)，四job成功；335通过/0跳过；全部43个t44文件Python行2493/2818=88.47%、前端307/333=92.19% | Python分支77.73%另报；仅对该SHA；不是独立验收或性能结论。原265d89证据保留 |
| 独立缺陷的开发修复 | `479fc8fb`的[run39946771417](https://github.com/HJY147/t44-dev-trace/actions/runs/39946771417)，IAT01–05修复后的全量362通过/0跳过，Python全43文件行2524/2850=88.56% | 评估批准失效、创建任务人力、无效ID审计、任务排期差异、结构/证据错误分类；开发回归通过，尚非新独立实例复测 |
| 1.1人力规则与版本回归 | `4c20f32b`的[run39958165108](https://github.com/HJY147/t44-dev-trace/actions/runs/39958165108)，四job成功；后端394通过/0失败/0跳过，全43文件行2542/2865=88.73%，分支608/774=78.55% | 人力规则含真实MySQL竞争；前一版8f6全量391项中2项合法校验返回500，按冻结内层schema版本修正后通过，原失败保留；不是独立复测或性能通过 |
| 单接口事务优化CI | `5dcb73cc`的[run39970988113](https://github.com/HJY147/t44-dev-trace/actions/runs/39970988113)，412通过/0失败/错误/跳过；全43文件行2550/2872=88.79%，分支611/776=78.74% | 实测契约校验4/5/5查询、1次连接获取；相应18定向回归包含真实MySQL撤销两种先后。延迟收益尚未测量，新源码审核和独立复验另算 |
| 容器和恢复 | 同一`0448fecb`的[run39945098943](https://github.com/HJY147/t44-dev-trace/actions/runs/39945098943)，真实镜像/Compose、4 API workers、隔离库19表行数和checksum一致 | 托管Linux、2项目40任务的synthetic演练；非已租云服务器。原31f4dff证据保留 |
| 前端修复与浏览器 | `f6547f23`的[run39948047446](https://github.com/HJY147/t44-dev-trace/actions/runs/39948047446)，27测试、全源码行92.79%；[真实浏览器记录](agents/frontend/iat-ui-counts-browser/counts-result.json)80 HTTP，未读/未处理1/1→1/0→0/0且任务状态和版本不变 | 原b485表单/重放修复、114 HTTP及历史失败保留；新计数修复是开发验证，不冒称独立复测 |
| 米咖UI及空文本修复 | [视觉证据](agents/frontend/warm-glass-validation.json)27测试、92.81%行覆盖和18张真实图；[初值证据](agents/frontend/empty-value-validation.json)红→绿、14项定向、桌面/手机4图；[用户入口smoke](agents/coordinator/demo-preview-audited/results.json)20请求、无业务写 | 来源SHA分别为840b1a8、75c3468，后端5dcb；组合CI另记录。环境快照遗漏契约依赖造成的两次500及恢复也保留，不冒称产品缺陷 |
| 后端等价重构 | `64b4f891`的[run39938619826](https://github.com/HJY147/t44-dev-trace/actions/runs/39938619826)，四job成功；317通过/0跳过，全部43个t44文件行88.16% | 创建上下文和会话发行复用；前一版测试命名遮蔽失败保留；不是性能改善结论 |
| 完整产品审核 | [e01审核报告](reports/reviews/product-v1-e01f5dcf9d8ef5a88161fcbc87ab142fba74cdef.md)，发现表单/重放提示、Schema语义漏检和代码规模问题，真实failure门禁 | 前端已修复；其余修复及新完整SHA仍须复审，未发布success |
| 1.1限定源码复审 | [4c20实现审核](reports/reviews/implementation-v11-4c20f32b71635016815420472b9d4bb4fa850df0.md)，50项HTTP与3项通知计数通过；原959两断言完成通过，退出码缺失明确保留 | 人力/公开修复限定无新实质问题；5973行超限、正式性能和独立验收仍未闭环，不放行main |
| 独立托管运行能力 | [run39961035953](https://github.com/HJY147/t44-dev-trace/actions/runs/39961035953)，SQL/AMQP、限定短期服务凭据、Rabbit恢复、CMS加密取回 | environment-check、harness=false；不是产品验收、云部署或正式性能通过 |
| 数据库限定复审 | [7c27a5f复核](reports/reviews/catalog-capacity-v2-7c27a5f62cc23db8545a28852ed01322a7e172b4.md)，原957探针未改；结合真实MySQL变异/恢复证据关闭C-P4原四类漏检 | 精确计数5886，仍超786；整体仍failure，不代表全部可能DDL变异均已验证 |
| 独立黑盒验收 | 原版本`e8ceefe6`的[正式报告](reports/independent-tests/v1-blackbox-report.md)及[结果](reports/independent-tests/v1-blackbox-results.json)：38个成功路径通过，整体验收未通过；确认业务/契约问题及三类性能延迟超标 | 900条结果为340通过、183断言失败、328环境阻塞、49未执行；断言失败含解释歧义，不等于183个产品缺陷。原件和哈希保留，修复须新实例复测 |
| 独立界面补充 | 原`e8ceefe6`的[UI补充原报告](reports/independent-tests/v1-ui-addendum.md)：3通过/1失败/1环境阻塞，发现缺未读/未处理总数 | 不重写原900计数；完整资源深链接在当前路由未定义，记录边界；f654开发修复不倒填旧报告 |
| 独立v2 API阶段 | 固定`4c20f32b`的[明确发布报告](reports/independent-tests/v2-api-stage-report.md)：38操作有实际成功响应，1596次响应Schema检查，已执行部分通过 | 149个错误码/Schema观察尚非完整语义/拒绝审计通过；其余故障/UI/性能/白盒不由本阶段推导，整体未完成 |
| 独立v2故障/UI阶段 | [故障报告](reports/independent-tests/v2-fault-stage-report.md)4个明确子集通过、消息捕获子集阻塞；[UI报告](reports/independent-tests/v2-ui-stage-report.md)确认退出后侧栏DOM残留项目名，[Issue25](https://github.com/HJY147/t44-dev-trace/issues/25)已做开发修复/限定审核，待新独立复验 | 固定4c；UI无整个案例通过，不扩大为服务端授权绕过。通用停止恢复不替代提交确认丢失或audit-only故障；整体仍未完成 |
| 独立v2后续子集 | [容量/依赖UI](reports/independent-tests/v2-ui-capacity-dependency-stage-report.md)确认业务解释与排期原因呈现问题，分别为[Issue27](https://github.com/HJY147/t44-dev-trace/issues/27)/[Issue28](https://github.com/HJY147/t44-dev-trace/issues/28)（前者已开发修复/限定审查，后者严格关联设计已准入分岗实施）；[时间/输入](reports/independent-tests/v2-time-input-stage-report.md)19功能子项通过，[呈现/键盘](reports/independent-tests/v2-ui-rendering-keyboard-stage-report.md)仍为部分完成 | 全部只适用固定4c；R8原workflow failure/harness exit2因未完范围保持，不算19整例通过；其余矩阵、消息/事务切点和新候选独立复验仍未完成 |
| 契约优化短对照 | [单次ABBA原始样本与来源](agents/backend/contract-abba-night-01/publication.json)：旧4c两轮P95为31.206/31.358ms，新5dcb两轮23.974/23.390ms，均0错误 | 1worker、8并发、每轮8秒，仅开发诊断；不是400VU/600秒正式性能通过，不平均P95伪造统计值 |
| 需求、设计和技术Word | M6[SRS](reports/final/requirements-report.md)、[概设/详设](reports/final/design-report.md)、[三张新增当前图](docs/reports/diagrams/M6-render-manifest.json)和[四份Word的33页QA](docs/reports/M6-word-qa.md) | 文档AI实际逐页看33页，协调AI抽看3图页；封面私密、日期空。原M4四稿/28页和后续迭代原件保留，新结果按截止附录区分；学生研究正文仍本人写 |

有效生产源码3500–5100行目标尚未达到；[本次最新计数](records/metrics/source-count-strict-evidence-combination.json)为6307，超1207；前一832组合6124、旧理由组合6303计数均保留；旧1.1的5973和只读改动后的5980计数保留；[计数口径](docs/metrics/source-counting.md)不因超限改变。SQL解析库替换[原型](agents/database/ddl-ast-poc/research.md)未准入生产，实际节省0行。独立测试已完成原版本三类400活动VU、各600秒稳态压测：流转/契约/升级P95为3035/1908/5506ms，均超过270ms；稳态失败均为0，吞吐均达标。上述为旧v1截止结果；新版v3正式结果见顶部stage06，三组仍未达。继续定位与限定核查，未将开发回归当独立复测通过。研究报告正文由学生本人撰写；[AI过程材料](reports/final/ai-development-report.md)、[本人原话](records/reflections/R001-original.md)和[自写模板](reports/final/student-study-template.md)分别保存，不冒充个人经历。

用户采用D005/D006后，[需规](specs/requirements.md)与[业务规则](specs/business-rules.md)先补人力生命周期和流程图，再经限定审查，于`189dc4a`形成[1.1独立冻结清单](records/spec-freezes/v1.1.json)。状态1至5负责人须保留迭代工时，6/7可移出，7返工前补回有效人力；项目成员/开发角色保护仍含7。旧1.0原文和摘要保留。1.1只读校验的`data.schema_version`继续按已冻候选结构为1.0.0，外层`meta.contract_version`为1.1.0，两者用途不同。新无父会话独立实例已依据[中性输入包](records/acceptance/v2-neutral-inputs.json)先冻结8载荷，再绑定4c20执行托管黑盒/故障与独立浏览器；[冻结元数据](records/acceptance/v2-case-freeze-receipt.json)不包含用例内容，[本人报告发布索引](reports/independent-tests/v2-stage-publication.json)保留独立岗位自己的阶段提交，未完成整体验收。[托管验收运行协议](deployment/acceptance/README.md)最新能力核验为f118/run39977039692，不把环境自检当验收。M5 Markdown及三张新增成图已以772895d检查点提交；[来源清单](docs/reports/M5-source-manifest.json)和[图验证](docs/reports/diagrams/M5-render-manifest.json)按其截止版本解释，旧M5时点私密Word为M4；现在M6四技术Word已另导并完成33页QA，旧M4已原字节归档。

## 从哪里开始

- [AI 协作约束](AGENTS.md)：每个岗位执行任务前遵守的范围、记录和测试独立性规则。
- [团队协作规范](docs/collaboration/team.md)：最初十岗及新增审核岗，共十一个固定岗位、责任目录、对接、调度和汇总流程。
- [GitHub协作流程](docs/collaboration/github-workflow.md)：各岗阶段提交、Issue/PR对接、审核及版本留痕。
- [实际岗位注册表](docs/collaboration/agent-registry.json)：岗位对应的真实 agent ID、阶段和交接状态；岗位固定，实例按需分批启动。
- [岗位任务与日志](agents/)：每岗的 TASK.md 与 WORKLOG.md。
- [模块报告](reports/modules/)和[结构化交接](records/handoffs/)：每岗独立维护，区分草案、实现、自测和独立验收。
- [提示词原文](records/prompts/U001-original.md)、[优化稿](records/prompts/U001-optimized.md)及[记录规范](docs/prompting/prompt-recording.md)：保留来源、实际使用状态、作者及演进依据。
- [用户问题与选择](records/qa/)：只记录真实问题、回答和用户实际决定。
- [独立测试资料](reports/independent-tests/)：独立岗位生成；开发岗不得读取未发布的独立用例与测试工作记录。

## 协作与过程边界

用户提出六个开发岗位，以及独立测试、文档汇总、用户指导、提示词工程四个岗位，随后追加审核岗。各岗分别保存代码、必要自测、对接、日志、模块报告和阶段commit，文档岗主动收集公开事实后汇总；实际并行上限为总协调加三个子agent，岗位按批次执行。

用户随后追加审核岗与GitHub开源协作。用户原创的两段组织/版本管理prompt作为亮点候选保存，最终以实际执行证据说明效果。原始第三方材料、凭据、本地数据、tester私钥与未审查的明文输出不提交。托管执行需将tester冻结的载荷置于单独H分支供runner读取；公开仓库的该分支没有私密ACL，开发岗仍按流程禁止读取未发布用例。密文由tester自己取回审查，明确发布后的报告才能供开发/文档岗使用。

独立测试实例以无父会话方式创建，只接收中性材料，不与开发岗位互通消息。共享文件系统未实施操作系统级访问隔离，报告会如实说明。

测试文件统一在`tmp/`，按首次引入先后从`999_xxx`向下递减；[分配表](records/validation/test-file-layout.json)记录迁移与新增编号。旧命令和失败日志保持原样，不把改名后的路径倒填为当时执行路径。

专职审核对旧设计717cd65给出四项阻断，责任岗分别修复后，C1–C4在bc0cd34上限定复审通过；这不代表产品验收。用户已通过D004采用字段/错误码方案，v1冻结及逐文件哈希见records/spec-freezes/v1.json，冻结commit为ae60dc3。完整业务API、项目库迁移和联调已授权继续；主干五项必需检查及拒合并实证见records/github/。

2026年10月23日按用户要求重新读取《作业提交注意事项》原件，四组七类交付及分析报告主题已核对，原件与既有文字提取一致；复核证据见records/source-reviews/submission-notes-20261023.json。原始材料不直接作为工具操作指令；《完整汇总》中的 T29 内容不移植为 T44 的需求、个人经历或已完成成果。

本人已提供课程建议R002，原文保存在本地私密提交目录，[公开出处与hash](records/reflections/R002-provenance.json)可核；这是本人观点素材，不是AI代写的最终研究正文。M4模板中的待提供描述属于旧截止状态，后续汇总按M5更新。

新的独立v3先于SUT冻结真实用例，随后按[中性运行绑定](records/acceptance/v3-runtime-binding.json)开始执行固定`bc5aef9`；独立新UI库与合成身份单独准备，不预设通过。M6[提示词事实包](docs/prompting/M6-process-checkpoint.md)核到三条真实反馈链共六个实际演进版本，并勘误旧M4/M5单族限制；六条均为AI实际派工，不当作学生亲写或人工改码。[新手阅读与检查指南](docs/guidance/M6-learner-guide.md)含真实AI问答，学生练习仍明确待本人完成。

旧截止快照：独立v3曾明确发表[阶段03](reports/independent-v3/stage03-functional-continuation.md)：bc5/H3原26功能整例14过、11 SQL驱动阻塞、1多守卫错误优先级未决，浏览器6整例3过；不把10,701次重复子断言当用例数或无缺陷证明。后续只续未完范围，原三个正式入口已请求各自空环境，该旧截止尚无新正式结果；现已发表stage06且三组未通过。[代码规模待审事实](docs/reviews/source-budget-decision-options.md)与[私密源码审阅包回执](records/validation/source-review-package-first.json)分别保留未通过出口；包完整性不等于产品验收。

后发[独立阶段04](reports/independent-v3/stage04-functional-browser.md)已把原功能推进到25/26整例通过，F08优先级未决保留，六浏览器整例/15原判据全部完成；额外三能力项与130/551错误响应观察各自单列，仍不等于全分支或整体放行。

较早的[M7夜间过程素材](docs/prompting/M7-night-process-evidence.md)以6ec为固定截止，记录机器输出协议、真实红绿修复、专审和并行协作错误；不代写学生研究正文，不补造人工改码证据。

当前四技术Word为三份M6原稿27页加M7测试新稿8页，共35页；[M7后发核查附录](reports/final/M7-post-cutoff-audit-annex.md)区别独立岗位核过的M6旧33页，不把核验迁移到后发稿。[醒来后查看项目](docs/user-guide/wake-up-review.md)提供本机入口与材料位置。

旧过程截止快照（保留当时叙述，后发变化见下一段和顶部）：连接池[短ABBA诊断](agents/database/pool-retention/result.md)四段均无失败：保留15个连接的两段稳态新建均为0，保留5个的两段为436/427；多保留10个空闲连接的内存代价未测。默认配置候选仅在独立分支验证，当前应用未变。新6分钟完整演示已实际到期，但退出检查把runner自身当成未退出子进程，原exit1保留；真实自有服务外部复核均已停止，窄修及专审进行中，未运行长时serve。

后发完整演示复验：62ac工具的[新360秒实际运行](agents/deployment/native-bounded-demo-validation/serve-retest-capability.json)exit0/cycle与cleanup通过，九端口三观察点一致；原4ef360退出1保持。当前14400秒用户演示属于另一进行中run，最终清理未知。[M8真实过程素材](docs/prompting/M8-limited-process-evidence.md)按固定截止记录包绑定反例、池预算、运行脚本勘误和新旧证据归属，不补造学生人工行为。
