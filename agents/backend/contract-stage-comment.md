Agent-Role: backend
Prompt-Ref: ROLE-backend-CONTRACT-v1
Refs: #3, #13

合同设计草案已完成：`specs/contracts/openapi.json`（OpenAPI3.1，31路径/38操作/130schemas）、`specs/contracts/README.md`、`specs/backend-design.md`。含三类主接口及鉴权、项目成员、迭代产能、开始前依赖/负责人、评审模板/证据、上线评估/预案审批、决策、升级、通知已读/处理及项目只读审计。

已对齐用户采用业务v1及协调者D002/权限质量细化：不新增状态出口；先鉴权/项目权限再幂等重放，之后检查旧任务版本；成功写/审计/outbox原子提交，拒绝审计独立事务；新升级事件count/task.version同增，通知仅增notification.version；MQ降级后同事件不重提醒。评审项和升级规则可版本化扩展，但v1仍只R01～R10及原三档规则。

真实规范校验：初稿Idempotency-Key重复失败由AI共享参数列表造成，失败日志保留 `agents/backend/openapi-validation-failure.log`，修复后根.venv openapi-spec-validator通过。辅助离线样例校验器引用用法曾失败，保留 `agents/backend/openapi-offline-resolver-failure.log`；修复后130schemas及6个合成例/整数、bool、extra、UTC约束检查通过，输出 `agents/backend/openapi-validation-success.log`。这些都是规格/离线检查，不是实际HTTP或业务测试。

当前所有接口仍未冻结、业务未实现；没有ORM/迁移/产品代码、HTTP契约测试、联调、独立验收、覆盖率或性能结果。待总协调及reviewer复核契约/DDL/锁序，部署岗确认审计不可用时的持久故障介质；真实作者及证据内容不能仅凭API存在性校验判断。实际派工、协商和M0先前提交记录见本岗WORKLOG/CONTRACT-v1-prompt.md，AI修改不记为用户亲改。
