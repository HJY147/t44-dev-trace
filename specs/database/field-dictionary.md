# 字段字典 v2-draft

状态：数据库完整设计提案，未冻结、未审核放行、未执行DDL、无模型/迁移。实际操作者为数据库岗位AI；派工ROLE-database-DESIGN-v1。配套schema.sql与persistence-contract.md。原始材料只作需求依据，不随本稿复制发布。

## 全局标准与最小范围

- 18表：4核心(tasks/task_dependencies/reviews/decisions)；14辅助仅承接账号及撤销、项目成员、迭代/计划差异、评估预案、审计/幂等、可靠事件/通知及续扫，不建通用工作流/多租户平台。
- 所有表统一id INT UNSIGNED AUTO_INCREMENT；15k评审/决策加持续审计/通知会超过SMALLINT，选择INT为当前可用统一最小层级。业务ID上限4294967295；版本上限2147483647，与API一致，禁止回绕。
- InnoDB、utf8mb4_0900_ai_ci；用户名、哈希、operation/key、SHA等按列ascii_bin区分大小写。业务状态/布尔为TINYINT UNSIGNED，禁止SQL ENUM及散落字符串状态。
- DATETIME(6)仅存UTC，API/只读契约校验/持久入口共享范围1000-01-01T00:00:00Z～9999-12-31T23:59:59.999999Z，仅Z、小数秒最多6位，并验证真实日期；先通过共享API Schema及语义校验再写库，拒绝越界而非截断/取整。连接UTC/严格SQL模式/READ COMMITTED。SQL中的NULL由每列显式声明；默认值只限初始化状态/版本/计数/active，其余服务显式赋值。
- 对外小时为Decimal的0.25倍；内部estimated_quarters MEDIUMINT UNSIGNED(最大400000)、buffer_quarters SMALLINT UNSIGNED(最大40000)，避免float误差/超配BIGINT。capacity JSON仍保存API可读小时快照。
- 外键无级联删除，默认RESTRICT；用户/成员/业务历史不物理删除。复合外键防跨项目及跨任务引用；角色、环、状态出口、有效JSON证据均由事务内领域守卫承担。
- JSON用于固定结构证据/快照，嵌套枚举仍为数值。DB CHECK守数组/对象及必要形状，不能替代JSON Schema、有效模板清单或逐项证据校验。列定义以下直接按当前DDL列出，CHECK/索引以同节列表与schema.sql为准。

## 集中枚举与映射

| 字典 | 固定v1含义及扩展边界 |
| --- | --- |
| TaskState | 1待受理，2开发中，3阻塞，4待评审，5待上线，6已交付，7已回滚 |
| ProjectRole/API | 1经理，2开发，3评审；DB roles_mask位值1/2/4，组合1..7 |
| ResponsibilityStage | 1受理，2开发，3评审，4上线，5外部依赖 |
| ReviewVerdict | 1通过，2拒绝 |
| ReviewItemJudgment | JSON数值1通过、2失败、3未验证、4不适用；必需项不能以不适用规避 |
| AssessmentStatus | 1待评审、2批准、3拒绝；只允许一次审定，终态不可变 |
| DecisionType | 1交付、2回滚、3返工；经理实际决定 |
| AuditOutcome/ActorKind | outcome 1接受2拒绝；actor 1human2service3unidentified |
| EscalationLevel | SQL 1..255；有效rule版本决定实际清单。v1仅1临期、2超期、3严重，未授权第4级 |
| RiskPerspective/Severity | JSON视角1数据2权限3外部依赖4观测；severity1低2中3高 |
| 各表状态 | idempotency 1处理中2完成；outbox 1待发送2租用3confirm4fallback；scan 1运行2完成3中断 |

八段式稳定section_id为scope_baseline、requirements_mapping、change_scope、compatibility、correctness、evidence、findings、conclusion。评审项形状R+2～3位数字，实际清单取template_version；v1仍R01～R10，新增项不要求DDL变更。升级匹配窗口/收件角色/优先级亦取版本化数组；规则原文、hash及决定者可追溯。

### AuditReason v1显式稳定编码

以下是本次设计的完整显式映射，禁止实现时用OpenAPI enum数组下标临时计算。冻结后只追加新码、不重排/复用旧码；API保持字符串错误码。SQL只约束1..255，服务按有效字典拒绝未知编码，扩展不要求改DDL。

