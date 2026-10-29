# T44 AI开发过程事实索引

本页为学生本人研究提供可核过程入口，不是学生最终研究正文。当前技术报告固定产品源356f29983c904e949245aedfad464efc1bf7b63d，旧阶段按准确版本保留；AI设计、实现、调试和审核不改记学生亲自操作。

## 1 用户原创亮点

U001原文提出多岗位、无开发上下文的测试、每岗代码对接和过程记录；U002原文提出各岗阶段commit、GitHub跨岗沟通及专门审核。原件分别为[U001](../../records/prompts/U001-original.md)和[U002](../../records/prompts/U002-original.md)，AI建议版[U001-O1](../../records/prompts/U001-optimized.md)、[U002-O1](../../records/prompts/U002-optimized.md)单列，仍是proposed，不能冒充实际发送。当前[AI规格说明](ai-spec-guide.md)第4节逐项列出原文选段、建议和已执行/未执行状态。

## 2 真实过程链

| 过程 | 公开入口 | 解释边界 |
| --- | --- | --- |
| 人的业务选择和冻结 | D001/D004、D005/D006、U021/D008及v1至v1.2manifest | 人采用规则，AI实现；旧失败不因新规则撤回 |
| 六个实际prompt版本 | [M6过程](../../docs/prompting/M6-process-checkpoint.md)、[版本映射](../../docs/prompting/M6-prompt-version-map.json) | 三反馈链六版皆实际AI派工，不重新凑数，不计学生人工 |
| 会话与理由质量链 | M6过程及当前设计/测试报告，原42243与bc5限定复审 | CI绿仍可漏生命周期或类型语义，窄关闭不等整体通过 |
| 测试工具也需检验 | [H2公开交接](M10-night-test-handoff.md) | 发压/oracle/ACK/聚合局限导致INCONCLUSIVE，不倒推旧结果 |
| 当前后端复用 | [actual prompt](../../agents/backend/final-20261029/prompt.md)、[差分](../../agents/backend/final-20261029/differential-identity-green.xml) | 动态schema语境、对象身份、错误上限和批读仍须差分，不外推CPU样本 |
| 当前DB和前端 | [DB报告](../../agents/database/final-20261029/report.md)、[FE报告](../../agents/frontend/final-20261029/REPORT.md) | AST/夹具/Bandit和computed-style失败分别保留，图片相同不覆盖失败 |
| 当前文档收尾 | [先行设计](../../docs/reports/FINAL-20261029-design-checkpoint.md)、实际prompt和本岗日志 | 四岗实问、准确源与新Word逐页QA，旧档案不覆盖 |

## 3 本人仍须完成

R001反思和R002课程建议已提供，R002仅用公开provenance，原文不读或公开。学生本人最终组织技术选择、质量、协作、踩坑、任务书第12节、个人亮点和课程建议。当前没有完成学生亲改12条、亲识别纠正幻觉3条、人工校正映射5处的可核证据；AI互改、用户同意、Git账号或本页不充抵。可用[研究提纲](student-study-template.md)自行组织，不把提纲当成品。

## 4 当前工程出口

准确356f开发CI后端796/前端89全绿，行覆盖90.232389%/93.33%，规模5817仍超717。新独立功能/正式云结果等待root明确发表；镜像成功不等云部署、备份和删除完成。当前入口和短历史表见[提交导航](submission-map.md)，旧M4/M6/M7 Word及原QA/manifest原字节保留。
