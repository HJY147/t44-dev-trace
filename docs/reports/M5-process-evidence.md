# M5 真实过程素材与学生自写索引

这是文档AI依据公开记录整理的事实索引，**不是学生本人研究正文**。生产内容截止6ba9f94；后收到公告另标。R001本人反思与R002课程建议确已收到；R002仅公开provenance和SHA，本文不读取或复述私密原文，也不推定本人已亲写骨架、断点调试、改码或独立识别幻觉。

Agent-Role documentation；Prompt-Ref ROLE-documentation-M5-REPORTS-v1；Refs #9。

## 1 课堂要求如何落实为可审材料

[U010](../../records/prompts/U010-original.md)要求研究报告记录需求怎么审、需求→设计prompt、质量/测试/debug和本人收获，并明确学生自己写；[U011](../../records/prompts/U011-original.md)要求需规/概设详设先行且持续补充，[U012](../../records/prompts/U012-original.md)要求参考正式需规、多画图。用户希望提示词岗代作本人，但AI操作者不因此成为学生。本文提供证据与提问，判断和成文由本人完成。

[R001](../../records/reflections/R001-original.md)及[归属](../../records/reflections/R001-provenance.json)是本人关于架构封装/函数I/O、需求含糊处与测试决策的真实观点；[R002来源](../../records/reflections/R002-provenance.json)确认本人课程建议已提供，原文SHA `28308134d9b8e2809bc07f621d9313160732a07f7a10afa32d003cf9b6118fae`，研究正文尚未提供。未来先由人写def/#todo骨架是建议，不倒填本项目已亲自实施。

## 2 需求审查到设计再到代码的实际链

| 实际来源/派工 | 推导和产物 | 顺序、操作者与限制 |
| --- | --- | --- |
| U001/U002及M0各岗真实派工/问取 | 固定责任岗、隔离独立测试、Issue沟通、本人commit/准确SHA审核 | 用户原创组织要求；不是业务代码已完成，也不是学生亲改 |
| backend CONTRACT-v1→v2，C1–C4首次失败 | 三类接口、请求来源、101收件人、时间域及真实可达错误设计修复 | AI审核发现/AI责任岗修复，bc0限定复审；D004用户采用后ae60冻结1.0 |
| APPLICATION/INTEGRATION实际派工 | 冻结接口/DDL→模块/门面/状态机/事务；enum码、seed metadata与故障夹具debug | 先有规范与审核，M2/M3图在开发中补充；不倒造开发前全图完成 |
| U015/D005、U016/D006 | 转派先登记capacity；1–5工时保护、6/7允许移出、返工再验；成员保护仍1–5+7 | 用户作业务选择；原root混同两种保护由reviewer AI纠正，不记学生识别 |
| [容量实现实际派工](../../agents/backend/CAPACITY-V11-IMPLEMENT-v1-prompt.md)及1.1冻结 | 42d需求、705e DB、90e API→审查→189dc14文件→4c正式实现/回归 | 早期本地guard草稿及一次草稿回归的披露保留，未把草稿称部署或后冻结首次写出 |
| [读UoW RFC](../../specs/changes/contract-validation-read-uow-rfc.md)、backend WORKLOG实际续派 | 3187设计→5dcb唯一接口单UoW，保留鉴权/在途语义/错误和独立拒绝事务 | 原只读S锁提案撤回；净增7行非减行，412全套不证明正式延迟改善 |
| [暖色实际派工](../../records/prompts/ROLE-frontend-WARM-GLASS-v1.md)、U017/U018/D007 | 官方本地OpenDesign技能/模板→326设计/原型→协调实看→840 Vue导入 | 用户定视觉方向，AI定色号/组件；本地文件模式非App/MCP/外部模型；8原型图非业务API证据 |
| [空文本实际派工](../../records/prompts/ROLE-frontend-EMPTY-VALUE-FIX-v1.md) | 736问题设计→75单组件props修复→621红绿/受影响组/真实浏览器证据 | 初始化函数本来正确，跨组件边界定位；AI发现/AI修复，不算学生亲改 |
| 本轮M5实际派工 | 从已发布规范/代码/模块/独立阶段报告整理当前技术稿、函数I/O与三新图源 | 本文是开发中过程汇编；不接触独立私密材料、不重跑业务或借图批次凑prompt六版 |