| DB码 | API ErrorCode |
| --- | --- |
| 1 | AUTH_REQUIRED |
| 2 | INVALID_CREDENTIALS |
| 3 | TOKEN_EXPIRED |
| 4 | TOKEN_REVOKED |
| 5 | PROJECT_ACCESS_DENIED |
| 6 | ACTION_FORBIDDEN |
| 7 | SERVICE_SCOPE_REQUIRED |
| 8 | RESOURCE_NOT_FOUND |
| 9 | PARAMETER_INVALID |
| 10 | INVALID_JSON |
| 11 | SECURITY_INPUT_REJECTED |
| 12 | STATE_CONFLICT |
| 13 | VERSION_CONFLICT |
| 14 | IDEMPOTENCY_CONTENT_CONFLICT |
| 15 | IDEMPOTENCY_IN_PROGRESS |
| 16 | DEPENDENCIES_UNSATISFIED |
| 17 | DEPENDENCY_SELF_REFERENCE |
| 18 | DEPENDENCY_CYCLE |
| 19 | DEPENDENCY_EDIT_LOCKED |
| 20 | EVIDENCE_REQUIRED |
| 21 | REVIEW_NOT_PASSED |
| 22 | REVIEW_BASELINE_MISMATCH |
| 23 | RELEASE_APPROVAL_REQUIRED |
| 24 | ASSESSMENT_BASELINE_MISMATCH |
| 25 | OWNER_NOT_PROJECT_DEVELOPER |
| 26 | LAST_MANAGER |
| 27 | MEMBER_IN_USE |
| 28 | ACCOUNT_NOT_INITIALIZED |
| 29 | TIME_RANGE_INVALID |
| 30 | CAPACITY_REFERENCE_INVALID |
| 31 | NOT_ELIGIBLE_FOR_ESCALATION |
| 32 | SCHEDULE_VERSION_CONFLICT |
| 33 | RULE_VERSION_CONFLICT |
| 34 | CONTRACT_INVALID |
| 35 | AUDIT_UNAVAILABLE |
| 36 | DEPENDENCY_UNAVAILABLE |
| 37 | TRANSACTION_UNCERTAIN |
| 38 | RATE_LIMITED |
| 39 | PAYLOAD_TOO_LARGE |
| 40 | INTERNAL_ERROR |
| 41 | ASSIGNMENT_EDIT_LOCKED |

## users

账号与Argon2id摘要；持久入口安全审计，DDL仅附加防线。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `username` | `VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | 登录名，ASCII区分大小写，唯一；API限字母数字_.- |
| `display_name` | `VARCHAR(100) NOT NULL` | 用户显示名，最多100字符 |
| `password_hash` | `VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | 仅合法Argon2id编码；DB仅形状防线，持久入口校验并独立审计拒绝；不存明文 |
| `active` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` | 0禁用/撤销，1启用；不物理删除历史关系 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |
| `updated_at` | `DATETIME(6) NOT NULL` | 最后一次真实更新UTC；不使用触发器/隐式自动更新 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_users_username (username)。
约束名：ck_users_active、ck_users_hash_shape。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## service_accounts

服务Token跨轮换的稳定actor_id，不冒用人类经理。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `name` | `VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | 稳定服务主体名，ASCII唯一；无经理身份与口令 |
| `active` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` | 0禁用/撤销，1启用；不物理删除历史关系 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_service_accounts_name (name)。
约束名：ck_service_accounts_active。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## auth_sessions

不透明Token摘要及逐会话/全部会话撤销，满足泄露阻断。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `actor_kind` | `TINYINT UNSIGNED NOT NULL` | 主体类型：1human / 2service；审计另允许3unidentified |
| `user_id` | `INT UNSIGNED NULL` | 用户ID；引用users或按所属文档校验 |
| `service_account_id` | `INT UNSIGNED NULL` | 稳定服务主体FK；和user_id二选一，由actor_kind决定 |
| `token_hash` | `BINARY(32) NOT NULL` | 高熵不透明Token的SHA-256；唯一，不存Token原文 |
| `project_ids` | `JSON NOT NULL` | 服务token授权项目ID数组；初始化校验存在性/唯一性，human会话必须[] |
| `scopes` | `JSON NOT NULL` | 服务权限字符串白名单数组；human会话必须[]，不授予项目经理角色 |
| `expires_at` | `DATETIME(6) NOT NULL` | 会话到期UTC，必须晚于创建 |
| `revoked_at` | `DATETIME(6) NULL` | 已撤销时刻；NULL表示尚未撤销，仍须校验到期/主体active |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_auth_sessions_token_hash (token_hash)；KEY ix_auth_sessions_user (user_id,revoked_at,id)；KEY ix_auth_sessions_service (service_account_id,revoked_at,id)。
约束名：fk_auth_sessions_user、fk_auth_sessions_service、ck_auth_sessions_actor、ck_auth_sessions_scopes、ck_auth_sessions_expiry。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## projects

项目权限和同项目图编辑的串行锁锚点。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `name` | `VARCHAR(100) NOT NULL` | 显示名称；长度与API一致，非全局唯一业务编码 |
| `description` | `VARCHAR(2000) NOT NULL` | 项目说明，最多2000字符，缺省由服务补空串 |
| `version` | `INT UNSIGNED NOT NULL DEFAULT 1` | API乐观版本，范围1..2147483647；成功写CAS后递增 |
| `created_by` | `INT UNSIGNED NOT NULL` | 实际创建用户ID；引用users，角色由业务守卫确认 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |
| `updated_at` | `DATETIME(6) NOT NULL` | 最后一次真实更新UTC；不使用触发器/隐式自动更新 |

索引：PRIMARY KEY (id)；KEY ix_projects_creator (created_by,id)。
约束名：fk_projects_creator、ck_projects_version。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## project_members

多角色、实时参与资格和历史关联；撤销软删除。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `user_id` | `INT UNSIGNED NOT NULL` | 用户ID；引用users或按所属文档校验 |
| `roles_mask` | `TINYINT UNSIGNED NOT NULL` | 内部位集合：经理1、开发2、评审4，可组合1..7；API角色数组1/2/3映射至bit0/1/2 |
| `active` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` | 0禁用/撤销，1启用；不物理删除历史关系 |
| `version` | `INT UNSIGNED NOT NULL DEFAULT 1` | API乐观版本，范围1..2147483647；成功写CAS后递增 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |
| `updated_at` | `DATETIME(6) NOT NULL` | 最后一次真实更新UTC；不使用触发器/隐式自动更新 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_members_project_user (project_id,user_id)；KEY ix_members_user_active (user_id,active,project_id)。
约束名：fk_members_project、fk_members_user、ck_members_roles、ck_members_active、ck_members_version。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## iterations

