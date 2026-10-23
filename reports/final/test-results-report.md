# T44测试结果技术报告

版本：M5阶段技术工作稿 v0.5，**未完成整体验收，不能判总通过**。生产内容固定`6ba9f94ad23ac96380269aaefa8726f8b535b450`，后端5dcb、前端75；cutoff后收到的同源CI、独立阶段和限定审核公告单列。本文由文档AI汇编公开结果，不重新执行产品测试/业务请求/负载，不接触独立私密用例、日志、密钥或截图。公开封面无个人值，日期空。

Agent-Role documentation；Prompt-Ref ROLE-documentation-M5-REPORTS-v1；Refs #9。

## 1 准确版本与层次

| 层次 | 精确对象或来源 | 结论边界 |
| --- | --- | --- |
| M5代码截止 | 6ba9f94；冻结1.1.0的14文件 | 版本标识不等于验收结论 |
| 后端读UoW开发CI | 5dcb73cc10c38deb14fae68d33318b04d538fecf；run39970988113 | 412/0失败/0错误/0跳过，全43文件，不是独立验收或性能 |
| 暖色视觉开发 | 840b1a88e6976f0ecfb0b0ba45676b208aae4d98；63519c2证据 | 27测试/18实界面图/40HTTP；不覆盖后续props修复 |
| 空文本小修 | 75c3468de07303cc47b9afd0e4a169664743470e；6212e5f证据 | 同组红2→绿6，受影响14/20HTTP/4图；当轮没有重测coverage |
| 独立v2 API公开阶段 | 4c20f32b71635016815420472b9d4bb4fa850df0；原样归档54af1e3 | 38成功操作/1596响应Schema、14执行函数，仅各自已执行子集 |
| Linux中性能力 | 环境f118f9dd35bc2cde69affe235f5a499d03a396fc，SUT仍4c20；run39977039692 | harness/profile=false；不是故障用例或总验收 |
| M4历史技术材料 | 2e0481f/0448fec，四Word28页QA | 原文/失败/QA保留，不自动包含M5代码和结果 |

[1.1冻结清单](../../records/spec-freezes/v1.1.json)、[412开发汇总](../../agents/backend/read-uow-ci-summary.json)、[前端视觉](../../agents/frontend/warm-glass-validation.json)、[空文本](../../agents/frontend/empty-value-validation.json)、[独立API公开报告](../independent-tests/v2-api-stage-report.md)/[JSON](../independent-tests/v2-api-stage-results.json)分别可核。独立公开文件里的私密路径和hash不构成读取许可。

## 2 开发CI与覆盖率

