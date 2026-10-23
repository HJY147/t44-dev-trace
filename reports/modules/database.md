# 数据库模块报告

## 当前任务与状态
- 岗位database；当前修复派工ROLE-database-DESIGN-v2，原设计v1；业务实现状态：未实现。
- 用户采用规则见business-rules v1/D001，开始前编辑约束见D002；接口和数据库设计仍待冻结/审核。
- 已读AGENTS、requirements、business-rules、D001/D002、原始T44任务书、review-protocol、backend-design/OpenAPI和implementation-layout。
- 主责FR-02/AC-02；配合状态/排期、评审决策、升级幂等、权限和安全拒绝审计。

## 实际产物
- specs/database/field-dictionary.md：18表226列完整字段、集中字典、四核心逐表核对与待审事项。
- specs/database/schema.sql：MySQL8.4完整CREATE/ALTER DDL提案，统一INT UNSIGNED PK、tinyint枚举；仅文本未执行。
- specs/database/persistence-contract.md：锁序、事务、幂等/CAS、独立拒绝审计、扫描、confirm/fallback/消费边界。
- agents/database/design-static-check.json：本轮静态自查原始摘要与文件SHA，明确非MySQL执行。
- agents/database/github-design-confirmation.md：本轮Issue实际确认正文；prompts/ROLE-database-DESIGN-v1.md为真实派工归档。
- 本岗WORKLOG与records/handoffs/database.json已更新；M0历史及评论原文保留，不以新阶段改写当时事实。

## 字段与事务取舍
- 核心表tasks/task_dependencies/reviews/decisions；必要辅助承接用户/服务会话、项目成员、迭代/计划diff、评估、审计/幂等、outbox/升级/通知/scan。
- version、schedule_version、delivery_cycle、review_cycle分开；返工交付轮次+1且评审轮次重置1，改期留代码评审而撤旧上线批准。
- 成功变更/审计/outbox/幂等结果同事务；拒绝先主事务回滚，再独立连接提交审计和错误快照，失败503。
- 同key持久PROCESSING/owner_token/租约防并发重执；先重放再检查旧版本；不同key同版本仅一次CAS。
- 锁序session→幂等→project如需→成员按user_id→任务按id；同项目依赖变更串行查环，开始/解除回开发/返工锁前驱。
- 升级唯一(task_id,schedule_version,level)，通知唯一(event_id,recipient_id)；新升级CAS版本/次数+1，重复有效请求无增量。
- level范围1..255但v1仍3级，由版本规则清单生效；评审item按模板有效清单，避免扩展引发DDL变更。
- 会话仅存token摘要；初始化持久门面hash-only且独立安全审计，DDL hash形状不能证明已记录。
- 证据JSON/配置快照不代替服务语义校验；生产路径按implementation-layout更新为backend/t44/persistence、backend/migrations、backend/tests/persistence。

## 跨岗确认与未冻结项
- 数据库Issue确认：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358608869 。
- backend责任岗回复：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358617437 ，确认字段映射、cycle、会话锁序、租约幂等、升级CAS、安全边界。
- 上述是责任岗设计对齐，不是总协调冻结或审核通过；消息/调度的confirm、fallback竞态/超时、续扫及配置归档还待确认。
- deployment询问迁移入口已真实回复：当前没有迁移实现；由统一t44.cli适配，版本元数据和精确命令后续迁移派工确认，不伪称可运行。
- 正式数据库逐表审核、配置原文保留/加载、审计故障恢复介质及实际MySQL验证尚未完成。

## 执行和验证
- 资料读取/本岗设计文档生成，官方MySQL8.4/SQLAlchemy2语义核对；未修改其他岗产品路径。
- v2 Python静态自查退出0：18表226列，字典/DDL逐列类型/空值/默认精确一致，35外键/94命名约束/41原因码及关键唯一键一致。
- 静态检查不验证完整MySQL语法或运行约束；真实摘要与hash见design-static-check.json，不能代替数据库执行。
- 两次多文件补丁因目标行不匹配被工具拒绝，未产生部分修改；随后拆分准确补丁完成，未把失败写成成功。
- 未执行DDL、未连接/迁移数据库、未写模型/产品代码；无模块自测/联调/验收/压测。根Git索引未操作，无add/commit/push/checkout。
- 本轮Issue评论通过本岗body-file发表，命令退出0；未联系或读取独立测试岗内容。

## 人机与后续
- 操作者为数据库岗位AI；规则采用者见D001用户事实，D002/技术锁设计为AI协调选择；未记用户亲自改码或凭空凑留痕指标。
- 下一步由总协调冻结规格、reviewer逐表审核，再另行授权模型/迁移实现和真实验证；本轮无迁移许可。

设计归档补记：获ROLE-database-DESIGN-COMMIT-v1独占时段后核验正确分支/空暂存区、四份SHA及锁序一致；范围评论 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358694236 。本次仅归档已有设计，提交结果由完整SHA交接，不等于审核放行。

## v2 审核修复C1与C3对齐
- 原717cd65不通过审核保留不动；C1补response_request_id，PROCESSING为NULL、COMPLETE非空，保存最终生成已存成功/拒绝结果的处理请求ID；接管后不固定首次认领ID。
- 重放original_request_id读此列，初次replayed=false可NULL；不依赖audit_id，不存旧meta/Token。时间先共享Schema/真实日期/范围校验再写DATETIME(6)，UTC Z、1000～9999、微秒≤6。
- 根.venv Draft202012Validator+FormatChecker边界9/9符合预期，证据agents/database/design-v2-time-check.json；只验证Schema，非MySQL/HTTP运行。
- 实际C1回复 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358988632 ；提示词原文已归档prompts/ROLE-database-DESIGN-v2.md；等待新SHA复审，不宣称已通过。
- 修复完成时未操作根索引；后获ROLE-database-DESIGN-v2-COMMIT独占授权，仅归档10份本岗资料，完整SHA另交总协调；未执行DDL/模型/迁移/业务验证。