迭代时间/人力产能/缓冲/延期预案；不隐式改任务。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `name` | `VARCHAR(100) NOT NULL` | 显示名称；长度与API一致，非全局唯一业务编码 |
| `planned_start` | `DATETIME(6) NOT NULL` | 计划开始UTC，API保持同名 |
| `planned_end` | `DATETIME(6) NOT NULL` | 计划结束UTC；严格晚于开始，缓冲不改变此升级截止时刻 |
| `capacity` | `JSON NOT NULL` | API CapacityEntry数组快照：user_id/available_hours；每用户唯一、当前项目成员与0.25h精度由服务校验 |
| `buffer_quarters` | `SMALLINT UNSIGNED NOT NULL` | 缓冲四分之一小时整数；0..40000，对外buffer_hours=值/4 |
| `delay_contingency` | `VARCHAR(2000) NOT NULL` | 延期预案，非空白；API最多2000字符 |
| `version` | `INT UNSIGNED NOT NULL DEFAULT 1` | API乐观版本，范围1..2147483647；成功写CAS后递增 |
| `plan_version` | `INT UNSIGNED NOT NULL DEFAULT 1` | 迭代计划版本；改迭代计划+1，不隐式修改任务排期 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |
| `updated_at` | `DATETIME(6) NOT NULL` | 最后一次真实更新UTC；不使用触发器/隐式自动更新 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_iterations_project_id (project_id,id)；KEY ix_iterations_project_time (project_id,planned_start,id)。
约束名：fk_iterations_project、ck_iterations_time、ck_iterations_capacity、ck_iterations_buffer、ck_iterations_versions。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## tasks

