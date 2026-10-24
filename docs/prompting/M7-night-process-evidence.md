# M7 夜间真实过程素材与学生自写索引

操作者：提示词工程岗AI；实际派工`ROLE-prompt_engineering-M7-NIGHT-CHECKPOINT-v1`。这是事实与问题索引，**不是学生最终研究正文或第一人称经历**。本轮内容cutoff固定根`6ec8d3c93f4ff5283d3db62ae7993e66c4c54ca2`，用户预览另绑定已发布`2e58381`。先行设计已实际提交/推送`4c476c634d019e74ef41a27c10deeb9bc4c5a07b`，之后才向四岗问取及整理。后发性能/源码诊断不追改本cutoff。

M6已核三条反馈链共六条实际演进、原M4/M5过严“单族六版”勘误保持。此次任务ID、工具修正和每次运行不自动增计版本。U001/U002仍优先展示用户原创；U019夜间自治只授权普通实现问题继续处理，大业务取舍仍单独保留。全部新实现/审核/运行与资料整理均属AI执行，不记学生亲改、人工验收或人日。

## 1. 先把环境输出协议说清楚，再修适配

| 公开输入/阶段 | 真实问题、修正与验证 | 不能延伸为 |
| --- | --- | --- |
| 独立v3 stage01/02公开MD+JSON | init-user控制exit0却stdout非确定JSON，26功能整例未执行；stage02五个环境均在该边界阻塞，正式600秒稳态未开始 | 环境ready/recovery=true不能算业务或故障通过；退出码0本身不足以证明可用回执 |
| 根`2e2bffa`先写`neutral-control-stdout-rfc.md`→`cf685d7`实现 | 静态核实Docker stderr被合入机器stdout；分流两路，init-user只接受单对象、唯一user_id、真实int且1..UINT32max，拒绝bool/额外字段/混合文本，不截最后一行求成功 | 这改的是中性部署控制，不改bc5产品、冻结用例、业务预期或性能阈值 |
| `neutral-stdout-validation`原件 | 原11合成10红1绿→全63合成绿；非零/超时、两路输出、类型范围歧义均留痕。默认Ruff原4项既有诊断exit1保持；`189a4e2`用实际CI配置` scripts/ci/ruff.toml`补核exit0 | 63是合成边界，不是63个SUT验收例；官方CI配置通过不能倒写默认命令成功 |
| 独立岗自身机械修订 | stage02 factory按冻结`data.task`投影，24离线wire样例；stage03原生TSV被旧driver当JSON，70离线协议边界；stage04零行结果与浏览器定位/等待/字段绑定续修 | 开发岗未代写独立driver，也未读私密用例。驱动错误不能列作产品bug或学生发现 |
| 根只读中性SQL观察 | `mysql-batch-empty-neutral.json`两条常量SELECT证明exit0零行可产生0字节stdout，非空为header+TSV | 没有业务写，不证明某业务行数或任何业务例通过；不能把所有命令强行统一成JSON |

中性命令各有格式：init-user与scheduler-scope JSON、audit-sql TSV且零行可空、broker原生文本、成功fault可无stdout。实际I/O必须逐命令定义，不能以一次JSON修复推定所有控制返回同一种结构。后续只读runtime-metadata能力源`b3ee0ac/059b33e`有75合成边界，但根没有实际Docker观察，已发R未采集资源仍unknown，不从新能力补造运行时硬件字段。

## 2. 完整周期成功后，专审仍能发现未触发的失败边界

