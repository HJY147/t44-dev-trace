# T44 软件开发大作业

本项目选题为“中小软件外包团队研发流程留痕与上线评估管理系统”，应用名“留痕”。[公开仓库](https://github.com/HJY147/t44-dev-trace)采用MIT许可证。已实现Vue业务界面、38项冻结API、MySQL事务与审计、RabbitMQ通知、独立APScheduler扫描和Compose部署工具，仍在审核、独立验收与规模优化阶段。完整集成见[draft PR #21](https://github.com/HJY147/t44-dev-trace/pull/21)；受保护main尚未发布该完整产品。

## 功能与运行

支持项目成员与角色、迭代产能和排期、任务依赖、七状态流转、八段十项评审、四视角上线风险和回滚预案、经理交付/回滚/返工决定、三级延期提醒、通知已读/处理和审计追踪。发布和回滚记录人的决定，不替人操作外部生产系统。

技术栈：Vue 3 / TypeScript / Element Plus，FastAPI / Python 3.12，MySQL 8.4，RabbitMQ，APScheduler，Docker Compose。单体分层，API、消息和扫描分别运行；不将多agent开发岗位当作业务微服务。

请按[单机运行与恢复说明](deployment/README.md)配置、构建、显式迁移、初始化账号和签发调度身份。凭据随机生成并私密保存，不提供可直接公开登录的默认密码。部署说明包含停写备份、新隔离目标恢复和SSH隧道访问步骤。

## 界面与设计过程

界面采用用户指定的米色、浅咖啡色、多圆角与玻璃层次。[OpenDesign来源与视觉规范](docs/ui/warm-glass/DESIGN.md)、[可点击原型](docs/ui/warm-glass/prototype.html)先形成设计提交326f971，再以840b1a8导入Vue；使用的是官方本地agent技能/模板工作流。可查看[实际桌面](agents/coordinator/demo-session-fix-smoke/1440-workspace.png)与[手机](agents/coordinator/demo-session-fix-smoke/390-workspace.png)截图，合成数据明确标记。

浏览器检查发现的既存空文本强转true另以7369400设计、75c3468修复及6212e5f证据留痕；[视觉审核](reports/reviews/warm-glass-840b1a88e6976f0ecfb0b0ba45676b208aae4d98.md)与[初值补充审核](reports/reviews/empty-value-75c3468de07303cc47b9afd0e4a169664743470e.md)分开记录。开发验证、审核和独立验收保持不同范围。

## 可核对的阶段证据

| 范围 | 实际证据 | 边界 |
| --- | --- | --- |
| 最新组合CI | `8323692`的[run40016165656](https://github.com/HJY147/t44-dev-trace/actions/runs/40016165656)四job成功：后端437项、全43文件行2558/2878=88.88%、分支612/778=78.66%；前端65项、全19文件行353/379=93.13%、分支783/894=87.58%；[原件与适用版本](records/validation/composite-832-ci.json) | 后端A产品153b9c8、前端容量说明3628ee1，完整分母无排除；开发CI不等于独立复验、正式性能或规模达标。另一次自动PR触发的同head CI状态单列，不重复计测试 |
| 同源容器和恢复 | 同一`8323692`的[run40016165658](https://github.com/HJY147/t44-dev-trace/actions/runs/40016165658)真实Linux/Compose、4 API workers、19表恢复行数与checksum一致；18业务表226字段复核通过 | 2项目40任务的synthetic演练；不是已租云、正式性能或独立验收。共享flock第二扫描器预期exit1，原件保留；原6ba记录不覆盖 |
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
| 需求、设计和技术Word | [SRS](reports/final/requirements-report.md)、[概设/详设](reports/final/design-report.md)、[8张成图](docs/diagrams/README.md)及[四份Word的28页QA](docs/reports/M4-word-qa.md) | 四份本地技术审阅Word均逐页查看，含私密封面、日期留空；M4内容有明确cutoff，后续1.1及最终验收须另更新；学生研究正文仍由本人写 |

有效生产源码3500–5100行目标尚未达到；[本次最新计数](records/metrics/source-count-preflight-ui002.json)为6124，超1024；旧1.1的5973和只读改动后的5980计数保留；[计数口径](docs/metrics/source-counting.md)不因超限改变。SQL解析库替换[原型](agents/database/ddl-ast-poc/research.md)未准入生产，实际节省0行。独立测试已完成原版本三类400活动VU、各600秒稳态压测：流转/契约/升级P95为3035/1908/5506ms，均超过270ms；稳态失败均为0，吞吐均达标。当前正在修复和剖析，未将开发回归当独立复测通过；准确新版完整审核及最终提交文档仍在进行。研究报告正文由学生本人撰写；[AI过程材料](reports/final/ai-development-report.md)、[本人原话](records/reflections/R001-original.md)和[自写模板](reports/final/student-study-template.md)分别保存，不冒充个人经历。

用户采用D005/D006后，[需规](specs/requirements.md)与[业务规则](specs/business-rules.md)先补人力生命周期和流程图，再经限定审查，于`189dc4a`形成[1.1独立冻结清单](records/spec-freezes/v1.1.json)。状态1至5负责人须保留迭代工时，6/7可移出，7返工前补回有效人力；项目成员/开发角色保护仍含7。旧1.0原文和摘要保留。1.1只读校验的`data.schema_version`继续按已冻候选结构为1.0.0，外层`meta.contract_version`为1.1.0，两者用途不同。新无父会话独立实例已依据[中性输入包](records/acceptance/v2-neutral-inputs.json)先冻结8载荷，再绑定4c20执行托管黑盒/故障与独立浏览器；[冻结元数据](records/acceptance/v2-case-freeze-receipt.json)不包含用例内容，[本人报告发布索引](reports/independent-tests/v2-stage-publication.json)保留独立岗位自己的阶段提交，未完成整体验收。[托管验收运行协议](deployment/acceptance/README.md)最新能力核验为f118/run39977039692，不把环境自检当验收。M5 Markdown及三张新增成图已以772895d检查点提交；[来源清单](docs/reports/M5-source-manifest.json)和[图验证](docs/reports/diagrams/M5-render-manifest.json)按其截止版本解释，私密Word仍为M4。

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