核心1：状态机当前快照、四计数、阻塞与证据引用。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `iteration_id` | `INT UNSIGNED NOT NULL` | 所属迭代ID；同项目外键，排期diff与task_id二选一 |
| `title` | `VARCHAR(200) NOT NULL` | 任务标题，1..200字符且非空白 |
| `description` | `VARCHAR(4000) NOT NULL` | 任务说明，最多4000字符，缺省补空串 |
| `owner_id` | `INT UNSIGNED NOT NULL` | 同项目成员FK；必须active且含开发角色，编辑仅开始前 |
| `state` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` | 任务状态1..7，含义见集中字典；只能服务状态机改写 |
| `version` | `INT UNSIGNED NOT NULL DEFAULT 1` | API乐观版本，范围1..2147483647；成功写CAS后递增 |
| `schedule_version` | `INT UNSIGNED NOT NULL DEFAULT 1` | 任务排期版本；初始1，改期/返工+1；升级业务去重基线 |
| `delivery_cycle` | `INT UNSIGNED NOT NULL DEFAULT 1` | 交付轮次；初始1，回滚返工+1，和排期版本独立 |
| `review_cycle` | `INT UNSIGNED NOT NULL DEFAULT 1` | 本交付轮次内评审轮次；拒绝返开发+1，返工新交付轮次重置1 |
| `planned_start` | `DATETIME(6) NOT NULL` | 计划开始UTC，API保持同名 |
| `planned_end` | `DATETIME(6) NOT NULL` | 计划结束UTC；严格晚于开始，缓冲不改变此升级截止时刻 |
| `estimated_quarters` | `MEDIUMINT UNSIGNED NOT NULL` | 估计工时四分之一小时整数，1..400000，对外estimated_hours=值/4 |
| `buffer_quarters` | `SMALLINT UNSIGNED NOT NULL` | 缓冲四分之一小时整数；0..40000，对外buffer_hours=值/4 |
| `delay_contingency` | `VARCHAR(2000) NOT NULL` | 延期预案，非空白；API最多2000字符 |
| `blocked_from_state` | `TINYINT UNSIGNED NULL` | 仅state3时非NULL且为1/2/4/5；解除从此返回，不信任客户端目标状态 |
| `block_reason` | `VARCHAR(2000) NULL` | 仅阻塞时非空白；解除后NULL，历史留审计 |
| `responsibility_stage` | `TINYINT UNSIGNED NULL` | 仅阻塞时1..5；intake/development/review/release/external_dependency |
| `artifact_revision` | `CHAR(40) CHARACTER SET ascii COLLATE ascii_bin NULL` | 固定40位小写Git SHA；服务校验形状与当前提交审核对象 |
| `latest_review_id` | `INT UNSIGNED NULL` | 本任务最近发布评审FK，不自动等于已通过评审 |
| `approved_review_id` | `INT UNSIGNED NULL` | 本任务当前有效通过评审FK，业务校验轮次/SHA/最新 |
| `approved_assessment_id` | `INT UNSIGNED NULL` | 本任务当前已批准评估FK，失效时清空；不得跨任务引用 |
| `approved_assessment_version` | `INT UNSIGNED NULL` | 上述批准的评估行version，与ID成对NULL/非NULL |
| `escalation_count` | `INT UNSIGNED NOT NULL DEFAULT 0` | 成功创建升级事件次数；重复扫描/消息消费不增加 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |
| `updated_at` | `DATETIME(6) NOT NULL` | 最后一次真实更新UTC；不使用触发器/隐式自动更新 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_tasks_project_id (project_id,id)；KEY ix_tasks_project_state (project_id,state,id)；KEY ix_tasks_owner_state (project_id,owner_id,state,id)；KEY ix_tasks_iteration (project_id,iteration_id,id)；KEY ix_tasks_scan (state,planned_end,id)。
约束名：fk_tasks_project、fk_tasks_iteration、fk_tasks_owner、ck_tasks_state、ck_tasks_versions、ck_tasks_time、ck_tasks_hours、ck_tasks_block、ck_tasks_assessment_pair、ck_tasks_escalations。
另由文件末段ALTER补充同任务latest_review/approved_review/approved_assessment外键，避免建表循环。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## task_dependencies

核心2：同项目有向边、双向索引，自依赖/重复边约束；图环需锁内DFS。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NOT NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `depends_on_task_id` | `INT UNSIGNED NOT NULL` | 前驱任务；同项目复合FK；禁止自依赖，查环由project锁下业务校验 |
| `created_by` | `INT UNSIGNED NOT NULL` | 实际创建用户ID；引用users，角色由业务守卫确认 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_dependencies_edge (project_id,task_id,depends_on_task_id)；KEY ix_dependencies_reverse (project_id,depends_on_task_id,task_id)；KEY ix_dependencies_creator (created_by)。
约束名：fk_dependencies_task、fk_dependencies_predecessor、fk_dependencies_creator、ck_dependencies_not_self。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## reviews

核心3：不可变八段式/清单证据及对象基线；不能由任务负责人自评/自批。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NOT NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `version` | `INT UNSIGNED NOT NULL DEFAULT 1` | 不可变已发布评审版本恒1；更正以新记录发布，不覆盖历史 |
| `delivery_cycle` | `INT UNSIGNED NOT NULL` | 交付轮次；初始1，回滚返工+1，和排期版本独立 |
| `review_cycle` | `INT UNSIGNED NOT NULL` | 本交付轮次内评审轮次；拒绝返开发+1，返工新交付轮次重置1 |
| `template_version` | `INT UNSIGNED NOT NULL` | 有效评审模板版本，服务校验对应有效清单 |
| `template_hash` | `BINARY(32) NOT NULL` | 不可变模板UTF-8原文SHA-256；模板原文按版本归档 |
| `artifact_revision` | `CHAR(40) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | 固定40位小写Git SHA；服务校验形状与当前提交审核对象 |
| `sections` | `JSON NOT NULL` | 八段式对象数组，长度8；稳定section_id精确覆盖与内容/证据由服务校验 |
| `checklist` | `JSON NOT NULL` | 10..100项JSON数组，item_id=R+2~3位数字；有效模板清单精确覆盖且不重复，必需通过项逐项有证据 |
| `verdict` | `TINYINT UNSIGNED NOT NULL` | 1pass / 2reject；必需项不全通过不得pass |
| `reviewer_id` | `INT UNSIGNED NOT NULL` | 发布者users FK；必须项目评审/经理，且不是task.owner |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_reviews_task_id (task_id,id)；KEY ix_reviews_task_cycle (project_id,task_id,delivery_cycle,review_cycle,id)；KEY ix_reviews_reviewer (reviewer_id,id)。
约束名：fk_reviews_task、fk_reviews_reviewer、ck_reviews_versions、ck_reviews_sections、ck_reviews_checklist、ck_reviews_verdict。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## release_assessments