| 精确对象 | 已发生事实 | 结论边界 |
| --- | --- | --- |
| native实现`0a6da88`，归档`5ef1bde`，应用SUT`bc5aef9` | run1整体失败且cleanupfalse；DTO投影与shutdown CLI错误保留，后置PID/端口消失不倒写清理成功 | 首轮两次Pika连接、16事件/26通知等局部事实不是整个run1成功 |
| 同0a6的fresh run2 | driver0/cycletrue/cleanuptrue；API4worker、consumer、UI代理、两次扫描间隔60.303070秒、TTL300轮换4→5/撤销/全停 | 二轮仅复核既有16事件/26通知，不声称二轮重新发布；不是持续常驻服务、独立、正式性能或云部署通过 |
| 专审封档`c6883f2`，精确target5ef/代码0a6 | 唯一无进程反例：communicate首超时→mock SIGTERM→子命令最终rc0；原capture忽略首次超时，正常返回成功，原拒绝断言真实exit1，P2 NATIVE-CAPTURE-TIMEOUT-01 | 真实OS进程/信号均0，这是对精确函数AST的合成反例；不是run2曾失败，也未证明进程越权或秘密泄露 |
| `7f4845e`先设计→`b238978`窄修→`cc6a211`封档 | 永久保留timed_out与真实child returncode；清理未确认另失败；五边界真实码0/7/0/-15/null保留，原红、五项绿与ClassVar lint原失败分开归档 | 只修capture，不重跑完整cycle、其他守卫或服务；“15行发生变化”不是净增15，报告给物理净增9 |
| `cd3e4c2`限定复审、PR34 COMMENT5634940377 | 同事件序列和原拒绝断言语义重建一次绿；新receipt仍exit_code0但timed_out=true/success=false，抛OWNED_COMMAND_TIMEOUT | 原inline命令未单独存脚本，不能称命令文本/输出字节相同；只关闭该P2，原5ef不通过、原0a6周期事实保持，新b238未完整cycle |

公开入口：`agents/deployment/native-application-validation/README.md`、`run2-capability.json`；两份`reports/reviews/34-5ef...md`/`34-cc6...md`；`native-capture-timeout-validation/README.md`；reviewer的`capture-timeout-exit-zero-probe.json`与`original-counterexample-replay.json`。本岗只读公开原件，不执行反例、不访问私密回执索引指向的文件。

## 3. 并行协作的真实踩坑也必须保留

- `reviewer-history-merge-resolution.json`记录首次递归JSON合并遇到两侧都删除的base键而KeyError，后续换行又暂存未解冲突；`git diff --check`拒绝标记，**没有生成该错误提交**。根从不可变HEAD/MERGE_HEAD/base重新构造，保存双方完整append-only日志和旧失败/复审历史，不从已冲突暂存文件猜答案。
- `deployment-parallel-merge-resolution.json`记录部署两支的公共WORKLOG/report共同前缀+完整双方尾段；handoff的stage标量选择新native，同时把另一支metadata阶段保留为显式并行字段。`reviewer-native-capture-merge-resolution.json`保存每个冲突标量原值/新值和理由，原不通过与新限定关闭分别留存，104源文件不因处理记录冲突改变。
- 根`a4c71dc`为870预留时用泛化列表选择，误放到migration的files数组；`cee7a57`在helper创建前移到显式reservations并记录更正，未影响产品/测试文件。这是AI记账错误、AI纠正，不是产品bug或学生识别幻觉。
- 源码审阅包`source-review-package-first.json`绑定`48e3bbc`的Git正向选择快照，2581文件、hash已核、输出私密0600。它是离线审阅快照，不是最终作业包或正式release；本岗只读公开provenance，没有打开私密ZIP，也不把“打包成功”当材料或软件全部通过。

这些处理具体支持U001的责任目录/记录和U002的阶段commit/精确审核价值，也说明共享公共记录仍会冲突。没有效率对照或真人操作证据，不写节省时间、效果百分比或把Git账号名当学生亲改。

## 4. 本轮可以引用的独立结论，只来自八个公开文件

白名单固定`reports/independent-v3/stage01-environment`、`stage02-driver-binding`、`stage03-functional-continuation`、`stage04-functional-browser`各MD+JSON。未跟任何private refs/入口/日志/密文/keys，也未联系独立tester。所有阶段SUT均bc5；报告声明无产品源读取、无真人参与。

| 阶段 | 原整例与独立机械边界 |
| --- | --- |
| stage01 | 0通过/0失败/26未执行；环境输出解析阻塞，恢复true只属环境 |
| stage02 | 五次未进入业务/正式稳态；24离线驱动样例不计SUT；原失败保留 |
| stage03 | 14功能整例通过、11 TSV驱动阻塞、1 F08原断言不符；10701动态通过子项有重复契约调用，不当整例或分支数 |
| stage04 | 累计25/26功能整例通过，已完成不重跑；6浏览器整例/15原业务判据完成。130/551同操作/状态/错误码组合被观察，421未观察；组合相同不证明每条件覆盖 |