5dcb的[run39970988113](https://github.com/HJY147/t44-dev-trace/actions/runs/39970988113)四job成功，原JUnit412/0/0/0。全部43个backend/t44生产文件纳入，excluded_lines=0；行2550/2872=88.7883%，分支611/776=78.7371%。综合line+branch百分比86.6502%不是行覆盖率，不新增分支80%门槛。contract114/integration70/fault11标记相互重叠，不能加到412之外。

18项读UoW专项已包含在412中：HTTP11、真MySQL7均通过。改前4+5个失败为新优化目标/在途读语义断言，不是9个旧业务缺陷。三类成功4/5/5 SELECT和一次acquire有账本；COM_PING/初始化SET/commit/rollback不在SELECT统计，不能换算总网络往返或P95改善。源码限定复审见[5dcb报告](../reviews/read-uow-5dcb73cc10c38deb14fae68d33318b04d538fecf.md)。

历史394绑定4c20；更早335/88.47%绑定0448、317/88.16%绑定64b4。不同被测SHA、不同分母不互换；M4原95附件/归档仍见[原技术报告](https://github.com/HJY147/t44-dev-trace/blob/9e9e23d83ab2426ed490bd5457e7007047d2ca67/reports/final/test-results-report.md)及records/ci/39945098961。

## 3 各模块自己的测试和接口边界

| 模块 | 实际输入输出及公开模块证据 | 不可外推 |
| --- | --- | --- |
| frontend | 冻结Schema→字段/操作表单，api.request→Envelope；840视觉27，75组件红绿/受影响14，真实HTTP只读与图见下一节 | 开发浏览器不是学生手测/独立UI；75当轮没新coverage |
| backend/domain/services | Call/validate→Runtime四元组；纯decide→Decision；1.1人力/鉴权/幂等/CAS/审计与读UoW全量412 | HTTP/注入故障不自动成为真实宕机、全551错误语义或正式性能 |
| database | UoW/Rows/迁移/Outbox/Scan已实现；旧真MySQL四类语义漂移/恢复、seed行摘要等证据保留 | 新scan-run去重RFC净增1、未准入，生产节省0；AST原型46/1不当完成 |
| messaging | Runtime传入g/Call→通知data；worker在事务外broker I/O，消费提交后ACK；旧28/3本机Rabbit未跑和真MySQL11分开 | 最新托管CI有真实MySQL/Rabbit，不倒填原本机skip；消费记录唯一非网络恰一次 |
| scheduling | Scanner.run/tick→持久scan_run；EscalationFacade.create→event/created/task_version；原模块107含22真MySQL/ASGI/CLI、20任务与续扫 | 原模块干净重启/扩展配置实验非400并发或完整中批崩溃验收 |
| deployment | 原Docker/隔离恢复与新中性环境能力分别绑定SUT；52 guard/Ruff/actionlint为本岗验证 | harness=false不当tester执行，六服务恢复集合不当六服务均已故障 |

各FR→概设→详设/真实代码→本模块用例/日志→剩余验收见[M5追踪矩阵](../../docs/reports/M5-traceability.md)。测试入口为tmp/backend、tmp/frontend及原递减编号；不改历史日志中的原命令，不相加不同岗位/版本用例数。

## 4 UI设计、导入及空文本红绿链

326f971先形成DESIGN/合成原型/来源许可及8原型图，协调者实看4样本后才实施840；原型未连业务API。840的27/27、全19 TS/Vue源文件行310/334=92.81%、分支687/782=87.85%、函数188/222=84.68%，typecheck/build通过，825.22kB JS>500kB告警保留。18张真实界面图由前端AI检查，40响应全200、两次登录POST其余GET、0业务写/页面错误/横溢出；不能当全业务写流程或完整可访问性验收。

真实样式覆盖曾使关闭按钮越界，修正后测长表单滚动；隐藏背景选择器超时与过渡截帧属于工具/截图局限，原件保留。减少透明度CDP实际matchMedia=true；不支持backdrop引擎只源码检查，未完整测focus陷阱/读屏/其他浏览器。

FE-INIT-01先设计7369400再修75：Vue生成props中Boolean先于String，将空串强转true；纯initial()无错。显式modelValue运行时type:null/静态PropType<Json>保留JSON原类型，未改Schema/API/initial业务默认。新增三项现有测试，改前2失败/4通过/24未选，同组改后6通过/24未选，受影响组14通过/16未选，6不另加到14。build含typecheck通过，大chunk告警保留；当轮无新coverage，不能将840覆盖率套给75。

首次浏览器登录502、未进入表单也无截图，保留为环境阻塞。演示恢复后1440/390三文本DOM空值/必填错误有效，20HTTP全200、两登录+18GET、0业务写、4图由前端AI检查。本文只汇编其公开证据，不冒称本岗重新浏览器执行或亲看这些UI截图。

## 5 独立v2 API阶段 已发布子集

SUT固定4c20，先冻结后接触，API恢复没有重跑已完成案例。38个操作有实际成功响应，1596条HTTP通过冻结响应Schema；14执行函数含SETUP和只读取回，不是14个完整验收要求。已发布范围未确认产品缺陷不等于证明产品无缺陷。

- 生命周期/发布回滚/返工、部分依赖、评审、输入/权限/时间域、人力与通知服务边界已执行各自子集。
- 同版本不同键30次双请求均一成功/一409；创建/分配/返工与容量移除各30次共90次竞争。尚未逐轮独立证明全部审计/outbox计数或所有幂等竞态。
- 551逐操作错误条件：149仅“声明码及响应Schema观测有效”、399未执行、2公共API不可达、1可达性未明。149尚缺完整语义/前后持久状态/拒绝审计，不是149完整错误用例通过。
- 18业务表226列名称/类型/可空/自增一致；非完整CHECK/FK/index/default和应用连接事务/时区审计。审计连接8.4.13/REPEATABLE-READ/time_zone SYSTEM不等于应用连接配置已验证。
- 原fixture误解包data.task、个人通知未给项目过滤器、依赖201误判200，均是独立脚本/前置勘误，产品未因此修改。原记录保留。

当时故障分支缺逐次恢复/拓扑而BLOCKED，driver wrapper PASS非故障通过；正式性能、白盒/CI/规模、UI不由此API阶段下结论。不能把后续能力环境或开发5dcb结果倒填本阶段。

## 6 cutoff后收到的独立故障阶段公告

此项原样归档于**68eb5e1，晚于6ba内容截止**，不合并/改写6ba历史。仅明确发布的[故障MD](https://github.com/HJY147/t44-dev-trace/blob/68eb5e1/reports/independent-tests/v2-fault-stage-report.md)、[结果JSON](https://github.com/HJY147/t44-dev-trace/blob/68eb5e1/reports/independent-tests/v2-fault-stage-results.json)和publication receipt被读取，不跟随其私密路径。

run39998518039仍固定4c20：4个真实故障子集PASS、1个原消息捕获BLOCKED，另SETUP；513HTTP属于本阶段，不与1596合并成无重叠总数。5次不同recovery_id逐次回执真实恢复；这是stop路径，不借环境pause自检宣称产品pause用例通过。

| 子集 | 已证明 | 未证明 |
| --- | --- | --- |
| SCAN-01 | 20逾期含5阻塞、最高级2/完整收件人快照/一次计数，干净重启65秒重扫不重 | 扫描中批崩溃/cursor恢复 |
| MQ-01 fallback | Rabbit停期间本账号20条fallback、读/处理区分且任务不变，恢复不重且新事件非fallback | 全收件人实际投递、确认歧义、迟到原消息 |
| TX restart | API停/恢复后已提交任务快照及两成功审计记录取回字节相同 | 事务中途、丢提交ACK或独立拒绝审计故障 |
| TX DB down | MySQL停时授权读取503/audit_id=null，恢复后任务相同 | audit-only故障或数据库宕机仍可审计 |
| 原消息重复 | 未安全捕获原消息，BLOCKED | 未执行重复发布后置断言，不称产品去重失败 |

整体验收仍未完成；六服务恢复范围不代表六服务都受过故障。101人、边界时钟、完整矩阵、正式性能/白盒仍待。

## 7 原独立v1与正式性能历史

原e8ceefe699951c52d4b01023b47a76b575d48c2a四公开报告保持原结论：900严格分布340通过/183断言失败/328环境阻塞/49未执行；183含97 Retry-After语义歧义和15引用/守卫顺序问题，不等于183bug。38成功路径通过。UI附加3通过/1失败/1完整用例阻塞，原900不改；通知页双总计缺口与深链阻塞分开，不能声称原报告测过b485/f654/暖色版本。

| 原正式入口 | 活跃闭环VU/稳态 | P95 ms | 次/分钟 | 稳态失败 |
| --- | --- | ---: | ---: | ---: |
| transition | 400/600秒 | 3035 | 6910.1 | 0 |
| contract validation | 400/600秒 | 1908 | 23396.5 | 0 |
| escalation | 400/600秒 | 5506 | 3483.6 | 0 |

三者均超270ms、exit99；吞吐≥1000与稳态零失败通过。不是400个瞬时socket；同机Mac/API4worker/MySQL/k6，WPS背景存在，未独立采样API/DB资源，不推定瓶颈或云容量。40/6000/9000/11400评审+3600决定全synthetic，批次未清库，准备时调整604依赖而保持9000总数；202仅持久受理非broker端到端送达。后续短诊断或少SELECT不当正式达标。

## 8 容器、环境与工程过程

M4原0448fec/run39945098943的完整Compose/API4worker、小synthetic2项目40任务、停写备份→新隔离库19表count/checksum一致保留原件，非后续版本自动复测。新f118/run39977039692只中性能力：真实SQL/AMQP、受限服务凭据、stop/pause逐次恢复及synthetic加密roundtrip；harness/profile=false，不当独立故障通过。原pause后unhealthy失败与后续有界健康观测修正保留。

6ba演示前端75→后端5dcb的907小smoke，1440/390各20卡，0资产/API失败/页面错误/横溢出，两登录+18GET、0业务写，协调者实看两样本。原frontend-only快照漏冻结JSON后500，补文件仍500，重启/新cache/明确fs范围组合后200；**未单独证明负缓存是原因**。shell未短路误续检查为AI过程错误，不是产品源码缺陷或学生识别。独立4c入口仅中性恢复，无reset/provision/业务请求；不读独立UI未发布结果。

## 9 审核、规模与退出条件

1.1设计、冻结前复核和4c20实现、5dcb单UoW均是准确SHA的限定审核，整体未放行。旧e01四项failure保留，C-P4在7c27限定关闭不证明所有DDL变异。当前原cloc2.10非空非注释物理口径，[f289统计](../../records/metrics/source-count-empty-text-fix.json)64应用文件6051行，超5100上限951；--require-range实际exit1，不改分母、不将草案预算当节省。

cutoff后实收到审核岗公告：840视觉d8bba16限定无新阻断；75空文本36b90e3限定FE-INIT-01关闭，均非APPROVE/status成功或整产品放行。公告、实际问答和公开固定报告链接见[M5收集](../../docs/reports/M5-collection.json)，不说6ba当时已含这些后续回执。

最终须准确新头完整CI/源码审核、独立剩余矩阵/正式性能/规模与作业交付证据齐备。R001本人反思、R002课程建议已收，研究正文仍本人写，人工12/3/5和单族六版不由AI修复/图批次抵充。M4 Word28页QA只技术排版；M5 Markdown未导Word。

## 10 cutoff后同源组合CI与Docker公告

root在本轮实告：**同6ba源码**的PR run39999929187四job成功，后端412/0失败错误跳过、43文件2550/2872；前端30/0/0、19文件310/334=92.81%、分支688/782=87.97%。这是75已纳入组合源后的新证据，不能继续概括“75一直没有覆盖率”；第4节“当轮未跑”仍是当时事实。checkout9c2a整tree与6ba相同由root核验，原artifact及摘要后由root在b9f7fbd明确公开；本岗已读composite-6ba-ci.json，并对选定原JUnit/coverage进行轻量解析，准确hash列本轮manifest，不重跑CI。

同6ba的Docker run39999920326也passed：4worker、2项目40任务、19表count/checksum匹配。它是同源小synthetic容器/恢复，不是正式性能、独立总验收或规模达标；公开原件发布后按来源清单核对，不追改M4 Word。

## 11 cutoff后收到的独立UI阶段公告

root在b9f7fbd原样归档[UI公开MD](https://github.com/HJY147/t44-dev-trace/blob/b9f7fbd/reports/independent-tests/v2-ui-stage-report.md)/[JSON](https://github.com/HJY147/t44-dev-trace/blob/b9f7fbd/reports/independent-tests/v2-ui-stage-results.json)。仍固定4c20、5175→18084，与暖色演示5173不同。10冻结用例：0完整PASS、1FAIL、1BLOCKED、8未执行或只部分观察，不把子条件提升整例。

V2-UI-001/P2是logout200后侧栏rendered DOM残留前项目名，后退11秒后仍有、完整刷新才清除；仅DOM清理失败，不据此认定服务端越权、保留任务行、登录覆盖下像素可见性或外部泄露。既有截图在刷新后，不能证明残留；本岗没有打开私密截图/日志。Issue25由root转派修复，**本稿不称已完成或独立复测通过**。

七态/评审/四视角/409后权威读取、局部窄屏和键盘等只观察部分；本地故障能力未绑定使UI08阻塞，托管API通知不能替代浏览器通知通过。原14个驱动器错误与产品发现分开，未把它们当14bug。

## 12 cutoff后短ABBA诊断公告

公开来源为072bc4e的[publication](https://github.com/HJY147/t44-dev-trace/blob/072bc4e/agents/backend/contract-abba-night-01/publication.json)。root实告单次ABBA：A4c的P95为31.206/31.358ms，B5dcb为23.974/23.390ms，均0错；条件为1worker、8并发、每段8秒，整体39.88秒exit0，18083已停。它只支持这组短对照，不能替代原400VU/600秒/4worker正式负载、其他入口P95、独立验收或云容量，亦不扩大为已知性能瓶颈归因。
