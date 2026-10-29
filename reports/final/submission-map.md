# T44 当前提交导航

当前产品源为356f29983c904e949245aedfad464efc1bf7b63d，业务契约v1.2。四技术报告已按当前版本统一组织；历史保留在原Git、附录及旧Word目录。源码5817行超上限717，新的独立云结果仍待明确发表，当前不宣称整体作业通过。学生研究正文仍须本人完成。

外层审阅包辅助Markdown是仓库原字节副本，复制不会改写相对链接。请在展开的内层源码树中使用本页及reports/final下报告；本机入口为docs/user-guide/wake-up-review.md。封包前重取材料hash，实际包状态、源及生成结果以包内manifest和外部receipt为准。

## 1 四份当前技术报告

| 提交物 | 当前正文 | 内容和边界 |
| --- | --- | --- |
| 需求规格 | [软件需求规格说明书](requirements-report.md) | 范围/角色/FR/NFR/AC、v1.2人审取舍及设计测试追踪 |
| 概要与详细设计 | [设计报告](design-report.md) | 架构/ER/事务/算法、当前row_model/page.prepare等I/O、UI及部署恢复 |
| 测试结果 | [测试结果报告](test-results-report.md) | 当前模块/CI、旧独立结果及新云结果待发表范围，不混版本计数 |
| AI可执行规格 | [规格和过程说明](ai-spec-guide.md) | 权威输入/执行约束、U001/U002原文亮点及建议/used区别、真实归属 |

新四Word输出到私密review-documents/FINAL-20261029，封面个人值不入Git、日期空；新稿均须render及逐页实际PNG QA。最终hash/页数/QA结果将在本岗公开交付manifest中登记，尚未完成的不能借旧QA宣布通过。当前源码、38API及双向映射见[来源函数索引](../../docs/reports/FINAL-20261029-source-index.json)、[接口表](../../docs/reports/FINAL-20261029-interfaces.md)、[追踪矩阵](../../docs/reports/FINAL-20261029-traceability.json)。

## 2 当前证据和待办

产品整体run40869266343已核后端796/前端89全绿，行覆盖90.232389%/93.33%，原件commit绑定另记；DB单岗40867341358成功，免费双镜像40869531724成功但不等云已部署。新的753独立结果仅在root明确发表后纳入，文档不读取其PRIVATE/代码/日志、不传开发结论。[源计数](../../records/metrics/final-candidate-20261029.PUBLIC.json)仍5817/65超717；旧性能失败与H2 INCONCLUSIVE保持。

实际APP备份、完整下载解密及隔离恢复、root最终VM释放均按新公开运行回执确定，不以工具准备或本页推定完成。整体门禁、学生最终研究及人工12修改/3幻觉/5映射的证据缺口继续保留；AI互改、同Git账号和用户同意不充抵人工配额。

## 3 历史档案

| 历史阶段 | 准确入口 | 保存方式 |
| --- | --- | --- |
| M4 | PR24合入的原技术稿28页 | 原私密M4及archive-integrity，原字节不覆盖 |
| M5 | 772895d七稿/三图 | [历史七稿索引](../../docs/reports/M6-historical-report-index.json)，不冒新Word |
| M6 | 126df四稿33页 | [M6逐页QA](../../docs/reports/M6-word-qa.json)，当时源和页数保持 |
| M7 | 1f6f376测试8页加M6三稿27页，合35页 | [M7manifest](../../docs/reports/M7-deliverable-manifest.json)及[新8页QA](../../docs/reports/M7-word-qa.json) |
| M8至M10 | 固定各截止的后发材料 | [工程附录](M8-engineering-annex.md)、[准备方法](M8-performance-preparation-addendum.md)、[旧导航](M9-review-navigation.md)、[H2交接](M10-night-test-handoff.md) |
| 20261024云C | 839公开复核 | [云C补记](cloud839-evidence-addendum.md)，不移植当时源结果 |
| 当前重整前 | 产品基356f299中的原四MD及旧导航 | Git准确历史保留；本版不改旧M4/M6/M7文件或manifest |

旧附录“当前”“尚未发表”均属于其自身截止，当前状态以本页和测试报告为入口。旧33页独立核验不能当现35页或新四稿QA。

## 4 学生本人研究材料

[AI过程索引](ai-development-report.md)提供可核事实，[研究提纲](student-study-template.md)仅是素材和待写结构。U001/U002用户原创、AI建议版和实际执行分开；已有三反馈链六个真实AI版本不再凑数。R001及R002材料已提供，R002只用provenance、不读取或发布原文。最终个人观点、课程建议组织及研究正文由学生本人撰写，封面署名不将AI操作改记为学生完成。
