# R29 学生本人自写研究：事实素材索引

本页是AI整理的事实和来源，不是“胡锦洋研究报告”正文，也不供换署名提交。本人应阅读原证据、选择确实理解的案例，再独立组织观点；不把AI写的方案、操作、错误和修复改成“我亲手完成”。工程当前状态见[R29 checkpoint](../../reports/final/engineering-checkpoint-r29-20261029.md)。

## R29B 可核追加（新CI成功，其他门仍未闭合）

- 两个真实局部去重已集成到源码`0bffe0c535e5897890aebf30879fdd3839dc52d6`：后端query helper净减3、模块152通过；数据库catalog有序注册净减4、模块133通过/43未选；审核自有72检查无新增P1/P2，均是AI实际工作，不算本人亲改。见[工程补记](../../reports/final/engineering-checkpoint-r29-20261029.md)。
- 当前[已跟踪固定计数](../../tmp/768_integration_r29/source-count-r29b.json)为5880/65文件、仍超780。可由本人分析“实际微收益为什么没有闭合整体目标”，不能写规模已通过。
- [新CI40827655008摘要](../../records/ci/r29b-0bffe0c5-40827655008/summary.PUBLIC.json)已四job成功：原后端796、前端89，行2502/2773=90.2271908%，分支713/848=84.0801887%。原CI发现目录不含tmp765/766的新本地项，不把152/133加进796；新旧CI独立记录，旧f7云P95/NP不转挂新源。
- [QA v2.3正式PUBLIC](../../records/qa-tool/r29b/LOCAL_V2_3_SELFTEST_RESULT.json)为本地模拟HTTPS：400客户60+600秒运行段有记录，但后置只114/400快照、100审计，286预算未观察；实际5/15误配而要求15/40，整体NP。正确预算有限后置回归及全新完整运行仍待，不拼接片段。SUT/cloud0只描述本地模拟，Darwin未执行Linux正式cgroup守卫，拟4CPU免费Actions工具子集不等正式8CPU环境；本人只能将它作为工具质量过程素材。
- [原CI日志格式回执](../../records/ci/r29b-0bffe0c5-40827655008/diff-check-scope.PUBLIC.json)保留真实ANSI尾空格导致全量diff-check exit2及root首次回执脚本终止符错误；限定其他源码/metadata检查0不等整包clean，均属AI过程而非本人亲自debug。

## 可供本人选择的六组材料