更早实际prompt、失败、Issue/PR和12条AI过程映射在[提示词岗M4事实包](../prompting/M4-real-process-evidence.md)及[来源](../prompting/M4-source-manifest.json)，按其截止解读，旧“课程建议未提供/尚未冻结”不当成M5当前状态。本轮实际问取及未送达事实见[M5收集](M5-collection.json)。

## 3 真实质量与debug事实

| 原问题或观察 | 修正/验证 | 性质和剩余边界 |
| --- | --- | --- |
| 候选Schema版本误取全局1.1 | 保留内层1.0/外层1.1，原失败/修复和CI归档；1.1.1建议撤回未创建 | AI实现/AI纠正，不是用户选择新版本 |
| 只读UoW新目标9失败 | 新断言改前4+5失败，改后11HTTP+7真MySQL并入412；4/5/5 SELECT/1acquire | 不是9个旧缺陷；连接跨本地校验CPU、总往返与P95须实测 |
| 840视觉关闭按钮越界 | 主题优先级与内部滚动修复，18实界面图/40HTTP；原失败保留 | 产品样式问题；隐藏背景选择器和截帧另属工具局限 |
| FE-INIT-01文本true | 纯initial通过但真实props失败；Boolean-before-String强转，显式JSON props修；同组2fail→6pass，受影响14/20HTTP/4图 | 产品组件边界问题；75当轮无coverage，84092.81%不冒充新源码覆盖率 |
| demo登录502 | 同源演示进程恢复后再测；未进入表单的首次结果不算通过 | 环境阻塞，不是修复逻辑失败 |
| frontend-only快照遗漏冻结JSON | 漏文件500；补齐仍500；重启/新cache/明确fs范围组合后200；shell误续检查保留 | 环境/AI过程失误；未单变量证明负缓存为原因，不称产品源码bug或学生识别 |
| Linux pause恢复unhealthy | 逐次false原回执保留，后有界健康观察及依赖顺序修正，f118能力成功 | harness=false，非产品故障通过；独立后续公告另归属 |
| DB去重/AST候选收益不足 | scan-run候选净增1、AST原型46/1且无明确收益，均未投产 | 生产节省0；不能以估算充抵6051超951 |

## 4 分阶段质量和可测证据

需求层审角色/数据域/前后置/成功拒绝/可达性；设计层核API/DDL/状态/锁序和调用方；编码层用真实I/O、门面DI与冻结运行副本；模块层分别记录纯域、SQLite/mock、真MySQL、HTTP、MQ和进程；组合CI覆盖全生产源码且不排低覆盖文件；审核绑定精确SHA；无历史独立实例只收中性资料、先冻结再测；性能和规模独立保留失败线。任何一层通过不代替下一层。

当前准确数字见[测试报告](../../reports/final/test-results-report.md)。5dcb412与独立4c API/故障子集、840视觉27和75定向14不混总数；6ba组合CI后来30前端另列新证据。独立v1旧P95失败不被查询减少或新CI绿覆盖。新图/函数索引是AI据代码补充，非本人开发前已写骨架。

## 5 学生本人仍须完成的部分

- 本人选取真正理解的事实，写需求如何审、为何接受/否决方案、如何依据测试作决定及个人收获；若只观察AI过程，明确写观察。
- R001和R002都是本人贡献，课程建议已提供；最终研究正文仍由本人组织，AI不把它润写成署名成品。
- 单族六版真实演进尚未核实；学生亲改12、本人识别3、人工校正映射5的可证实数量仍不由现有AI活动证明达标。角色分工、被审SHA、工具重试、Word或图迭代都不自动计prompt版本。
- U001/U002原创亮点有真实Issue/commit/PR链，可分析其作用和成本；无对照测量不写提效百分比，也不声称已彻底杜绝上下文污染。

可填写[学生自写模板](../../reports/final/student-study-template.md)。本索引不提供代签名的第一人称研究结论，不复制R002私密原话。
