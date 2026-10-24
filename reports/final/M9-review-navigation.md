# T44 审阅导航与版本截止

AI文档岗整理，固定导航截止728c4e8e273a8e1f8505db505c09168d1abe3556。本页只说明材料的位置、版本和阅读顺序，不扩展旧Word已验范围。新实际bundle尚未创建；H2尚无公开最终结论，不为导航等待或预填结果。

## 1 外层副本与源码内链接

外层审阅包的辅助Markdown是仓库原字节副本，仓库相对链接不因复制而自动改写或生效。请先展开计划包里的内层源码压缩包，进入其仓库根，再打开对应文件：`reports/final/submission-map.md`、`reports/final/M9-review-navigation.md`、`reports/final/M8-engineering-annex.md`和`reports/final/M8-performance-preparation-addendum.md`。本M9文件只在内层源码，不宣称单独附在外层。实际封包前将重取材料字节hash，当前没有新包可核验。

本机原仓库可直接使用`docs/user-guide/wake-up-review.md`入口及[五分钟导览](../../docs/guidance/M8-five-minute-tour.md)。此处相对链接以仓库树为上下文，不承诺外层单份副本可直接跳转；私密登录说明仍留本机，不复制账号到公开材料。

## 2 固定四Word共35页

| 技术Word | 页数 | 内容与出版截止 | 对应源码内MD |
| --- | ---: | --- | --- |
| requirements-review.docx | 10 | M6，应用bc5，文档ref e8998d6 | reports/final/requirements-report.md |
| design-review.docx | 14 | M6，应用bc5，文档ref e8998d6 | reports/final/design-report.md |
| ai-spec-guide-review.docx | 3 | M6，应用bc5，文档ref e8998d6 | reports/final/ai-spec-guide.md |
| test-results-review.docx | 8 | M7，文档ref a462365；bc5黑盒与6ec等价应用CI分别绑定 | reports/final/test-results-report.md |

三个M6原稿27页复用，M7只新导测试8页，hash和新旧状态见[M7交付清单](../../docs/reports/M7-deliverable-manifest.json)。M6原四稿33页及其QA保留；独立stage08核的是旧33页，不能称当前35页全由独立复核。文档AI的逐页QA只证明相应文稿排版，后发M8事实没有倒填入旧Word；本轮没有打开或重导Word。

## 3 后发材料分开阅读

- [M8工程附录](M8-engineering-annex.md)：主体1005715，dcad ready为另列后发节点；stage07/08、源码包窄修、候选池、native原失败/新360及资源观察局限有各自准确来源，ready不等4h完整结束。
- [性能准备补充](M8-performance-preparation-addendum.md)：新截止5ce98e0；原六准备退出正式NOT_RUN，H2为接触SUT后明确方法修订，新六请求只有授权，尚无最终结果。不以旧“尚未发表”字段抹掉已发表的准备摘要。
- [DB只读索引回执](../../agents/database/index-readonly/report.md)：5948公开原开发fixture的14条只读语句/普通EXPLAIN。估算和实际键存在不等真实耗时、正式根因或已实施优化。
- [BE静态下一步索引](../../agents/backend/static-performance-next-measurement.md)：d834绑定bc5/冻结DDL，静态I/O、次数及未来观测建议，没有本轮新SQL/EXPLAIN/负载；结构/读集等价不能替代准确新源运行或性能证明。

提交清单第1至4节保留M7技术快照和原当时未完成项；第5、第6节及本导航给后发入口，各守自己的截止。原失败、规模及本人研究/真实人工证据缺口不因导航、同账号COMMENT、AI问答或候选设计而通过。六prompt版本和人工12/5/3不重新计数。