F08同时命中旧评估基线过期与改期已使旧批准失效；原期待ASSESSMENT_BASELINE_MISMATCH，实为RELEASE_APPROVAL_REQUIRED。冻结资料未确定同时命中的优先级，原断言失败和未执行后续语句保留，列规范未决，不改期待凑绿、不自行改业务错误优先级。另3个预先声明的规范/安全观察能力阻塞单计。

stage04时故障运行和三组正式运行仍待取回判读；**本cutoff无新正式性能结果或完整600秒通过结论**。根`6ec8d3c`组合CI当时待结果，已完成开发CI仍bc5的510BE/89FE，全44Python行2638/2957、分支659/824，前端全20源行364/390；自动PR重复run不再相加。开发Docker四worker/19表恢复也不能代正式独立故障或性能。代码6307超过5100计1207，未修改门槛或计数范围。

## 5. 预览与文档的验证者是谁、验证了什么

预览职责岗已发布`2e58381`，设计`627e627`→证据`c5e79e0`→交流封档。固定bc5只读archive85源前后hash相同，旧进程身份核后退役，新API24604+四worker及Vite24610绑定5173→18080。systemPython tarfile.filter准备失败、root.venv误试import失败都发生在停旧服务前；沿用已验证backend环境，无安装和产品修订。原907一次1440/390共20请求（2login/18GET）、0业务写、0错误响应事件/页面错误、4图由前端AI查看；它没有逐条记录所有成功响应状态，不能称“20个200”，也不是容量/reason业务重验。私密登录说明未读。

M6四技术Word最终10+14+6+3=33页，正文/出版引用e899、QA封档126df；首轮35页标题/短段问题、二轮34页设计空白页保留，只有设计第三轮重导到14页，其他三稿复用已看二轮。`M6-word-qa`证明文档AI逐页看33张原PNG；根公开samples receipt只实际看3页，不能改成根全看。M7本岗未打开任何私密Word/封面/PNG/PDF或重导文档。队列内部旧`technical_reports.Word_current_status`仍写35页ongoing，而同一队列work_items及最终QA已33完成；当前排版结论取最终逐页QA，旧字段作为滞后元数据，不假称源完全同步。排版完成不等软件验收或学生本人审稿。

## 6. 可选亮点与留给学生自己的问题

可选亮点按优先级选择：

1. **U001用户原创：固定岗位、职责产物与上下文隔离。** 可用本轮至多四岗实问/实回和独立只读白名单展示执行，明确共享文件系统仍是流程隔离，AI岗位不是真人团队。
2. **U002用户原创：GitHub阶段版本与绑定SHA的审核。** 可用5ef原不通过→7f设计→b238窄修→cc6复审链及并行记录冲突receipt；不把COMMENT当另一个真人批准，不把限定关闭当main或整体验收通过。
3. **AI执行素材：把“完成”拆成可核事实。** stdout机器协议、run1局部真但整体失败、run2成功仍可有未触发超时缺口、语义重建与字节相同之区别，可供学生理解后自行评价。这不是新增学生原创prompt或人工改码证据。

学生可自行思考并据真实观察作答：

- 为什么cleanup完成、child exit0、业务整例通过和正式性能达标需要不同证据？
- 面对F08两个都声明的守卫，哪些选择需要人定规则，哪些只是AI可以自治修复的driver问题？
- 无完整保存旧inline命令时，语义重建能证明什么，怎样诚实表达证明范围？
- 并行日志的共同前缀/完整尾段和标量旧值保留，怎样帮助判断谁改了什么，仍有什么局限？
- 本人实际做过的是需求选择、观察、审阅还是亲自改码？哪些材料能证明，哪些还不能？

本页不代给第一人称答案。R001本人反思和R002公开provenance确认本人建议已提供，R002原文仍私密未读。最终研究正文、≥12人工修改、≥3幻觉人工识别纠正、≥5人工校正上下文映射仍无完成证据；本轮不增加已证人工计数。新AI错误/修复不充抵这些要求。

本岗只运行必要文档/hash/JSON/XML与Git阶段核对，无产品测试、基准、全CI、真实服务/DB/浏览器、Word重导或新图；未修改M6历史、产品、冻结文件、别岗报告或共享ledger。问取、来源hash、实际任务、Issue11真实沟通与GET回读分件归档。
