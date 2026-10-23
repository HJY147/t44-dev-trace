# T44 AI可执行规格相关文件说明（阶段工作稿）

> **阶段工作稿、非最终验收。** 本文是独立的规格介绍说明稿，介绍已存在的文件和正确使用边界；Q002仍pending，完整业务技术冻结、实现和运行证据未完成。

Agent-Role: documentation
Prompt-Ref: ROLE-documentation-REPORTS-DRAFT-v1

## 文件用途与当前状态

| 文件 | 如何约束AI | 当前限制 |
| --- | --- | --- |
| [AGENTS.md](../../AGENTS.md) | 指定岗位边界、责任目录、真实留痕、独立测试及Git协作 | 组织规则不是完整业务规格；用户新的明确授权优先 |
| [implementation-layout.md](../../docs/collaboration/implementation-layout.md) | 指定backend/t44包、进程/入口、各岗可写目录、依赖锁责任 | 是实现派工约定，不证明入口已实现 |
| [requirements.md](../../specs/requirements.md)与[需求工作稿](requirements-report.md) | 将8FR/9AC、量化目标和交付要求映射为任务 | 不能改要求/断言/覆盖率分母以追求通过 |
| [business-rules v1](../../specs/business-rules.md) | 固定用户采用的状态出口、责任人/经理、幂等与三级提醒业务语义 | D001已采用；实际发布/逐单回滚仍由对应人决定 |
| [human-review.md](../../specs/human-review.md)与[Q002](../../records/prompts/Q002-field-errors.md) | 把字段与错误码的人的取舍单列 | 仍pending；预选项、等待或AI复审不能替代用户回复 |
| [OpenAPI](../../specs/contracts/openapi.json)和[契约说明](../../specs/contracts/README.md) | 定义路径、输入输出、类型/时间域、错误及触发条件、幂等/版本 | 0.1.0-draft，38操作；未冻结不联调，Schema自检不是HTTP一致性 |
| [字段字典](../../specs/database/field-dictionary.md)与[DDL](../../specs/database/schema.sql) | 统一四核心表和辅助表的字段/主键/类型/约束/索引，避免魔法值 | 18表226列静态设计，不是MySQL执行或迁移许可 |
| [持久契约](../../specs/database/persistence-contract.md) | 约束会话/图锁序、CAS、成功/拒绝事务、幂等恢复、outbox/fallback | 通用UoW不等于业务事务已实现；运行故障/并发需另证 |
| [backend-design.md](../../specs/backend-design.md) | 连接状态机、门面DI、证据轮次、扫描/通知伪码和复杂度 | 设计与当前代码存在范围分开，见正式模块交接 |
| 将来的review-template.json/escalation-rules.json | 计划位于backend/t44/resources/；版本化精确评审清单与规则数组 | **未来实现路径**，本稿不声称配置已存在/启用；v1仍十项三级 |
| [评审协议](../../docs/reviews/review-protocol.md) | 对准确SHA做八段/十项检查、证据不足不放行 | 协议存在不产生审核success；旧head结论不覆盖新head |

## 给AI的正确读取顺序

1. 先读本次真实授权、AGENTS和本岗位TASK/责任目录，确认阶段、可写范围与禁止项。
2. 读取根原始T44/提交要求及requirements，建立FR/AC映射，不移植其他题目或个人经历。
3. 读取D001业务规则、D002/D003技术约束及Q002真实状态，分清用户决定与AI提案。
4. 读取准确版本的OpenAPI/错误、字典/DDL/持久契约及审核报告，再读目录/门面/上下游正式交接。
5. 任务需实现时才在自己范围写代码和模块自测，记录运行环境、真实命令/结果、修改者及prompt到产物映射。
6. 交接包含完整SHA、输入输出/错误、实际验证及未跑项；文档/Schema/自测/集成/独立验收分开。

## 谁修改、如何评审和冻结

后端负责API/领域/事务编排，数据库负责模型/迁移/持久能力，消息与调度各自负责投递消费和扫描规则，前端只展示并调用权威接口；目录以implementation-layout为准。跨岗问题在Issue提出，由责任岗修改，不覆盖对方未提交工作。文档岗只能说明和汇总，不自行改契约或给出冻结批准。

总协调汇总责任岗确认和人的必要选择，记录准确版本、批准人/角色、时间和影响范围；reviewer按确切SHA独立于被审作者检查。C1–C4在bc0cd349fcf854f48f4179e1f131e5c2dd8a7e68技术复审通过，但Q002待回复，不能据此宣布全规格冻结、允许迁移或产品验收。

契约/字段/规则变化须保留原值、新值、生效时间、影响和拍板人，同步API/DDL/调用方及契约测试；迁移另有逐表审核、明确目标和授权。规则表示范围可扩展不自动授权新业务等级；不得悄悄清理幂等记录或更改状态出口。

## 证据在哪里，能证明什么

- [M1来源清单](../../docs/reports/M1-source-manifest.json)及[真实问取](../../docs/reports/M1-collection.md)：固定来源SHA/哈希、岗位原文及即时/最终交接区别。
- [设计v1失败](../reviews/design-v1-717cd65ef73560fde7ff5bca2821c9fe2b20d68a.md)和[v2复审](../reviews/design-v2-bc0cd349fcf854f48f4179e1f131e5c2dd8a7e68.md)：技术问题、责任岗修复及1130设计断言，不是HTTP用例。
- [M1 GitHub快照](../../docs/reports/M1-github-snapshot.json)：PR/Review准确head与首次Actions真实failure，不能改写为当前产品checks全通过。
- [公开测试初始化报告](../modules/testing.md)和[公开交接](../../records/handoffs/testing.json)：没有产品执行结论；不联系测试、不读私有用例/日志，正式验收由总协调给中性冻结包。
- [设计稿](design-report.md)与[研究稿](ai-development-report.md)：分别归档实现/事务/运行边界和AI协作事实；本人的人工改码/识别/课程意见缺来源处待补。

最终专门说明须在Q002选择、技术冻结、完整代码和测试/验收齐备后更新版本与映射，再与[提交对照](submission-map.md)一起交付；当前独立阶段说明已经形成，不能冒称最终完整规格介绍或软件完成。

T44量化验收线保持原要求：局部domain约98%和本模块测试数不能替代全项目覆盖率≥80%、真实性能和独立验收；相关缺口继续在三报告与提交对照表中保留。
