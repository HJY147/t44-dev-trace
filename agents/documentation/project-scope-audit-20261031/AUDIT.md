# T44提交范围与十一岗文档审计

2026-10-31，documentation AI。仅离线文件审计，未修改产品、原始材料、测试或历史报告，未访问服务器。用户确认服务器已关闭。本报告不是最终验收证书。

## 原题与边界

题目为“中小软件外包团队研发流程留痕与上线评估管理系统”。核心为交付任务阻塞、延期与回滚的状态闭环，以及接口契约、字段/DDL评审、代码评审、依赖排期、上线风险/回滚、定时升级与幂等MQ。前后端分离单体、单机数据库和本题中间件；不做微服务拆分/集群编排或多地域。性能只是其中一个非功能门槛，CPU满载不是题目验收指标。

原任务书SHA d772bde097e77082f433c5bbb1bca5ab154fbb0316a5555c211cb532488b0177；提交注意事项SHA c688f2a25c8a1c73803e7e958e8c50681a0484ef1f34a679fa8b100ce2d64f32。原文仅在受限runtime语义摘取；不公开整份第三方材料。

## 提交物与实际状态

| 必须覆盖内容 | 当前可核证据 | 结论与遗漏 |
|---|---|---|
| 最终代码，前端/后端/数据存储及中间件 | source90b734f6，frontend/src、backend/t44、规格/部署；docs-final90b的FINAL90b-source-count.json、core-runtime-groups.json | 产品与工程材料存在，不等最终放行。全固定口径65文件5818行，超5100上限718；用户采用62文件核心5038，辅助3文件780单列，不等老师批准排除 |
| 需求报告 | reports/final/requirements-report.md、冻结v1.2及追踪 | 有稿，须将最终当前结果与版本统一；不能将文档存在当FR全部独立通过 |
| 设计报告 | reports/final/design-report.md、architecture.md、接口/字段/DDL/状态表/伪代码/图与traceability | 有稿；最终提交核题目要求的至少2组技术选型比较、八段评审/十项清单证据、复杂度、可维护性改动预算，不能仅交架构图 |
| 测试结果文档与原始数据/复现命令 | 最新冻结p13 FINAL_CONCLUSION.PUBLIC，source90b官方CI及reports/reviews/90b734f6-ci-evidence.md | CI后端797/前端89绿、行覆盖90.23%/93.33%可证；独立完整验收未成立。p13 NP_NOT_ACCEPTED，四P95约1011–1096ms，后置/原raw完整性门禁不足；备份75文件hash绿不等内部原raw完整或AC08通过 |
| AI可执行规格及说明 | AGENTS.md、docs/collaboration、冻结需求/接口/DDL、reports/final/ai-spec-guide.md | 文件存在；须解释各阶段如何实际约束AI，并连到最终source，不能把AI规格仅理解为prompt名单 |
| AI时代研究分析与每人总结内容 | ai-development-report.md是AI事实素材；student-study-template.md为未填提纲；R001/R002各自provenance | 最终本人正文未证实完成。应覆盖AI影响、各阶段质量手段、协作/真实坑、题目第12条、个人亮点、课程建议。原材料未明确必须拆成两份文件，可合并呈现但内容不能遗漏；不得由AI素材换署名冒本人总结 |
| AI留痕 | records/prompts、reflections、决策/规范变更 | 旧材料称三链六实际版本已核，但不能把不同角色标签凑成演进。至少12真实人工修改对照、3人工识别纠正幻觉、5上下文到最终代码及人工校正映射，最新文档仍未获本人完成证据；AI修改/AI reviewer发现不得冒人工 |
| 最终可提交包 | 历史coursework-review-final回执和私密Word目录 | 现有审阅包是历史快照，未验证为包含当前source90b+p13结论的统一最终包。不得把历史CRC/封包QA或旧main放行套到现状 |

## Word截止与当前导航漂移

最新documentation分支codex/docs-final90b，head66cb2b20；模块报告记四技术Word13/15/5/5页，共38页。本次重新核四Word全部存在且精确SHA等于docs/reports/FINAL90b-deliverable-manifest.json。但当前四份MD源码SHA均不等于该manifest的source_sha256，另逐项git show复核manifest所记documentation_ref，四份历史来源blob均准确匹配source_sha256：历史绑定有效，不是manifest造假或输出损坏。当前只能证明该历史Word截止与原字节完整，不能称已与当前MD同步。最新模块说明仍停P07性能准备截止；p12/p13后发结果须另版增补/重导受影响稿并新QA，不能回写旧快照。

coordinator当前reports/final/submission-map.md仍夹有M6/M7旧35页、6307等历史截止，它们本身明确为历史。问题在缺乏一份当前统一入口，而非应删除历史失败。后续需新版本导航列出每份报告截止、source SHA、最新独立结论、Word来源与最终包manifest。

## 十一固定岗

- frontend：页面、交互、错误提示与前端验证。
- backend：鉴权、项目权限、状态机、评审上线、事务。
- database：字段/DDL/迁移/约束/索引/数据生成。
- messaging：MQ投递消费、幂等、降级、站内通知。
- scheduler：规则、超期扫描、幂等、重启续扫。
- deployment：打包启动、资源环境、备份恢复、工程门禁。
- testing：隔离独立功能/安全/故障/并发/性能验收。
- documentation：收集真实资料，汇总各提交报告与当前导航。
- guidance：用户问题、操作教程、真实选择记录。
- prompt_engineering：原始提示、真实演进、上下文到产物映射。
- reviewer：按精确commit审核实现/证据/门禁。

十一岗在本审计基线各有TASK、WORKLOG、模块报告和handoff四件；测试内部仅检查存在，未读内容。这只是责任档案齐备，不表示十一岗已完成。多个通用handoff明显滞后：backend仍2026-10-25阶段、scheduler仍2026-10-23，deployment旧handoff称未跑云而后续已实际多轮。最新专项分支已前进，故总协调应建立当前跨岗总索引，不将旧通用文件直接当最新状态。

各岗接口不得漏：frontend↔backend契约、backend↔database事务/字段、messaging↔scheduler真实MQ/幂等/故障、deployment↔各模块备份恢复与工程门禁；testing只经协调交PUBLIC缺陷/结论；documentation只汇总具名冻结证据；guidance登记真实用户选择；prompt岗保持真实原文与迭代；reviewer按精确commit审核。当前重点应回归FR/AC逐项闭环和提交材料完成，而非单独追CPU占用。

## 下一步文档责任

先新建当前提交总索引/FR与AC证据矩阵，标清代码规模、独立功能、性能/原raw门禁、本人研究/人工留痕缺口；在最终决定前保持未通过状态。集中同步四技术MD和当前Word，再核最终源码及包的准确版本/链接/敏感资料排除。本文不修产品、不替人写经历、不扩展云测。
