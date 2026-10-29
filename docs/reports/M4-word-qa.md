# M4 技术审阅 Word 逐页检查记录

Agent-Role documentation；Prompt-Ref ROLE-documentation-M4-TESTS-AND-WORD-v1；Refs #9。

四份 Word 沿用项目自己的 Markdown 与 M3 八图。内容主基线为 2e0481f，开发 CI/同版容器证据为 0448fec，公开文档链接锁 746b5b8。后续 362 测试、容量 v1.1 变更和性能诊断均不冒称已纳入这四份。它们供学生审阅技术结果，**不是软件最终验收通过，也不是学生研究报告**。

| 私密文件 | 最终页数 | 本岗实际查看 |
| --- | ---: | --- |
| requirements-review.docx | 10 | 逐页原 PNG，含原封面 |
| design-review.docx | 9 | 逐页原 PNG，含原封面 |
| test-results-review.docx | 6 | 逐页原 PNG，含原封面 |
| ai-spec-guide-review.docx | 3 | 逐页原 PNG，含原封面 |

create/4/docx marker 在首次 author 前成功一次；迭代未重复调用。bundled Python 和指定 bundled LO 经技能 render_docx.py 生成 140 DPI 页面；最终 qa-v4 共 28 页全部以 original detail 打开查看。核对原封面字段字体/换行、中文、无蓝线黑色 Title、八图与图注完整、表格整行/重复表头、页码页眉、正文无重叠裁切，日期空。结果为技术审阅材料排版通过。

首轮 bundled LO 未发现中文字体且 Title 继承蓝边框；以私密 FONTCONFIG_FILE 发现系统 Songti SC，统一 ascii/hAnsi/eastAsia 字体并移除 style 边框。第二轮发现网格导致行距和表格尾词拆页；加入显式行距及每行 cantSplit。第三轮显式行距误裁 inline 图；图片段落改自动行高后重新渲染最终版本。原失败图片/中间 PDF 只保留私密目录，没有删除或伪称首轮通过。FONTCONFIG_FILE 的覆盖机制见 [Fontconfig 官方用户文档](https://fontconfig.pages.freedesktop.org/fontconfig/fontconfig-user.html)。未改用户全局字体或调用桌面 LO。

输出位于根 .submission-private/review-documents，DOCX 0600、目录 0700、Git 忽略；逐页 PNG/PDF 留私密 qa-v4。公开 JSON 仅列页数、源/输出/页面 hash 与检查结论，不含姓名学号或封面截图。学生研究正文未代写；R001 只作本人观点来源，不计人工改码或识别幻觉。

截止稿保留最终验收未通过：独立 v1 针对 e8ceefe，900 严格结果 340/183/328/49；183 含歧义，不当成183个bug。三批正式 P95 失败、吞吐及稳态零失败通过；C-P4 限定关闭而 5886 行超上限仍 failure。开发修复不能替代独立复测。本轮未运行产品测试、构建、业务请求或负载，未联系独立测试或跟随私有证据路径。