四视角风险和不可变预案文档，审批与实际经理决定分离。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NOT NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `version` | `INT UNSIGNED NOT NULL DEFAULT 1` | 评估审批CAS版本，文档创建1，首次审定后2且终态不可变 |
| `schedule_version` | `INT UNSIGNED NOT NULL` | 任务排期版本；初始1，改期/返工+1；升级业务去重基线 |
| `delivery_cycle` | `INT UNSIGNED NOT NULL` | 交付轮次；初始1，回滚返工+1，和排期版本独立 |
| `status` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` | 1pending_review / 2approved / 3rejected |
| `risks` | `JSON NOT NULL` | 恰四项，perspective1数据2权限3外部依赖4观测；severity1低2中3高，均有mitigation/evidence |
| `rollback_plan_version` | `INT UNSIGNED NOT NULL` | 任务全历史预案版本；锁任务后分配单调+1，决定引用时必须匹配 |
| `rollback_plan` | `JSON NOT NULL` | 不可变RollbackPlan对象；含目标/触发/步骤/影响/验证/负责人/证据，负责人当前项目成员 |
| `created_by` | `INT UNSIGNED NOT NULL` | 实际创建用户ID；引用users，角色由业务守卫确认 |
| `reviewed_by` | `INT UNSIGNED NULL` | 预案评审者；必须有角色且不同于评估created_by |
| `reviewed_at` | `DATETIME(6) NULL` | 完成预案评审UTC，pending时NULL |
| `review_reason` | `VARCHAR(2000) NULL` | 预案评审reason；pending时NULL，终态非空，API只读字段 |
| `review_evidence` | `JSON NOT NULL` | 预案审批证据引用数组；pending为空，终态1..30项 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_assessments_task_id (task_id,id)；UNIQUE KEY uq_assessments_plan_version (task_id,rollback_plan_version)；KEY ix_assessments_current (project_id,task_id,delivery_cycle,schedule_version,status,id)；KEY ix_assessments_creator (created_by)；KEY ix_assessments_reviewer (reviewed_by)。
约束名：fk_assessments_task、fk_assessments_creator、fk_assessments_reviewer、ck_assessments_versions、ck_assessments_status、ck_assessments_risks、ck_assessments_plan、ck_assessments_review。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## decisions

核心4：不可变交付/回滚/返工决定，保留人/时/原因/影响/目标/依据。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NOT NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `type` | `TINYINT UNSIGNED NOT NULL` | 1delivery / 2rollback / 3rework；实际经理拍板，不等于执行外部部署 |
| `decided_by` | `INT UNSIGNED NOT NULL` | 实际经理users FK，不能用AI或service身份代拍板 |
| `delivery_cycle` | `INT UNSIGNED NOT NULL` | 交付轮次；初始1，回滚返工+1，和排期版本独立 |
| `reason` | `VARCHAR(2000) NOT NULL` | 经理决定原因，1..2000字符 |
| `impact` | `VARCHAR(3000) NULL` | rollback必填1..3000；delivery可NULL；rework为NULL |
| `target_version` | `VARCHAR(128) NULL` | delivery承接release_version；rollback为回滚目标；rework为NULL |
| `assessment_id` | `INT UNSIGNED NULL` | 本任务已审核预案的评估ID；delivery/rollback必填，rework NULL |
| `rollback_plan_version` | `INT UNSIGNED NULL` | 任务全历史预案版本；锁任务后分配单调+1，决定引用时必须匹配 |
| `evidence` | `JSON NOT NULL` | 结构化EvidenceRef数组；仅存引用，不抓取外部URL或据此宣称证据已验证 |
| `decided_at` | `DATETIME(6) NOT NULL` | 实际决定提交UTC |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_decisions_cycle_type (task_id,delivery_cycle,type)；KEY ix_decisions_project_task (project_id,task_id,id)；KEY ix_decisions_actor (decided_by,id)；KEY ix_decisions_assessment (task_id,assessment_id)。
约束名：fk_decisions_task、fk_decisions_actor、fk_decisions_assessment、ck_decisions_type、ck_decisions_cycle、ck_decisions_reason、ck_decisions_evidence、ck_decisions_payload。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## schedule_changes

任务排期或迭代计划前后完整快照差异，非只写新值。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `iteration_id` | `INT UNSIGNED NULL` | 所属迭代ID；同项目外键，排期diff与task_id二选一 |
| `from_version` | `INT UNSIGNED NOT NULL` | 旧task.schedule_version或iteration.plan_version |
| `to_version` | `INT UNSIGNED NOT NULL` | 新计划版本，必须from+1；各目标唯一 |
| `before_plan` | `JSON NOT NULL` | 原完整计划JSON；包括原时间/工时/缓冲/预案或迭代产能 |
| `after_plan` | `JSON NOT NULL` | 新完整计划JSON；不只保存文字变更摘要 |
| `reason` | `VARCHAR(2000) NOT NULL` | 操作/变更/拍板原因，非空白，禁止口令与Token |
| `evidence` | `JSON NOT NULL` | 结构化EvidenceRef数组；仅存引用，不抓取外部URL或据此宣称证据已验证 |
| `changed_by` | `INT UNSIGNED NOT NULL` | 实际改期经理users FK |
| `changed_at` | `DATETIME(6) NOT NULL` | 改期事务UTC |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_schedule_task_version (task_id,to_version)；UNIQUE KEY uq_schedule_iteration_version (iteration_id,to_version)；KEY ix_schedule_project (project_id,id)。
约束名：fk_schedule_task、fk_schedule_iteration、fk_schedule_actor、ck_schedule_target、ck_schedule_versions、ck_schedule_json、ck_schedule_reason。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## audit_events

接受与拒绝/安全记录，未知目标不因FK失败丢失；成功同事务、拒绝独立事务。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `attempted_project_id` | `INT UNSIGNED NULL` | 未解析/越权/不存在项目请求中的ID，故不设外键 |
| `attempted_task_id` | `INT UNSIGNED NULL` | 未解析/越权/不存在任务请求中的ID，故不设外键 |
| `actor_kind` | `TINYINT UNSIGNED NOT NULL` | 主体类型：1human / 2service；审计另允许3unidentified |
| `actor_id` | `INT UNSIGNED NULL` | 稳定主体ID；human与service由actor_kind分scope，未识别可NULL |
| `request_id` | `VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | 关联请求ID，ASCII，审计与响应/脱敏告警可关联 |
| `operation_id` | `VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | OpenAPI稳定operationId，ASCII区分大小写，非原始URL或SQL |
| `outcome` | `TINYINT UNSIGNED NOT NULL` | 1accepted / 2rejected；安全/业务拒绝独立事务 |
| `reason_code` | `TINYINT UNSIGNED NULL` | 集中AuditReason数字编码1..255；完整v1映射见下表；不是enum数组位置 |
| `expected_version` | `INT UNSIGNED NULL` | 被拒/成功请求携带的旧版本，可NULL；不伪造发生过的更新 |
| `observed_version` | `INT UNSIGNED NULL` | 当时观察到的服务端版本，可NULL |
| `before_values` | `JSON NOT NULL` | 字段/值数组白名单，凭据/原SQL/恶意完整输入不得入库 |
| `after_values` | `JSON NOT NULL` | 字段/值数组白名单，拒绝不能伪造状态变化 |
| `evidence` | `JSON NOT NULL` | 结构化EvidenceRef数组；仅存引用，不抓取外部URL或据此宣称证据已验证 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |

索引：PRIMARY KEY (id)；KEY ix_audit_project_task (project_id,task_id,id)；KEY ix_audit_request (request_id,id)；KEY ix_audit_actor (actor_kind,actor_id,id)。
约束名：fk_audit_project、fk_audit_task、ck_audit_actor、ck_audit_outcome、ck_audit_arrays、ck_audit_project_task。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## idempotency_requests

持久认领、owner代次和结果快照，抵抗相同key竞争/崩溃/响应丢失。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `actor_kind` | `TINYINT UNSIGNED NOT NULL` | 主体类型：1human / 2service；审计另允许3unidentified |
| `actor_id` | `INT UNSIGNED NOT NULL` | 稳定主体ID；human与service由actor_kind分scope，未识别可NULL |
| `operation_id` | `VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | OpenAPI稳定operationId，ASCII区分大小写，非原始URL或SQL |
| `idempotency_key` | `VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NOT NULL` | 客户端16..128 ASCII原key，区分大小写；scope内唯一 |
| `request_hash` | `BINARY(32) NOT NULL` | 规范化方法/路径/body（含expected_version）的SHA-256原始32字节；排除敏感认证输入 |
| `status` | `TINYINT UNSIGNED NOT NULL` | 1PROCESSING / 2COMPLETE；不清理完成记录使旧key二次执行 |
| `owner_token` | `BINARY(16) NOT NULL` | 随机16字节所有者代次标识，接管必须CAS换代 |
| `lease_until` | `DATETIME(6) NOT NULL` | UTC租约截止；到期只允许加行锁核旧owner并接管，不直接证明旧事务已结束 |
| `response_status` | `SMALLINT UNSIGNED NULL` | 完成时HTTP 200..499；503结果不完成幂等记录 |
| `response_body` | `JSON NULL` | 原业务响应快照，不含旧请求meta/Token，重放重建meta |
| `response_request_id` | `VARCHAR(128) CHARACTER SET ascii COLLATE ascii_bin NULL` | 生成该已保存成功/拒绝结果的处理请求ID；PROCESSING为NULL，COMPLETE非NULL且非空。租约接管后由最终完成者当前请求定格，不固定为首次认领ID。重放meta.original_request_id读取此列，不反查audit_id、不保存旧meta |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |
| `completed_at` | `DATETIME(6) NULL` | 幂等完成UTC，PROCESSING为NULL |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_idempotency_scope (actor_kind,actor_id,operation_id,idempotency_key)；KEY ix_idempotency_recovery (status,lease_until,id)。
约束名：ck_idempotency_actor、ck_idempotency_state。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## outbox_events

