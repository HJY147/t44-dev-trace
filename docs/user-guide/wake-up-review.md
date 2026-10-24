# 醒来后查看项目

应用和技术材料已经能审阅，作业尚未全部达标。先体验界面，再看报告与缺项；不需要先理解整个后端。

用户返回后已确定11月28日截止，D008发布提示顺序已采用并另行完成[1.2规格冻结](../../records/spec-freezes/v1.2.json)，随后实现、11项新目标和4项旧邻接通过、准确代码限定审核完成，最新开发CI后端522/前端89通过。[开发集成准入](../../records/decisions/D008-development-admission.json)仅对应C0dfb的新范围，不能取消旧F08或放行main。免费[857短stub校准已通过](../../reports/acceptance/v5-calibration-857-public-summary.md)，非产品或600秒性能。计划本人购买阿里云时看[选购清单](aliyun-performance-machine-checklist.md)，不要把旧AWS报价当阿里云价格。最新问题集中在[返回简报](../reviews/return-decision-brief-20261024.md)。下列09:20段落和固定Word是历史快照，不能用于证明新1.2实现。

2026年10月24日09:20（北京时间）历史收尾快照：当时候选C为`b66fa36a317145afec350d7f61ca374959b2eaf7`。相对bc5应用只在依赖查询增加可信`project_id`条件，限定等价范围已有[18b0271审核及准确PR42 COMMENT](https://github.com/HJY147/t44-dev-trace/pull/42#pullrequestreview-5636066453)。完整[CI40047832510](https://github.com/HJY147/t44-dev-trace/actions/runs/40047832510)和[Docker40047836840](https://github.com/HJY147/t44-dev-trace/actions/runs/40047836840)均绿，后端510项、前端89项。root已按事前dde39门槛决定准入开发集成，最终以`records/decisions/dependency-query-development-admission.json`收据为准；连接池db87不合入。这里不是性能改善证明或main放行。

**运行演示固定bc5，四份Word保留各自M6/M7截止，不是C的同源运行/文档验证。** 本岗没有重启、延长或重新测试入口。

## 先打开界面

完整本机演示 <http://127.0.0.1:5178> 已按北京时间2026年10月24日11:49:43的原截止自然结束，随后约4.11秒清理；现在不能登录这个入口。准确bc5演示的driver/post实际退出0，89个登记进程退出、本run端口释放，九受保护监听元数据与基线一致。[最终只读封档](../../agents/deployment/demo-natural-close-report.md)区分实际观察和未测范围；没有续期或重启，不把四小时生命周期成功当正式性能通过。原私密登录说明保留历史，不用于声称当前就绪。

另保留 <http://127.0.0.1:5173> 较大合成记录预览，也为准确bc5米咖玻璃界面，仅运行API和网页；使用另一份`.submission-private/演示登录说明.md`的账号。两入口数据和身份独立，账号未放到GitHub。连接池db87未合入，不把它说成这两个入口已采用。

可以先登录、选择项目、查看任务详情和审计历史。里面是明确标注的合成数据。你之后亲自做了什么，应另按实际时间记录；下述材料不把AI的浏览器操作记成你的验收。

## 再看四份技术报告

Word都在本机`.submission-private/review-documents`，含你提供的私密封面，报告日期保持空白。测试稿采用M7，其余三稿复用M6：

| 内容 | 本机相对位置 | 页数 |
| --- | --- | ---: |
| 需求报告 | M6/requirements-review.docx | 10 |
| 概要和详细设计 | M6/design-review.docx | 14 |
| 测试结果 | M7/test-results-review.docx | 8 |
| AI可执行规格说明 | M6/ai-spec-guide-review.docx | 3 |

共35页，文档岗已逐页检查对应最终排版。三份M6稿中的运行状态只代表各自内容截止，不能把其中“v3尚未发表”当作现在的状态；后发表的核查、部署与性能方法变化见[M8工程附录](../../reports/final/M8-engineering-annex.md)和[准备阶段补记](../../reports/final/M8-performance-preparation-addendum.md)。它们是AI编制的技术材料；技术报告排版完成不等于软件验收通过。源码审阅包和后续合并审阅包也只作为审阅快照，不自动变成最终提交。

本次审阅包已实际生成：本机`.submission-private/coursework-review-bundles/T44-coursework-review-M7-4833be05807d.zip`，绑定源码`4833be05807df5a9d43176eb2ec5a610c7ac06b1`，共18个外层成员、四份固定Word及3745个内层源码文件。准确SHA和缺项以`records/validation/coursework-review-final.json`为准，实际重新打开/CRC/成员与Git核验见`records/validation/coursework-review-final-postcheck.json`。它是本机私密审阅包，未上传GitHub，不是最终提交或整体验收通过。

先按[五分钟导览](../guidance/M8-five-minute-tour.md)查看界面，再看[提交物对照](../../reports/final/submission-map.md)；需要追函数和事务时，再读[M6代码导读](../guidance/M6-learner-guide.md)。概设回答模块怎么分，详设回答接口和函数收什么、返回什么，测试报告回答究竟检查了什么及哪里还未通过。

## 查看真实开发过程

完整产品在[集成分支](https://github.com/HJY147/t44-dev-trace/tree/codex/integration)和[draft PR21](https://github.com/HJY147/t44-dev-trace/pull/21)，main目前仍是受保护的基础版本。仓库首页的项目链接现指向集成分支。若之后重新获取源码，需选择`codex/integration`；默认main不能代表本轮完整应用，审阅ZIP则绑定自己的准确commit。

优先看你原创的[多岗位分工prompt](../../records/prompts/U001-original.md)和[GitHub留痕prompt](../../records/prompts/U002-original.md)，再看[六个实际演进版本](../prompting/M6-process-checkpoint.md)和[夜间调试过程](../prompting/M7-night-process-evidence.md)。原文、AI优化建议、实际使用和反馈分开保存。多agent都是AI，独立测试采用上下文与流程隔离，共享电脑没有操作系统级隔离。

有代表性的质量过程包括：开发测试绿色后审核仍找出迟到响应错误；历史证据把布尔true和数字1误等；部署子命令超时后最终exit0曾被误记成功。每条都有原失败、设计修订、窄修和限定复审，不能把这些AI发现写成你本人发现。

## 尚需处理的事

三组正式压力测试完整执行400活动VU、600秒稳态，P95为9512.069/3086.148/8272.364ms，均超过270ms；组内失败1021/0/2，原因尚未确定。短时开发样本没有复现503，也不能覆盖这些失败。[原独立结论](../../reports/independent-v3/stage06-formal-blackbox.md)保持不变。

固定口径新C有效代码6310行（原6307+本次修复3），超过5100上限1210。尚无可信的千行等价删重方案；不能压行、移计量目录或自行宣布老师放宽要求。

F08在旧规格下同时触发“旧批准失效”和“评估基线过期”，原资料未约定先提示哪个。用户返回后已采用先更新评估、再完成原独立评审和经理决定的顺序，记录于D008；1.2新冻结先于新实现，新C已有开发测试及限定代码审。原F08失败与未到达的后续语句继续保留，不追改为通过。新独立854仅封存77概念用例，执行0，不冒充独立复验通过。v3白盒/交付物已按明确发表摘要完成有限核查，整体仍NOT_ACCEPTED_INCOMPLETE。

后发H2六次均exit1，环境最终恢复为5次true、1次false；数据准备和600秒调度不等于有效400并发已成立。SUT性能结论为INCONCLUSIVE，不给bc5/db87排名，也不撤销原v3失败。新公开Pcal=`b69ac5e`的独立stub校准中，400用户即时响应场景仍有客户端循环延迟和超时；它只证明该本机隔离测试路径能出现这些现象，不能归因原CI或SUT，不能补成H2有效测量。没有补跑。

后发技术阅读从[M10夜间测试交接](../../reports/final/M10-night-test-handoff.md)、[M11质量与测试限制](../prompting/M11-quality-and-test-limits.md)及[M12最终源码与测量附注](../../reports/final/M12-final-source-and-measurement-note.md)进入；Pcal的[公开摘要](../../reports/acceptance/v4-driver-calibration-public-summary.md)与[JSON](../../records/acceptance/v4-driver-calibration-public-summary.json)只用于理解限制，不代表产品性能通过。各文稿保留自己的截止：M10中的待CI/未校准属于旧时点，后发变化看M11/M12及root准入收据。

最终研究报告须你本人组织和写作。已有[你本人的反思原话](../../records/reflections/R001-original.md)、课程建议原话的私密原件和公开出处，以及AI过程素材与未作答提纲。当前没有证明老师要求的12处人工修改对比、5处人工上下文到代码映射、3条由人识别纠正幻觉已完成；同意方案、AI互审或Git账号名都不能代替这些实际记录。

这页是AI提供的查看指引，不是你的研究报告或亲历总结。后续应保留你真实阅读、选择、修改与测试的过程，不能倒造睡眠期间的人为参与。
