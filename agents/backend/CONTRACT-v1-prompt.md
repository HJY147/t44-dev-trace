# ROLE-backend-CONTRACT-v1 实际派工归档

来源：总协调向backend岗位发送的实际任务；原文摘录如下，不是另造优化版，也不记为用户亲自改码。

> 用户已明确采用业务规则并要求继续设计开发，新增后续任务 ROLE-backend-CONTRACT-v1（覆盖旧初始化任务“只做初始化”的阶段范围，但本任务仍不编码产品）。读取 specs/requirements.md、specs/business-rules.md、architecture.md、records/decisions/D001-business-rules.md 及原始T44。先为完整产品设计 specs/contracts/openapi.json（OpenAPI3.1，三类主接口和所需鉴权/项目/依赖/评审/通知辅助接口，输入/输出/错误及枚举完整）、specs/contracts/README.md、specs/backend-design.md。使用同步FastAPI＋SQLAlchemy2/PyMySQL统一数据库访问，消息Pika、APScheduler独立进程，便于模块一致；不要写ORM/迁移或产品实现。
>
> 业务状态出口遵循已采用v1，发现缺口给总协调问题，不悄悄增加状态出口。契约需带任务版本与幂等键；先鉴权，正确识别相同请求重放再检查旧版本；不同内容同键拒绝；拒绝审计不随失败主事务丢失；MQ outbox、去重、故障转站内待办后同事件恢复不重提醒。包括任务流转、契约校验、升级通知三接口的性能测量入口和可测错误分支。字典/时间/分页/证据引用/角色范围保持统一，避免只列URL的空壳契约。各接口未经总协调和审核岗复核前都标草案，不声称冻结或实现。

后续实际协调指令与采纳关系（记录事实，不计为新用户决定）：

- M0先按documentation串行索引授权完成，实际提交 `29ec3401564243dc34f41e6a1bcca81b73528455` 后释放索引；新合同单独设计。
- 采用现有review-protocol八段ID及R01～R10，提供版本化模板；部署CLI初始化账号，登录用户可建项目，成员仅精确添加已有账号。
- 任务version控制所有关联写；schedule_version为改期，delivery_cycle为返工，review_cycle为评审退回；改期仅使上线批准失效，不新增5→4状态出口。
- D002由AI协调者决定依赖/负责人仅开始前编辑；最小权限由协调者细化：start/submit_review仅负责人developer，其他环节按阶段角色。
- 协调者要求代码评审发布者/批准者不得为task.owner；预案审核人不得为created_by，不声称核验SHA真实作者。
- 协调者指出真实OpenAPI重复参数错误，本岗保留失败、修复共享列表污染并用相同工具复验；协调者要求评审项/升级规则版本化可扩展，v1不自动启用新规则。
- 与数据库岗实际确认INT UNSIGNED、cycle命名、租约幂等、独立拒绝审计、session共享锁及升级CAS；具体证据见WORKLOG和本岗Issue确认正文。

本轮最后Git授权原文摘录：

> 仅显式add specs/contracts/{openapi.json,README.md}、specs/backend-design.md、agents/backend本轮日志/验证/实际派工归档、reports/modules/backend.md、records/handoffs/backend.json；不add数据库/共享台账。核对空暂存区/正确分支，完整自检且保留失败；commit footer Agent-Role: backend、Prompt-Ref: ROLE-backend-CONTRACT-v1、Refs #3 #13。保存并发表Issue#3阶段及必要接口确认（正文body-file）。只commit不push/checkout/merge，不宣布冻结/审核通过。

产物映射：本轮三份规格、三份真实验证日志、本归档及阶段/确认正文；模块报告和结构化交接只记实际状态。业务实现、HTTP自测、验收和压测未开始。
