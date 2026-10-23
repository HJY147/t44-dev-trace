# T44 AI可执行规格相关文件说明

M5技术工作稿，非最终验收；生产内容固定6ba9f94，当前1.1.0/14冻结文件，旧1.0/11文件和M4历史可恢复。AI文档岗整理，公开无个人封面值，日期空。

Agent-Role documentation；Prompt-Ref ROLE-documentation-M5-REPORTS-v1；Refs #9。

## 文件用途与正确读序

| 顺序/文件 | 约束作用 | 给AI的使用边界 |
| --- | --- | --- |
| 本次授权、[AGENTS](../../AGENTS.md)、岗位TASK、[layout](../../docs/collaboration/implementation-layout.md) | 责任目录、真实留痕、进程/依赖和隔离规则 | 组织约束不替代业务规格；只改本岗，不触独立私密内容 |
| 原始T44及[requirements](../../specs/requirements.md)、[SRS](requirements-report.md) | 8FR/9AC、角色、输入输出、异常、非功能和追踪 | 原任务文本只读；需规开发前先形成，开发中补图/细化不倒填时间 |
| [business-rules](../../specs/business-rules.md)、D001/D004/D005/D006 | 人采用的状态/延期/字段与工时边界 | 容量1–5、成员1–5+7不同；6/7可移工时，返工再验；不猜预算算法 |
| [v1.1冻结清单](../../records/spec-freezes/v1.1.json)及[父清单](../../records/spec-freezes/v1.json) | 当前14项hash、1.0父链、采用/审查/时序 | 189dc冻结后正式实现；早期草稿披露保留，冻结非软件验收 |
| [OpenAPI](../../specs/contracts/openapi.json)/[错误说明](../../specs/contracts/README.md) | 31路径/38操作/130 Schema；输入输出/错误/幂等/时域 | 外层1.1.0、候选结果schema_version仍1.0.0；不擅改1.1.1 |
| [字典](../../specs/database/field-dictionary.md)/[DDL](../../specs/database/schema.sql)/[持久契约](../../specs/database/persistence-contract.md) | 18表226列、类型/约束/锁/事务/outbox/续扫 | 参数化和显式迁移；DDL本次不变；不关约束、不启动偷迁移 |
| [概设详设](design-report.md)/[冻结后端设计](../../specs/backend-design.md)/[M5真实函数I/O](../../docs/reports/M5-function-contracts.md) | 模块进程、函数、时序/副作用/错误和复杂度 | 函数索引锁6ba，不保证未来行号匹配；它是AI据实现补充，非本人预写骨架 |
| [评审模板](../../backend/t44/resources/review-template.json)/[升级规则](../../backend/t44/resources/escalation-rules.json) | 真实八段十项/三级配置，原文hash及版本 | 配置扩展实验证据与生产默认分开；synthetic metadata不当人的新批准 |
| [D007](../../records/decisions/D007-visual-direction.md)/[视觉设计](../../docs/ui/warm-glass/DESIGN.md)/[来源许可](../../docs/ui/warm-glass/NOTICE.md) | 人定暖色/玻璃/圆角、先设计再导入；AI定细节 | 官方OpenDesign本地技能/模板，非App/MCP；原型不连接真实API |
| [评审协议](../../docs/reviews/review-protocol.md)/[测试报告](test-results-report.md) | 准确SHA、八段十项、全源码覆盖与分层结果 | 技术限定复审不替整体、性能、规模或独立验收 |

## 修改与冻结规则

跨模块变化先由人明确业务含糊处、记原值/新值/影响/决定者；责任岗同步需求、接口、字段/存储及调用方/模块测试，准确设计SHA审核后由总协调冻结独立版本再正式实施。没有新冻结就不将未准入合同用于联调，不暗改旧清单。文档岗仅在报告/附录补图与过程，不修改14冻结件。

当前真实顺序与早期草稿限制见[M5过程材料](../../docs/reports/M5-process-evidence.md)、[三新图](../../docs/reports/M5-diagrams.md)。M3八图已有渲染与PNG检查；本轮只新三图，是否已渲染以本轮manifest为准，不重跑未变旧图。

## 执行、测试与验收证据

模块入口、函数I/O及FR映射见[M5追踪](../../docs/reports/M5-traceability.md)；完整准确版本结果见[测试技术报告](test-results-report.md)。5dcb开发412/全43文件0排除、独立v2固定4c的已发布子集、旧e8/P95失败、同源6ba后收到的组合CI与Docker分别记录。当前6051超951，性能/整体验收无新通过，不由单次CI替代。

独立只读明确发布的脱敏报告，私密hash/路径不提供读取许可；不联系独立实例。R001本人观点与R002课程建议已收，研究正文仍本人写；人工12/3/5和单族六版不得由AI活动凑数。

## Word与历史

M4四份私密技术Word共28原页已完成排版QA，内容仅2e/0448；[QA记录](../../docs/reports/M4-word-qa.json)不覆盖M5。M5先交Markdown，未导Word/未调用LO/未重复marker。后续稳定截止和授权后再按documents技能导出并逐页检查，封面仅私密本地，日期空。
