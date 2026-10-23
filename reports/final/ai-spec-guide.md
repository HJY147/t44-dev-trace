# T44 AI可执行规格相关文件说明

版本：M4技术审阅说明，非最终验收。D001/D004已由用户采用，总协调ae60dc37冻结1.0.0；M1时Q002待定是历史事实，当前不再待采用。公开稿不含私密封面值，日期留空。

Agent-Role: documentation
Prompt-Ref: ROLE-documentation-M4-TESTS-AND-WORD-v1

## 文件用途与读序

| 文件 | 约束作用 | 正确使用 |
| --- | --- | --- |
| [AGENTS](../../AGENTS.md) | 岗位/可写目录、真实记录、隔离测试和版本协作 | 先读本次授权及岗位任务；不把组织规则代替业务规格 |
| [implementation-layout](../../docs/collaboration/implementation-layout.md) | t44包、门面/进程、依赖锁责任与目录 | 只改本岗，跨岗接口由责任岗确认修改 |
| [requirements](../../specs/requirements.md)和[SRS](requirements-report.md) | FR/AC、角色/成功拒绝路径、量化要求 | SRS开发中持续优化，不倒填早期全量成稿 |
| [business-rules](../../specs/business-rules.md)、D001/D004 | 人采用的状态、延期、字段与错误取舍 | 人采用不是亲改代码；实际交付/回滚仍需经理决定 |
| [OpenAPI](../../specs/contracts/openapi.json)/[错误说明](../../specs/contracts/README.md) | 38操作输入输出/错误/幂等/时间域 | 使用冻结1.0.0；真实HTTP测试不能由Schema静态通过替代 |
| [字典](../../specs/database/field-dictionary.md)/[DDL](../../specs/database/schema.sql) | 18表226列、类型/约束/索引 | 迁移有明确目标；不关FK/CHECK、不启动偷建表 |
| [持久契约](../../specs/database/persistence-contract.md) | 版本、锁、成功/拒绝事务、outbox/续扫 | 与真实UoW/Rows/Outbox/Scan实现和本模块测试对应 |
| [后端设计](../../specs/backend-design.md)/[M2概设详设](design-report.md) | 模块、状态、数据、时序和复杂度 | 冻结文件不由文档岗改；M2说明实际实现与残余风险 |
| [review-template](../../backend/t44/resources/review-template.json)/[escalation-rules](../../backend/t44/resources/escalation-rules.json) | 已存在的v1真实配置，八段十项与三级规则 | 读取实际原文/hash/版本；synthetic metadata不是新的人的批准 |
| [评审协议](../../docs/reviews/review-protocol.md) | 八段十项、准确SHA、缺证据不放行 | 新head重新审核；技术复审不替产品/性能验收 |

先读原始T44与用户决定，再读冻结记录和跨模块接口/字段，随后读本岗实际代码与已发布交接；每次派工列出输入版本、目录、输出和验证。需求到概设、详设、实现、本模块测试映射见[M2追踪](../../docs/reports/M2-traceability.md)。

## 变更、审核与冻结

冻结11文件哈希见[1.0.0记录](../../records/spec-freezes/v1.json)。M2不改这些文件。新业务/字段/规则变化须记录原值、新值、生效时间、影响和决定者，责任岗同步契约/调用方/DDL及测试，总协调组织准确新SHA审核和版本更新；不能为让代码通过暗改旧要求。

冻结前禁止联调；本项目已在D004采用及冻结后授权完整业务实现和联调。独立基础前置与完整编码分阶段，真实规范审查→冻结→编码→联调debug→文档迭代历史保留。AI技术选择D002/D003不冒充用户原话。

## 执行与验收证据

- 当前测试技术结果见[独立测试结果汇编](test-results-report.md)：0448fec开发CI后端335通过/零跳过、Python行88.47%、前端24/行92.19%；同SHA容器恢复通过。旧317/88.16等是历史，不替换分母。
- 独立v1公开两报告已发布，e8ceefe整体未通过，900结果340/183/328/49；三批正式P95超线，不能继续写“尚未执行”。183含歧义不当183bug，失败修复不当独立复测。
- 7c27的C-P4四类同名语义检查限定关闭；原口径5886超限786仍failure。精简估计不当已达标。
- 测试路径统一tmp/，历史命令保持执行时点。只读独立公开报告/JSON，不联系实例或跟随私有证据路径；UI独立补充已公开：原e8测3通过/1失败/1阻塞，原900不改，非b485复测。
- [R001原话](../../records/reflections/R001-original.md)已提供本人观点，研究正文及课程建议仍由本人完成；AI证据/模板不当学生署名成品，人工12/3/5不可由AI动作凑数。

本轮Word是准确截止版本的技术审阅材料，不是最终验收稿；逐页QA独立记录，未QA不交付为合格。封面仅私密本地使用，日期留空。

## M3 输入输出与图示补充

[function-contracts.md](../../docs/function-contracts.md)据当前真实签名逐层说明FE API、Runtime四元组、Business数据、纯domain决策、Rows/UoW/迁移、MQ提交后ACK、Scanner/升级及部署CLI的输入输出/错误/事务副作用；[源码索引](../../docs/reports/M3-contract-sources.json)固定行号/哈希和38操作Schema。它是现有实现的M3说明，不是本人预写骨架或新增冻结规格。

[M3八图及修订](../../docs/reports/M3-diagrams.md)已由root真实渲染/独立PNG查看，M3当时最终Word未逐页QA，本轮M4技术审阅Word的QA另记；M2未渲染记录不改。[提示词事实包](../../docs/prompting/M3-evidence-checkpoint.md)区分实发/建议/事后重述。[R001本人原话](../../records/reflections/R001-original.md)是观点来源，未来人工def/#todo工作流与本项目已冻结OpenAPI/DDL实践分开，不倒填人工执行。
