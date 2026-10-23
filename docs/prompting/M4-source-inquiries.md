# M4 实际问取与回执

Prompt-Ref: ROLE-prompt_engineering-M4-REAL-PROCESS-v1；记录者：提示词岗 AI。下面均为实际 send_message 问取/收到的事实摘要；不是替其他岗生成回复。未收到表示本 checkpoint 尚无本轮回话，不表示其没有完成。没有联系独立测试，也没有启动其他岗位的新任务。

| 责任岗 | 本轮实际问题 | 当前回执 |
| --- | --- | --- |
| backend | 实发prompt、IAT01–05失败/55HTTP/479CI、MySQL总5口径、955/502/代理/Ruff事实 | 已收到；下节保留真实来源及边界 |
| database | C-P4/catalog与capacity文档/实现的真实派工、失败/修正/验证、操作者 | 已收到首次说明与最终705e提交回执 |
| frontend | f654 CI27/92.79%、02ec80HTTP、c3e证据提交、原e8独立补充与修复后验证 | 已在Issue阶段评论后、commit前收到本轮实际回复；见下节 |
| documentation | M4实发prompt、函数I/O与R001定位、四批Word失败至28页QA，仅公开来源 | pending：本次异步回复尚未收到；已读公开M4 QA/来源，未读私密Word/cover/截图 |
| guidance | R001本人思考、D005/U015和D006/U016的pending→真实采用、归属与来源 | pending：本次异步回复尚未收到；已读公开实际prompt和人决定原文 |
| reviewer | 三阶段5fb/02/bbc、成员保护AI纠错、终稿准入、C-P4限定关闭 | 已收到完整公开出处；新FREEZE-CHECK当时无结果，不预填通过 |

## backend 真实回复要点

- 当前在做v1.1合同checkpoint，未为问取运行测试；已公开实发原文 `agents/backend/PERFORMANCE-DIAGNOSTICS-v1-prompt.md`。
- IAT01首次2失败→32 HTTP/SQLite，产品 `65007a46273fb16124f08e6cf7a0cab6c051e4d6`；IAT02–05改前13失败及另8失败2通过→55HTTP/SQLite，产品 `3b6dab5b4a2f8ea62043579428fae0f383d88126`。合根源479的run39946771417为362/0skip，985专项总5=原1+新增4；公开日志/JUnit/coverage在iat01/iat02/iat05及iat02-05-ci文件。
- [IAT01评论](https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6363586113)、[后续评论](https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6363885608)、PR16；识别来自已发布独立AI结果，后端AI改码，root仅协调，不是用户亲改。
- 955首次hook错误由96e4e修router；两baseline服务退出0但bootstrap502、无fixture/样本。6529661仅工具trust_env=False和记录修正，代理仍待重试；原失败JSON和Ruff错误配置/显式正确配置输出保存于profile文件；[评论](https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6364325608)。未读私有资料或联系测试。

## database 两次真实回复要点

- 产品 `0e3e99930dcf776de1afb3509fb68cc4e2104ab0` 为数据库AI修复；实发prompt为 `ROLE-database-LIVE-VERIFY-v1.md`。review-run1的MySQL索引重建引导符问题、run2同条ALTER复用FK名1826均保留；限定lexer/ASCII处理、探针分步恢复后，真实四类变异拒绝/恢复、默认全量seed验证及7原生拒绝、18项模块回归有公开日志。不是学生修改或识别。
- [live评论](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6363453107)、PR17 draft。先前Bandit B105告警以局部token→lexeme调整，原CI也保留，不把它说成业务逻辑漏洞。
- 首次回话时capacity仅在写未提交，后续真实完稿另发：`705e7b7ce63f15b583ba1a7d943ae1e4ae8bfed1`，实发prompt `agents/database/prompts/ROLE-database-CAPACITY-V11-CONTRACTS-v1.md`；仅field-dictionary/persistence-contract文档同步与19本地链接/锚点静态核对，无本岗capacity实现或产品验证。首次错误目录定位不算产品失败；后端全量owner/项目锁/原优先级确认写入日志。
- [完稿评论](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6364775327)，PR17仍draft；旧ae60/11hash和DDL18表226列保留。D005/D006归人选择，文档及代码行为归AI。

## reviewer 真实回复要点

- 实发prompt及三次续派：`agents/reviewer/dispatches/ROLE-reviewer-CAPACITY-V11-DESIGN-v1.txt`，证据提交 `d7c46a69a219a10f914d1647786dc02338aa77df`。三报告绑定5fb、02、bbc；成员保护1–5+7由reviewer AI读真实实现纠正root AI，U016/D006才是人的capacity选择。
- bbc仅精确目标人与原owner竞争差异，RFC hash `a6271ef7f6180c29b7aa3e0bfa373b25b76fbf19f1d11233768388d495682d98`。已公开并读回的[Issue](https://github.com/HJY147/t44-dev-trace/issues/12#issuecomment-6364500677)和[PR评论](https://github.com/HJY147/t44-dev-trace/pull/21#issuecomment-6364501387)为技术准入，不是产品放行。
- C-P4限定关闭：4362e证据/0e3e999产品，原957断言不改复跑，DB四类live变异归DB，不是reviewer新跑实库或所有DDL变异保证；7c27时5886超786仍failure。新FREEZE-CHECK轻量语义复核当时刚派、尚无结果，另有实发文件待公开。

## M3 checkpoint 之后实际收到的晚到资料

旧M3问取的“尚未收到”保留为当时状态，本轮追加：documentation给出M2实际prompt、779a5d/4492016与PR22，确认M3 ROOT记录为事后重述，R001为human_reflection；reviewer给出e01首次失败e9ab/ddaa与C-P4后续4362e限定关闭；frontend给出88e/bfa/b485、原失败、83CSS和114HTTP真实链及AI归属。这些消息均发生在旧checkpoint后，不倒填为旧时点已经收到。对应公开来源已经分布在M3/M4事实材料与manifest中。

## 成稿后总协调实际新交接

收到42d3515/90e01f6/9aeb40c契约阶段、1130旧meta fixture失败、5940超限和本地guard草稿先后说明。作为cutoff后交接另附主材料末尾，未重新运行或混入原49源/旧阶段结论。正式冻结未下发/新守卫未宣称通过，AI草稿/一次草稿回归不记人或部署。

## frontend 本轮实际晚到回复（Issue阶段评论后、commit前）

实发/续派/readiness全文为 `records/prompts/ROLE-frontend-INDEPENDENT-UI-FIX-v1.md`。输入是原e8公开UI补充，识别独立tester AI、root转交、修改frontend AI；原3失败/13未选与针对修后3通过分别保留。最小产品f654，CI27/27零skip/92.79%与原ZIP digest已核；前端f654/后端02ec的1.0真80HTTP，1/1→1/0→0/0、任务state/version1/2不变，唯一受控GET abort console不称0错误。验证提交20082da2d3fdb97b9d3299cfd4f652cc64195608，追加原ZIP证据c3e84e609623eb56229ee25e7657533141527aa5。

[PR14评论](https://github.com/HJY147/t44-dev-trace/pull/14#issuecomment-6364649614)、[Issue2](https://github.com/HJY147/t44-dev-trace/issues/2#issuecomment-6364612818)、[Issue3](https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6364613456)已公开。不是独立复测；新1.1 fixture/README同步另受派工，旧1.0 CI/HTTP不倒改。原Issue11阶段评论的“另三岗pending”保留为发布当时时点，当前仅docs/guidance本轮回复pending。
