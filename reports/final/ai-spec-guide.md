# T44 AI可执行规格相关文件说明

本说明帮助接手者按真实版本读懂约束、运行边界和证据。应用固定bc5aef9，1.1规格14冻结文件不改；准确开发CI通过不等于最终验收。本文是AI整理的技术说明，不是学生研究正文。

## 1 文件用途和正确顺序

| 次序 | 文件 | 作用 |
| --- | --- | --- |
| 1 | AGENTS.md、岗位TASK、collaboration/team | 责任目录、实问/交接、独立测试隔离与真实性；不是业务验收结果 |
| 2 | specs/requirements.md、business-rules.md | FR/AC、用户采用的业务规则和1.1容量生命周期 |
| 3 | records/spec-freezes/v1.1.json | 父链/人的决定/限定审核及14文件hash；不以最新代码覆盖旧冻结 |
| 4 | specs/contracts/openapi.json、字段字典/DDL/持久契约 | 38操作/130 Schema、类型、错误、幂等和18业务表226字段 |
| 5 | specs/backend-design.md、实现边界、状态机/门面 | 按Call→Runtime→Business→UoW数据流编码，模块职责和事务不越界 |
| 6 | reports/reviews、公开CI/独立报告、岗位handoff | 精确SHA及范围；不能把环境ready、collect或COMMENT当通过 |
| 7 | M6函数I/O、API表、追踪、来源清单 | 当前源码、测试和报告对应关系，不改写原始事实 |

完整来源见[M6清单](../../docs/reports/M6-source-manifest.json)，[函数索引](../../docs/reports/M6-function-sources.json)、[函数契约](../../docs/reports/M6-function-contracts.md)、[接口表](../../docs/reports/M6-api-contracts.md)均绑定bc5。执行命令沿README/责任岗说明，显式选择本项目库，凭据只能由对应受控环境读取，不进普通日志/公开报告。

## 2 约束如何指导AI

需求有歧义时，先向人确认最终业务取舍；D001/D004/D005/D006是人的采用，生成实现及AI审核仍属AI。新变更须写需求和影响、设计/契约/DDL/测试，再申请新冻结，不能偷偷改14文件。普通已授权实现问题可自治修复，但不能把人力保护集合、决定权限或验收线改松。

结构预检不执行完整业务守卫；纯domain Decision不表示SQL已提交；MQ确认不表示本人收到。前端只展示真实授权记录，不能把旧身份的异步响应写进新会话。history旧理由只做当前已授权页的保守响应投影，不根据相近时间/内容猜测或修改旧审计。

## 3 质量保证和失败记录

静态、契约、覆盖率是开发门禁；本机模块、真实MySQL/HTTP、MQ、Docker、独立验收、正式性能和Word QA层次分别记录。bc5的510BE/89FE、全源行89.21%/93.33%及Docker小规模集成有准确原件；6307超限、原P95三组失败和完整独立结果未完成保留。

42243组合504绿后仍有真实HTTP evidence true误同1的反例。原失败报告/COMMENT不改，ad6先勘误、bcb窄修、bc5同反例绿只限定关闭。不可为补绿删旧用例、改独立预期或把HTTP失败归环境。开发岗和文档岗不读未发布独立cases/driver/raw/credentials，不联系tester；仅明确公开16份v2报告、v3收据/binding及新stage01两件。

## 4 提示词和人工归属

[M6提示词证据](../../docs/prompting/M6-process-checkpoint.md)核到三条反馈链合计六条有意义且实际执行的AI派工版本，满足本轮数量证据；任务书没有要求全由学生输入或必须单族六版。M4/M5用单族不足判总量未满足过严，当前显式勘误，历史不改。建议优化版和proposed模板未执行，不计used。

U001/U002原文是用户原创多岗隔离/阶段commit审核/GitHub协作亮点；AI优化建议单列。六条AI派工、AI改码和reviewer识别不计学生人工12修改、3幻觉识别或5上下文到代码证据。R001本人观点、R002课程建议已提供；R002仅公开provenance，学生最终研究仍本人组织成文。

## 5 文档和交付边界

七类当前MD与原M4/M5历史分开；M6新增三图及hash/渲染/逐张查看记录，旧8+M5三图不重复渲染。四份技术Word按本地私密封面、空日期、旧M4原样归档后另存M6，实际逐页PNG QA后才能称排版通过；没有学生研究正文。PR24仅M4已合并，本阶段另建文档draftPR，不自行APPROVE、发布success或merge main。
