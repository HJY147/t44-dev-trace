# T44作业提交物对照表

需求/设计/AI规格保持M6的bc5快照，测试稿M7增补明确发表黑盒及6ec等价应用CI；整体门禁仍未达，不能把此表作为最终验收证书。原件只读保留，所有实际产物、操作者、版本和未完成项分别列示。

## 1 技术提交物

| 提交项 | 当前文件/证据 | 状态 |
| --- | --- | --- |
| 最终源代码/配置 | backend/t44、frontend/src及DB/MQ/扫描/部署 | 业务应用bc5与6ec包字节等价；44Py/20TSVue，6307超5100，整体未放行 |
| 需求报告 | requirements-report.md及M6-traceability | SRS范围/角色/8FR/NFR/9AC/异常和量化差距更新 |
| 概要/详细设计 | design-report.md、M6-function-contracts/API表 | 模块/状态/ER/事务/会话/理由I/O及三新图 |
| 测试结果 | test-results-report.md、composite-6ec8d3c-ci、stage04/05/06 | 510/89开发、同源Docker绿；独立25/26、浏览器6/6、粗故障4/4，正式0/3 |
| AI可执行规格 | ai-spec-guide.md、14冻结清单 | 规则/接口/DDL/读序、质量与真实归属说明 |
| AI时代研究分析 | AI过程素材、student-study-template | 最终正文须学生本人写，尚未成品 |

## 2 研究过程要求

| 要求 | 已有可用来源 | 尚缺项 |
| --- | --- | --- |
| 各阶段技术与prompt | M6-process-checkpoint、原始prompt、准确Git链 | 本人独立组织和解释 |
| 演进≥6版 | 三反馈链六个实际AI版本已核；单族要求过严已勘误 | 不计学生输入，也不自动完成AC09 |
| 原创prompt亮点 | U001/U002原话、优化建议和具体Issue/PR分别保存 | 本人选择分析，不编提效数据 |
| 人工≥12改码/≥3幻觉/≥5映射 | 当前未获本人完成证据 | 本人真实操作/判断、before-after和验证，不凑数 |
| 本人观点/课程建议 | R001已公开出处；R002仅公开provenance | 本人最终研究成文；AI不读R002原文 |
| 质量与debug | 初始设计C1–C4、会话/预检/理由真实红绿链 | 区分AI发现/修复和人的实际参与 |

## 3 Word和历史

四份技术Word为需规、概设详设、测试结果、AI规格说明，不含学生研究正文。M6最终126df的33页为需规10/设计14/测试6/AI规格3，本文档AI全部逐页original实看，root仅另看3页sample，不能记成root全看。M7只导出实质变化的测试Word到新私密M7目录，其余三稿原M6文件与hash复用、不重导；M7新测试稿8页加27页复用，共35页；页数/hash/新旧状态见[M7交付清单](../../docs/reports/M7-deliverable-manifest.json)与[逐页QA](../../docs/reports/M7-word-qa.json)。M4四稿原28页QA属于2e/0448快照；M5只有七类MD和三图，772收据不代表新Word或PR24合入。M6先保存MD/图，再将旧M4 DOCX/manifest/render PDF原样私密归档，M6另目录导出，逐页实际PNG QA；宽图按可读尺度安排。

个人封面值只来自private cover-info，日期空，原Word/QA/个人值不公开。PR24为已合并M4，本阶段独立branch/draftPR与准确head/readback另记。公开[M6来源](../../docs/reports/M6-source-manifest.json)、[历史七稿索引](../../docs/reports/M6-historical-report-index.json)和图manifest供追溯，不以排版QA替代软件通过。

## 4 最终仍须处理

6307超1207、原v1与v3正式P95三组均失败。v3功能25/26/F08优先级未决、浏览器6/6、粗故障4/4，另3功能/5精确切点阻塞及421未观察响应组合保持；白盒4/交付物4尚未有本轮可读发表结果。native旧0a6有限周期成功与新capture b238窄修/限定复审分版本，新代码无完整cycle；本机只读预览不等持续部署或独立验收。学生本人研究、真实人工材料及课程过程完成项继续明确，不编造签署/评分或人为经历。

附加可选阅读：[root整理的原始研究来源索引](https://github.com/HJY147/t44-dev-trace/blob/75d75da0bf3e1b0f3dbd7b6e09617572a96fb1fc/records/research/ai-software-engineering-primary-sources.md)。这是AI整理的四份原始摘要/机构页面索引与未作答问题，供本人自行阅读；不当本人研究正文或人工配额，跨研究耗时/任务量/2026选择效应指标不相加，也不用旧19%推断当前通用结果。

## 5 M8后发证据与旧Word截止

[工程附录](M8-engineering-annex.md)固定主体1005715，dcad只为明确后发ready小节。独立stage07/08四范围各自有限完成，整体仍NOT_ACCEPTED_INCOMPLETE；其Word核验只属M6旧33页。现行35页仍为M7测试8页加M6三稿27页，原hash/QA和需求设计规格原稿保持，本附录没有导入这些旧Word。源码绑定P2限定关闭不等新actualbundle；db87的520/89及Docker/有限审核不等root合入；62ac新360成功和后发4h ready不等完整4h或正式性能通过。v4只到新H两源各3入口授权，尚无新结果；6307超1207、旧正式失败与学生本人研究/人工12-3-5缺口保持。