| 研究方面 | 公开材料与可核事实 | 本人需要独立回答的问题 |
| --- | --- | --- |
| AI时代对开发的影响 | [协作岗位规则](../collaboration/team.md)、[本轮四岗交付](../../reports/final/engineering-checkpoint-r29-20261029.md)：分岗、独立worktree和SHA交接实际存在，但AI仍发生schema误读和导入问题 | 哪些判断不能交给岗位的“已完成”声明？共享文件系统的流程隔离有什么局限？只写本人观察，不能称物理隔离 |
| 需求、设计与代码 | [v1.2清单](../../records/spec-freezes/v1.2.json)保留v1/v1.1父链；D005/6/8来自明确用户采用；[追溯表](../../reports/final/engineering-checkpoint-r29-20261029.md)连接实现和证据 | 选择一条真正读懂的FR：原文的歧义由谁判断？输入、拒绝路径和数据保护怎样落实？不要把冻结等同于实现或验收 |
| 质量保证与真实调试 | [R29公开过程](../../reports/final/performance-r29-20261029.md)：资源归属首次拒绝、误读回执schema、`-I`导入两次失败都保留；离线检查未覆盖Linux整链 | 模块自测为何仍漏环境链问题？如何区分工具错误、环境故障和产品缺陷？本轮发现与修正者是AI，不是本人独立识别 |
| 协作与取舍 | [DB报告](../../agents/database/scale-r29/report.md)实减11仍超787；[前端报告](https://github.com/HJY147/t44-dev-trace/blob/6aed8b2464aad903f43abac94ac3850e55f7bee0/agents/frontend/scale-r29/REPORT.md)增4未集成；[缓存报告](https://github.com/HJY147/t44-dev-trace/blob/753f1bff71114dab6fb580936f1ed51f08e7c857/agents/backend/scale-20261029/report.md)增26且微收益不足 | “抽象得更多”为什么未必减规模？如何在准确净收益、语义风险和验证成本间作判断？没有证据的整体重写不能写成已解决 |
| 提示词与本人亮点 | [U001原文](../../records/prompts/U001-original.md)、[U002原文](../../records/prompts/U002-original.md)、[本轮文档派工](../../records/prompts/ROLE-documentation-R29-CHECKPOINT-20261029-v1.md)分别标明用户和AI操作者；优化稿另存 | 本人的真实要求如何改变流程？哪些建议确实执行、哪些只被提出？不同岗位和新归档prompt不自动算同一prompt演进 |
| 结果判断与课程建议 | [CI摘要](../../records/ci/r29-7b15f893-40821621806/summary.PUBLIC.json)绿；[短测](../../records/cloud/f7-r29-window-20261029/short-summary.PUBLIC.json)P95超标；[独立PUBLIC](../../records/cloud/f7-r29-window-20261029/QA772-PUBLIC/qa772-final-scope.json)NP；[停机回执](../../records/cloud/f7-r29-window-20261029/stop-and-continuation.PUBLIC.json)保盘停机 | 为什么CI、短测、独立验收、传输闭合和停机要分别判断？结合本人学习过程提出建议，不用AI补写个人感想 |

## 可引用的准确数值和归属

- 云上短测仅属于旧 `f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f`。400组任务查询P95 456.946701ms、流转617.347266ms、契约校验343.225717ms、升级接口635.948648ms；正式三目标均超过270ms。约5.26秒不能写成10分钟；202不能写成已投递。
- 独立 `r29qa772-01` 只有76字节证据头、没有runtime结果，公开状态 `NP_NO_RUNTIME_RESULT`。不能写SUT请求为0、业务失败、完整600秒覆盖或“独立验收通过”。collector自身0调用不是整个测试器请求量。
- 新源码 `7b15f8932b78e99a2b3daef2411f2cefeab98463` 的CI后端796、前端89通过；契约183/集成102/故障19是重叠子套，不累加。行覆盖2500/2771=90.2201%，分支713/848=84.0802%。旧f7的云结果不属于这个新source。
- 当前5887有效行、65应用文件，仍超5100上限787行。11行DB简化有实际代码与验证，不能说规模已达标，也不把未集成候选算已交付收益。
- APP/LOAD资源尾段19,661,075字节和SHA一致是传输证据；两VMStopped/StopCharging、自动释放“-”是保盘停机证据。它们均不替代性能验收；最终账单未核验，不写精确总费用或全账号零费用。
- 用户“已恢复”只表示浏览器恢复。具体prep/pressure/test grant由AI总协调在既有授权内签发；AI调度、审核、脚本修复不是学生手写、逐行审码或亲自debug。QA v2截止时仅本地测试器修复pending，未新测项目或云。

## 本人写作与真实性仍须完成的部分

| 待完成项 | 所需真实材料 | 本轮状态 |
| --- | --- | --- |
| 本人实际参与范围 | 本人真实决定、阅读和操作，时间及出处 | 由本人核对和写明；不从AI日志反推本人经历 |
| 人工改码至少12条 | 本人before/after、理由、文件/提交、验证 | 当前公开记录未证明数量完成；不把AI改码计入 |
| 人工识别并纠正幻觉至少3条 | 本人如何发现、如何核实、如何纠正的原证据 | AI reviewer或其他AI发现不能改名计入 |
| 至少5处上下文到最终代码对应 | 真实输入、本人校正、最终准确代码及验证 | 需本人选择并完成真实对应，不造synthetic经历 |
| 本人观点、亮点分析、课程建议 | 本人独立文字及可引用来源 | 尚需本人组织成文；已有个人原文不由本岗读取私件或代改 |
| 最终研究报告 | 本人连贯论证、引用、准确归属和审阅署名 | 尚未完成；本页和[既有提纲](../../reports/final/student-study-template.md)只是选材入口 |

本人可以分析“没有达标”的事实及其原因证据；不能把未证根因写成结论，也不能把计划、模拟、重试、CI或封存说成最终通过。这里不新增人工配额、不宣称新增六轮提示词演进、不填写个人封面或署名。