业务提交到MQ投递的可靠事件，event_id稳定、confirm/fallback互斥。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `event_type` | `TINYINT UNSIGNED NOT NULL` | 1business.changed / 2escalation.created，路由不是任务状态 |
| `schema_version` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` | 当前事件载荷版本1，消费者显式拒绝未知版本 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `payload` | `JSON NOT NULL` | 事件对象快照，包含业务版本/升级文字；无Token/口令 |
| `recipients` | `JSON NOT NULL` | 升级接收人ID去重数组；普通business.changed为空，不扩张提醒需求 |
| `status` | `TINYINT UNSIGNED NOT NULL DEFAULT 1` | 1pending / 2leased / 3confirmed / 4fallback；fallback终态 |
| `attempts` | `SMALLINT UNSIGNED NOT NULL DEFAULT 0` | 发布尝试次数，UINT16；达到配置上限进入恢复/告警，不能回绕 |
| `next_attempt_at` | `DATETIME(6) NOT NULL` | 下一次领取/重试UTC |
| `lease_token` | `BINARY(16) NULL` | 发布者随机16字节代次，只有leased非NULL |
| `lease_until` | `DATETIME(6) NULL` | UTC租约截止；到期只允许加行锁核旧owner并接管，不直接证明旧事务已结束 |
| `confirmed_at` | `DATETIME(6) NULL` | broker confirm并未return后的UTC；不等于已消费 |
| `fallback_at` | `DATETIME(6) NULL` | 全部缺失站内通知事务提交时刻；只标记准备不算完成 |
| `last_error_code` | `VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL` | 脱敏基础设施失败分类，不能存原连接串或载荷 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |
| `updated_at` | `DATETIME(6) NOT NULL` | 最后一次真实更新UTC；不使用触发器/隐式自动更新 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_outbox_project_task_id (project_id,task_id,id)；KEY ix_outbox_dispatch (status,next_attempt_at,id)；KEY ix_outbox_recovery (status,lease_until,id)。
约束名：fk_outbox_project、fk_outbox_task、ck_outbox_type、ck_outbox_payload、ck_outbox_state。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## escalation_events

每任务/排期/级别的升级ledger；规则原文及hash追溯。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NOT NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `schedule_version` | `INT UNSIGNED NOT NULL` | 任务排期版本；初始1，改期/返工+1；升级业务去重基线 |
| `level` | `TINYINT UNSIGNED NOT NULL` | 升级级别TINYINT，SQL范围1..255；实际有效值按rule_version配置，v1仅1/2/3 |
| `rule_version` | `INT UNSIGNED NOT NULL` | 有效升级规则版本，范围1..2147483647 |
| `rule_snapshot` | `JSON NOT NULL` | 完整有效规则JSON原文的解析对象；包含版本/生效时间/决定者及规则数组 |
| `rule_hash` | `BINARY(32) NOT NULL` | 规则不可变UTF-8原文的SHA-256原始32字节，非hex字符串 |
| `scan_run_id` | `INT UNSIGNED NOT NULL` | 内部scan_runs整数FK，对外UUID经run_key映射 |
| `planned_end` | `DATETIME(6) NOT NULL` | 计划结束UTC；严格晚于开始，缓冲不改变此升级截止时刻 |
| `observed_at` | `DATETIME(6) NOT NULL` | 选中升级窗口的服务端UTC，不信任客户端时刻 |
| `event_id` | `INT UNSIGNED NOT NULL` | outbox_events.id，稳定事件ID；不可为每次投递重新生成 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_escalation_once (task_id,schedule_version,level)；UNIQUE KEY uq_escalation_event (event_id)；KEY ix_escalation_project_task (project_id,task_id,id)；KEY ix_escalation_scan (scan_run_id,id)。
约束名：fk_escalation_task、fk_escalation_outbox、ck_escalation_level、ck_escalation_versions、ck_escalation_rules。
另由末段ALTER补充scan_run_id外键，保证建表顺序可执行。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## notifications

唯一站内通知，同时用作消费去重；阅读与处理独立。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `project_id` | `INT UNSIGNED NOT NULL` | 所属项目；外键/项目范围过滤，审计未知或安全事件允许NULL |
| `task_id` | `INT UNSIGNED NOT NULL` | 所属任务ID；与project_id组成同项目外键，NULL仅限明确允许的辅助记录 |
| `event_id` | `INT UNSIGNED NOT NULL` | outbox_events.id，稳定事件ID；不可为每次投递重新生成 |
| `recipient_id` | `INT UNSIGNED NOT NULL` | 实际收件用户FK；查询须本人且仍active项目成员 |
| `version` | `INT UNSIGNED NOT NULL DEFAULT 1` | API乐观版本，范围1..2147483647；成功写CAS后递增 |
| `level` | `TINYINT UNSIGNED NOT NULL` | 升级级别TINYINT，SQL范围1..255；实际有效值按rule_version配置，v1仅1/2/3 |
| `title` | `VARCHAR(200) NOT NULL` | 通知标题1..200字符，事件快照生成 |
| `message` | `VARCHAR(2000) NOT NULL` | 站内正文1..2000字符，事件快照生成 |
| `fallback` | `TINYINT UNSIGNED NOT NULL` | 0由MQ消费建立，1故障降级建立；重复消费不覆盖来源 |
| `read_at` | `DATETIME(6) NULL` | 已读UTC，不等于处理完成 |
| `handled_at` | `DATETIME(6) NULL` | 处理完成UTC，与已读分开 |
| `handling_note` | `VARCHAR(2000) NULL` | 处理说明；handled非NULL时必填 |
| `handling_evidence` | `JSON NOT NULL` | 处理证据数组；未处理为空，处理1..30项 |
| `created_at` | `DATETIME(6) NOT NULL` | 创建时刻UTC，由服务在事务内赋值 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_notifications_consumer (event_id,recipient_id)；KEY ix_notifications_recipient (recipient_id,project_id,id)；KEY ix_notifications_unread (recipient_id,read_at,id)；KEY ix_notifications_unhandled (recipient_id,handled_at,id)。
约束名：fk_notifications_event、fk_notifications_recipient、ck_notifications_version、ck_notifications_level、ck_notifications_fallback、ck_notifications_handling。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## scan_runs

UUID映射、规则快照、游标及重启证据；不能替代事件唯一约束。

| 字段 | SQL类型/空值/默认 | 含义与限制 |
| --- | --- | --- |
| `id` | `INT UNSIGNED NOT NULL AUTO_INCREMENT` | 统一自增主键；正数，API上限4294967295；不回收复用 |
| `run_key` | `BINARY(16) NOT NULL` | 外部scan_run_id UUID映射16字节，唯一；全表PK仍INT |
| `rule_version` | `INT UNSIGNED NOT NULL` | 有效升级规则版本，范围1..2147483647 |
| `rule_snapshot` | `JSON NOT NULL` | 完整有效规则JSON原文的解析对象；包含版本/生效时间/决定者及规则数组 |
| `rule_hash` | `BINARY(32) NOT NULL` | 规则不可变UTF-8原文的SHA-256原始32字节，非hex字符串 |
| `cutoff_at` | `DATETIME(6) NOT NULL` | 本轮固定UTC观察时点 |
| `status` | `TINYINT UNSIGNED NOT NULL` | 1running / 2completed / 3interrupted；终态必须finished_at |
| `last_task_id` | `INT UNSIGNED NOT NULL DEFAULT 0` | keyset游标，0表示尚未处理；不是tasks FK |
| `scanned_count` | `INT UNSIGNED NOT NULL DEFAULT 0` | 本run实际扫描条数 |
| `created_count` | `INT UNSIGNED NOT NULL DEFAULT 0` | 本run确定创建升级数 |
| `duplicate_count` | `INT UNSIGNED NOT NULL DEFAULT 0` | 本run确定返回created=false次数 |
| `started_at` | `DATETIME(6) NOT NULL` | 开始UTC |
| `heartbeat_at` | `DATETIME(6) NOT NULL` | 最近进展/心跳UTC，用于识别中断 |
| `finished_at` | `DATETIME(6) NULL` | 本run结束/确认中断UTC，running为NULL |
| `error_code` | `VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin NULL` | 脱敏基础设施错误分类，不存驱动原SQL/敏感载荷 |

索引：PRIMARY KEY (id)；UNIQUE KEY uq_scan_run_key (run_key)；KEY ix_scan_runs_recovery (status,heartbeat_at,id)。
约束名：ck_scan_runs_version、ck_scan_runs_rules、ck_scan_runs_state。
待审：字段/索引/单行CHECK与上游映射需审核岗逐项复核；当前仅静态设计，未在MySQL8.4执行或测量查询计划。

## 四核心表逐表设计核对与待审核

v2仅修审核C1并对齐C3，现为18表226列；未改写717cd65失败审核。幂等首次处理replayed=false时meta.original_request_id可NULL，重放replayed=true时取已保存response_request_id，必须非NULL；所有计划/只读校验同一可存时间域。

| 表 | 类型/主键核对 | 约束及索引核对 | 领域边界与放行缺项 |
| --- | --- | --- | --- |
| tasks | INT统一PK，state/责任环节TINYINT，四计数独立，UTC微秒，工时四分之一整数 | 同项目iteration/owner FK、状态/阻塞成组CHECK、证据同任务FK、project/state/owner/iteration及scan索引 | 合法迁移、轮次/版本更新、证据失效、同version CAS需实现验证；DDL未执行，待正式逐表审核 |
| task_dependencies | INT统一PK及一致FK，单一有向边 | 同项目复合FK、自依赖CHECK、边唯一、反向索引 | 环检查须project锁串行；开始/解除/返工锁前驱后查已交付；并发双向加边未运行 |
| reviews | INT统一PK，verdict TINYINT，version恒1，JSON证据，不存字符串状态 | 同项目任务FK、(task,id)唯一、轮次索引、八段/10..100项形状CHECK | 有效模板精确清单/必需证据/不得自评与最新有效基线须领域实现；非审核通过记录 |
| decisions | INT统一PK，type TINYINT，UTC决定时刻 | (task,cycle,type)唯一、同任务评估FK、按类型必需载荷CHECK | 经理资格/预案已审/引用版本及返工新计划事务需实现；数据库不执行云发布/回滚 |

辅助表亦已逐表列字段、索引、CHECK和外键待审；不以数据库岗设计自查替代reviewer放行。需要补真实MySQL8.4执行、SHOW CREATE TABLE、信息模式/约束负向、事务并发、MQ故障/重启和性能结果，才能形成运行证据。

## 设计取舍和兼容

- JSON快照避免为每个证据项/风险项再扩多表；其结构由共享契约精确校验，状态列仍最小整型。频繁查询字段独立列并索引，不在运行查询中扫描大JSON。
- auth_sessions项目范围用JSON，仅服务会话初始化时校验项目存在；个人权限实时join成员。不存在的scope项目不会自动获得任何业务数据。服务标识与个人ID用actor_kind隔离。
- 配置模板原文按不可变文件版本归档，reviews仅存hash；升级规则原文/hash同时存scan和ledger。模板文件实际路径及加载/保留策略需backend/deployment冻结，本轮没有创建虚构已生效规则。
- DB约束只保证下界；所有数据修改经服务/持久门面，不能把“可任意直连MySQL”当公开产品入口。DDL中hash形状或外键失败不自动产生独立审计。
- v1初建提案无存量迁移；后续改字段须列原值/新值/影响/生效/拍板人及备份恢复，不启动时自动create_all。当前没有批准迁移或执行记录。
