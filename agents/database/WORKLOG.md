# 数据库岗位工作日志

## 2026-10-23 初始化

- 实际操作者：数据库岗位 AI；派工与协调者：总协调。无用户亲自改码记录。
- 实际派工提示词 ID：`ROLE-database-BOOTSTRAP-v1`；来源为本轮总协调实际派工消息，任务文件为 `agents/database/TASK.md`。本岗未另写或冒充执行优化版提示词。
- 已读取：`AGENTS.md`、`agents/database/TASK.md`、`docs/collaboration/team.md`、`docs/collaboration/report-template.md`。
- 已读取原始材料：`specs/sources/T44-taskbook.txt`、`specs/sources/submission-notes.txt`、`specs/sources/homework-requirements.txt`。
- 已确认职责：FR-02 / AC-02 四核心表字段规范与后续建表审查；配合 FR-04、FR-06、FR-07 的事务、约束、审计与幂等数据设计。
- 已向总协调回报后端、消息、调度需补充的信息；尚未收到这些责任岗的确认，不构成共同冻结。
- 实际产物：本日志、`reports/modules/database.md`、`records/handoffs/database.json`，均为初始化资料。
- 当前设计版本标记：`draft-db-v0`，未冻结；未编写模型、DDL、迁移、种子脚本或其他产品代码。
- 未联系或读取独立测试岗内容；未运行模块自测、联调、数据库实例或独立验收。

### 已执行命令及结果

1. `pwd` 与定向 `rg --files`：确认根目录和岗位/模板文件位置。
2. `cat` 指定规则、任务、模板、协作规范及三份原始材料：成功读取。
3. 文件检索包含不存在的 `records/database`，该次 `rg` 返回 2；未将此目录当作已存在产物，未作额外资料调研。
4. `date -Iseconds`：取得初始化时间；检查三份目标文件均不存在后创建，未覆盖既有岗位记录。
5. 文件创建使用补丁工具；随后 `python3` 解析交接单 JSON，检查团队必需字段、三份产物存在性、实现状态及报告行数，退出码 0，报告 49 行。此为资料自检，不是产品测试。

### 待交接

- 后端确认状态枚举、转移条件、版本冲突、项目权限范围及成功/拒绝审计事务边界。
- 消息与调度确认升级幂等业务键、通知落库归属、消息不可用降级与重启续扫数据要求。
- 总协调汇总意见并冻结契约后，再授权字段/DDL逐表评审；评审通过且获迁移派工后才实施迁移。

## 2026-10-23 文档岗问取与 M0 阶段提交

- 询问者：文档岗位 AI；本轮实际派工 ID：`ROLE-database-M0-COMMIT-v1`。此为串行Git协作任务，不是业务实现或初始化提示词的优化版。
- 收到的资料询问原文：“实际产物路径、业务实现/执行状态、尚未冻结的上下游接口、日志与提示词位置。”询问与答复发生于本轮岗位消息，Git首检时间 `2026-10-23T13:26:57+08:00`。
- 已向文档岗回答原文：“实际产物为 agents/database/WORKLOG.md、reports/modules/database.md、records/handoffs/database.json；只有初始化设计资料，业务实现为未实现，未创建模型、DDL、迁移或产品代码。仅做资料自检，未运行模块自测、联调或验收。draft-db-v0 全部未冻结：后端待确认状态/版本/请求幂等/错误码/权限/审计事务，消息待确认事件与消费幂等/通知持久化/降级，调度待确认扫描窗口/规则版本/升级幂等/计划变更与续扫。日志与派工提示词引用在 agents/database/WORKLOG.md、records/handoffs/database.json，任务在 agents/database/TASK.md；初始化实际ID为 ROLE-database-BOOTSTRAP-v1，本轮为 ROLE-database-M0-COMMIT-v1。”
- 已重读本岗任务与交接、GitHub协作规则，核查本岗三份资料无“当前无HEAD”等待更新陈述；初始化记录保留为当时事实。
- Git首检：分支 `codex/team-bootstrap`；暂存区为空；已有 frontend 完整提交 `005ce55dec988a9038c6cc8df91e85698ad84989`，核对正文含 frontend 岗位/派工/Issue 标记，涉及5个frontend文件。其他岗未暂存改动未加入本岗提交。
- 已读取本岗 Issue #4 和真实上游 backend Issue #3；未读取独立测试岗内容或联系测试岗。
- 已保存本岗阶段评论及后端接口问询正文；问询只涉及现有草案中的拒绝审计事务边界，尚无后端确认。
- 实际执行 `gh issue comment 4 --repo HJY147/t44-dev-trace --body-file agents/database/github-stage-comment.md`，退出0，阶段评论：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358120215 。
- 实际执行 `gh issue comment 3 --repo HJY147/t44-dev-trace --body-file agents/database/github-backend-interface-question.md`，退出0，接口问询：https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6358121197 。
- 本轮未新增设计、研究或产品代码，未运行数据库与业务测试；仅在本岗目录保存评论并补充实际问答/交接。提交前再次核对分支和暂存区，提交结果以总协调/文档岗收到的完整SHA为准，不把准备提交写成已经提交。
- 提交前资料复核：`python3` 解析当前交接单，确认5份本岗产物与2个实际提示词引用，报告55行；退出0。`git diff --check --` 本岗5文件退出0；再次核实分支正确、暂存区为空、HEAD仍为上述frontend提交。仅为资料检查，非业务测试。

## 2026-10-23T14:08:13+08:00 完整设计 ROLE-database-DESIGN-v1

- 收到用户采用规则后的完整设计派工及续作要求；实际原文归档 agents/database/prompts/ROLE-database-DESIGN-v1.md。初始化/阶段提交历史保留；现在已生成DDL文本，与M0当时“没有DDL”的事实分阶段，不宣称执行。
- 已读AGENTS、requirements、business-rules、D001/D002、原始T44任务书及review-protocol；backend草案初始不存在，向责任岗索取后读取specs/contracts/openapi.json与specs/backend-design.md；后读implementation-layout。未读取测试内部材料。
- 与backend直接讨论并确认：统一INT IDs/cycle、角色/工时映射、会话辅助表、session→idem→project→members→tasks锁序、持久幂等租约/owner代次、拒绝独立连接失败503、首次升级CAS及重复无增量、自审守卫与hash-only安全入口。总协调追加规则扩展要求后改level范围1..255，v1仍3级；未擅加业务级别。
- 实际设计产物：specs/database/field-dictionary.md、schema.sql、persistence-contract.md；18表225列，含四核心和必要辅助表。统一PK，审计原因码显式映射41项；模板/升级配置可追溯hash。
- 使用官方MySQL8.4 CHECK/FK/DATETIME及SQLAlchemy2事务文档核对设计限制；引用链接在contract。未查阅其他题目或独立测试内容。
- 执行Python文档生成，输出18表225列；随后Python静态自查退出0，结果agents/database/design-static-check.json：35外键引用显式唯一键、94命名约束不重名、41错误映射与OpenAPI相符，关键唯一键/level/ID范围一致。此非MySQL语法解析或运行测试。
- 生成中的两次多文件补丁因不存在的匹配行被工具拒绝，无部分修改；已用准确补丁完成。其余文件创建/读取及资料检查的真实输出在本轮工具记录。
- 真实发表命令：gh issue comment 4 --repo HJY147/t44-dev-trace --body-file agents/database/github-design-confirmation.md；退出0，URL https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358608869 。随后gh issue view 4核验backend确认回复，URL https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358617437 。双方都注明未冻结、未实现，不替代审核。
- deployment真实问迁移入口/版本及备份恢复：本岗答复DDL路径、未实现入口，建议统一t44.cli适配；根随后明确persistence/migrations/tests责任路径与统一CLI。精确迁移命令/版本元数据留后续派工，未执行备份恢复。
- 未执行DDL/迁移/数据库连接，未写模型或其他产品代码；未运行模块自测、联调、验收或性能。未碰根Git索引，无add/commit/push/checkout。
- 待审：四核心及辅助逐表类型/索引/约束、配置原文归档/加载、消息confirm/fallback/消费与续扫、审计故障运维恢复介质、所有真实MySQL并发和性能验证。

## 2026-10-23T14:12:20+08:00 设计归档独占时段

- 实际派工ROLE-database-DESIGN-COMMIT-v1，原文追加本岗prompts/ROLE-database-DESIGN-v1.md；总协调指定commit footer引用ROLE-database-DESIGN-v1。本轮只归档已有设计，无新设计/实现。
- 首检分支codex/team-bootstrap、暂存区为空、HEAD为backend b893353c9bcf45e833f70f56bf6f72025f611271；核对该提交正文与13文件。未加入总协调/其他岗共享改动。
- 读取并复核设计静态摘要：schema、字段字典、contract和当前OpenAPI的SHA均一致；backend会话认证→幂等→project如需→members→tasks锁序与本岗contract一致。原失败记录保留。
- 实际执行gh issue comment 4 --repo HJY147/t44-dev-trace --body-file agents/database/github-design-stage-comment.md，退出0；范围/待审核评论 https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358694236 。
- 准备仅显式暂存本轮10份本岗变化文件并核对暂存清单；commit结果/完整SHA在完成后直接交总协调，不提前记作已提交。DDL/迁移/模型/运行验证仍未执行。

## 2026-10-23T14:33:45+08:00 ROLE-database-DESIGN-v2：C1修复与C3对齐

- 实际收到总协调修复派工，原文agents/database/prompts/ROLE-database-DESIGN-v2.md；已读reports/reviews/design-v1-717cd65ef73560fde7ff5bca2821c9fe2b20d68a.md，原不通过报告未修改/重写。仅负责C1并对齐C3，未改backend C2/C4文件。
- 实际改schema.sql：idempotency_requests.response_request_id ASCII VARCHAR128 NULL；PROCESSING必须NULL，COMPLETE必须非NULL且非空。同字段/语义同步field-dictionary与persistence-contract，当前18表226列。
- 与backend直接确认采用保存最终生成已存结果的处理请求ID；租约接管后可以来自后一次处理；成功主事务与拒绝独立审计事务均在完成时写入。不依赖audit_id或旧meta，首处理original_request_id可NULL，重放取已存非空ID。
- C3说明同步共享API Schema/FormatChecker先验证UTC Z、1000～9999及≤6微秒，再写库；读/写/只读契约校验同域，禁止静默截断。已向backend提醒核对regex转义，backend回报真实边界校验通过；本岗随后独立用实际共享Schema验证9例均符合预期。
- 实际执行根.venv/bin/python＋Draft202012Validator/FormatChecker：9/9符合预期，退出0；原结果agents/database/design-v2-time-check.json。Python静态检查退出0：18表226列、35外键、94约束、41原因码、字段字典/DDL类型空值默认完全一致；C1 CHECK存在；旧静态摘要/原失败审核SHA保留于更新的design-static-check.json。均非MySQL执行/完整SQL解析。
- 实际发表 gh issue comment 4 --repo HJY147/t44-dev-trace --body-file agents/database/github-design-v2-c1-response.md，退出0；URL https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6358988632 ，已通知backend核对。
- 本轮未使用根Git索引，无add/commit/push/checkout，待总协调明确授权；未执行DDL/迁移/数据库连接、未写模型、未运行HTTP/数据库并发/业务测试；未联系或读取独立测试。

### 2026-10-23T14:35:55+08:00 v2修复归档独占授权

- 收到ROLE-database-DESIGN-v2-COMMIT；真实原文追加本轮prompt归档，footer按总协调要求继续ROLE-database-DESIGN-v2。
- 已核验codex/team-bootstrap、暂存区为空、HEAD=72c6c0064e52cb091e8ca4533a1cb862fc46866d；后端v2提交正文与11文件已核对。当前设计/OpenAPI/time-check hash一致，原失败审核SHA不变。
- backend已直接回复确认最终完成者response_request_id与README/backend-design一致；保留本岗已有Issue回复，不发重复评论。
- 本次仅显式暂存已列10份本岗修复资料；提交前核对精确清单及diff-check。实际commit完整SHA由提交后回报，不提前宣称已提交；未执行DDL/模型/迁移或运行测试。

## 2026-10-23T15:04:00+08:00 ROLE-database-FOUNDATION-v1通用基础

- 实际派工原文agents/database/prompts/ROLE-database-FOUNDATION-v1.md；本树codex/database-runtime起点bc0cd349fcf854f48f4179e1f131e5c2dd8a7e68。只读本树AGENTS/implementation-layout/持久契约；本轮不写18表ORM/项目迁移，不接API。
- 已实现backend/t44/persistence下Engine/UoW/CoreGateway/内部异常和README，模块自测位于backend/tests/persistence。与backend直接确认工厂签名/CommitUncertain；提交确认失败后的rollback仅资源清理，不推断未提交。
- 只读backend树pyproject/requirements.lock，以python3.12 -m venv .venv及uv pip install --system-certs --python .venv/bin/python --require-hashes -r 后端锁实际安装67依赖，退出0；未改锁。实际SQLAlchemy2.1.6/PyMySQL1.2.3/pytest9.1.1。
- 首轮pytest15通过；Ruff首次7个风格失败（SIM105、I001、5个SIM117）原文foundation-lint-run1.log保留。修复后测试17通过/ruff通过；又补进入中断关闭资源的针对性检查，最终run3为18 passed in0.16s，Ruff All checks passed，退出0。所有输出原样存本岗run日志，不将风格失败删去或冒充产品缺陷。
- 测试范围为受控SQLite玩具表生命周期、绑定值及allowlist、mock MySQL初始化SQL/脱敏；测试夹具使用SQLite建表，不执行项目schema.sql。没有MySQL实库、事务隔离/CAS/约束/迁移/HTTP/性能或独立验收结果。
- 真实故障注入先commit再抛确认异常，行确实已存在，CommitUncertain在rollback和close失败后仍保留；同时测捕获驱动异常不允许部分提交及连接归还。环境/源码SHA见foundation-validation.json。
- 文档岗M1问取：分支/SHA/实际DDL迁移模型仓储/事务幂等图锁边界、命令结果、C1–C4与Q002状态、接口和日志。已原文回答“当前database-runtime树、起点bc0cd349...尚未提交；18表226列仅静态设计；通用基础进行中，新测试尚未运行；无MySQL/模型/迁移/API，C1–C4技术结论与Q002人的取舍分别记录”，该回答是当时事实；现已完成18项自测，待提交后补SHA/PR给文档岗。
- 已实际发表gh issue comment4 --repo HJY147/t44-dev-trace --body-file agents/database/foundation-stage-comment.md，退出0，URL https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6359431821 。
- Q002人的字段/错误码选择仍待回复，当前只有基础层实现；用户未亲自改码，本轮AI修改不当作人工改码留痕。未联系或读取独立测试，未操作根工作树索引。准备仅显式提交本树本岗文件，再push独立分支/draft PR，不merge或发布reviewer成功。

### 2026-10-23T15:06:24+08:00 foundation实际提交与draft PR

- 本树显式暂存20份本岗文件并核对精确清单，git diff --cached --check退出0；实际产品提交7caa2eff8e6b4fbb145c7160a3a859d5bba8b3cc，footer Agent-Role database / Prompt-Ref ROLE-database-FOUNDATION-v1 / Refs #4。
- git push -u origin codex/database-runtime实际成功；GitHub连接器用本岗foundation-pr-body.md同内容创建draft PR https://github.com/HJY147/t44-dev-trace/pull/17 ，base codex/team-bootstrap；attach_artifact实际成功。读回draft=true/merged=false/mergeable=true，不能据此声称审核通过。
- 创建后本树status为空、暂存区为空、本地/远端SHA一致；本次补记只更新日志/报告/handoff，无产品变化，不重复已通过测试。完整最终提交SHA另交总协调与文档岗。

## ROLE-database-PERSISTENCE-v1阶段1

- 用户D004实际采用Q002后，按派工先无冲突merge ae60dc3并读冻结manifest/AGENTS；本轮已获18表完整实现及迁移授权，之前foundation限制保留为当时事实。
- 与backend数分钟内确定实际RowsGateway/Pred/codec签名并实现：冻结18表226列Core元数据由打包冻结SQL/摘要构造；同名表/列白名单，查询/锁/insert生成ID/CAS条件update/delete/count/savepoint及完整错误分类。
- 实际本地模块测试21 passed in0.26s；仅SQLite可移植夹具与mock，MySQL-only CHECK保留于生产元数据/原DDL，未假称SQLite验证MySQL CHECK或FOR UPDATE。阶段1暂未完成migration/seed/outbox专用操作，不报完整完成。
- Ruff导入自动格式调整后按固定风格重排；未修改共享依赖锁/API/其他岗文件，未联系独立测试。准备先提交本阶段供backend直接互接，再继续其余能力。

## ROLE-database-PERSISTENCE-v1：真实迁移与门面修复阶段
- 用户D004采用后合并ae60dc3，随后合并总协调集成6afd13f；本岗未改共享锁或其他岗源码。
- 真实官方MySQL8.4.11 / t44_test：首次迁移成功，18表226列与冻结SQL摘要核对无缺陷；重复迁移返回already_applied=true，未drop/重建既有表。新增t44_schema_migrations仅技术版本记录，不算第19张业务表。
- 首脚本额外凭据键导致构造前TypeError，修为仅app连接键allowlist；从未使用root凭据、未输出连接串。首次真实测试3失败26通过（CHECK驱动错误分类），保留persistence-mysql-tests-run1.log，修为兼容PyMySQL3819 OperationalError后29通过。
- 已修backend实际反馈的tasks循环FK主键生成：id显式autoincrement=ignore_fk；SQLite与MySQL真实insert/get返回整数ID。hash-only初始化已实现合法Argon2id校验，非法输入通过独立新UoW持久脱敏拒绝审计；首次此入口真库验证通过。
- 证据：persistence-mysql-migration-run1.json、persistence-mysql-tests-run1.log、run2.log；Ruff format与check退出0。此阶段尚未宣称outbox/scan/seed、API联调、MQ、独立验收完成。

## ROLE-database-PERSISTENCE-v1：供消息/调度的阶段2实际交接
- 已实现OutboxStore claim/get/confirm/retry/consume/fallback、ScanStore start/get/recoverable/page/checkpoint及可选IdempotencyStore原语，精确签名/返回与事务边界在产品README。
- 真MySQL新增同key并发唯一/租约owner换代与最终response_request_id、扫描并发UUID/新Store重启游标恢复、outbox租约过期/retry/confirm、consume/fallback并发仅1通知且迟到confirm失效。run3为33通过；格式/显式所有权更新修复后针对性run4仍33通过，Ruff check退出0。
- 原执行失败：第一次追加测试apply_patch上下文与已格式化文件不同，未写入，随后按实际文件重做patch成功；无测试结果或代码失败被伪报通过。首次构造TypeError/真库3819分类失败记录均保留。
- 按总协调实际要求先交可运行Store并释放槽位，不以报告等待全部seed。seed草稿移至本岗agents/database/drafts/（非产品入口，未执行，需补代表状态/轮次一致性），不称整体任务完成。
- 实际Issue4/3 body-file评论URL分别6360580838/6360581522；未冒称消息/调度本人已确认。prompt归档本轮实际完整任务及阶段收口原文。
- 用户D004选择已生效；旧日志Q002待回复保留为当时事实，当前报告/交接已更新。未触独立testing资料，不发审核成功。
- 总协调与backend实际指出CI只给DATABASE_URL+T44_DATABASE=t44_ci且拒skip，已修改本岗fixture双环境、显式数据库一致/隔离库限制、CI缺配置fail及integration marker。本机路径须T44_TEST_DATABASE=t44_test。run5全33通过；另外用真实本机库但完全同CI环境变量入口12通过、无skip，保存persistence-ci-env-test.log，不冒充GitHub hosted CI结果。
- 阶段2真实产品提交af439304c8615e90d470a631dc41dcd76cbd5d6f已push；PR17已用GitHub connector重写完整当前范围（明确seed pending），并实际attach_artifact成功。后续仅补PR正文/交接元数据，不算新业务实现或验证。按总协调要求结束小阶段释放槽位，剩余seed与集成待恢复。

## ROLE-database-RECOVERY-SEED-v1：恢复接口小阶段
- 实际读Issue4 messaging评论6360793043，直接确认精确签名recover_confirmed(*,confirmed_before,now=None,limit=100)，旧token终态stale_owner符合约定。
- 实现固定MySQL JSON_TABLE+NOT EXISTS候选过滤：先排除完整通知，limit不被旧完整事件占满；同event FOR UPDATE SKIP LOCKED后重新比recipient/notice，只有created>0才confirmed→fallback。未改冻结DDL。
- 首次真库新增回归2失败12通过：共享t44_test存在其他阶段缺通知confirmed，候选正确优先返回较早事件，干扰“仅本夹具”断言。保留recovery-mysql-tests-run1.log；未删除/重置他岗数据，给本夹具独立confirmed时间窗口后14通过(run2，0.35s)。检查消费者持锁并发恢复跳过、完整后不降级、3旧完整不饿死后续缺失、迟到confirm与重复消费。
- Ruff check通过；此小阶段先commit/push给MQ/root，不等seed，不声称RabbitMQ/完整HTTP/独立验收完成。
- 总协调真实提出claim公平性审查；先在独占t44_bench跑无网络真实反例：batch2的旧低ID普通事件每轮retry后反复ready，3轮均未claim后来升级事件（claim-fairness-before.log）。改pending为next_attempt_at,id、leased为lease_until,id后同案例通过（after.log），沿已有索引且保持SKIP LOCKED/token fencing，无DDL变更。仅删除本案例明确ID的临时outbox数据，未动seed业务行，未碰test/dev/acceptance。
- 生产seed_demo已实现并与实际BE CLI惰性入口核对，无需BE再写SQL：签名保留projects/tasks/dependencies/records，新增可选seed/anchor_at/template_path/rules_path/batch_size。官方t44_bench空库首次迁移18/226通过，250批单UoW实际生成40项目/6000task/9000依赖/11400review+3600decision，另3600assessment；七态6=2400，其余各600。生成3.781s仅模块执行耗时非压测结果，校验20.959s通过；增强完整冻结JSON/模板rawhash/当前轮次/容量和批准指针检查后24.014s通过，真实CLI重复seed-demo退出0、不同seed拒绝且不覆盖（seed-mysql-bench-run1/final.json）。未触acceptance或清空dev/test。
- root澄清lease到期不单独定义新业务拒绝，接管换owner_token才必须fence旧worker；已向BE撤回单纯到期缺陷建议，未越界改Runtime。rg证实旧CoreGateway/TableBinding、可选IdempotencyStore只被本岗测试使用，删除105+124行重复生产代码；18项原事务/资源/注入/NULL/标识符断言迁到真正Rows，连同seed共23项通过；同key并发/接管/旧owner拒绝/最终response_request_id回放与内容冲突改调用实际Runtime并在真bench通过，不删功能或弱断言。
- 标准cloc2.10按root公开source-counting政策/原脚本（只覆盖ROOT为本worktree，固定工具hash校验）从已提交9aeb697归档统计：应用4582，本岗persistence Python1500；此树仍旧FE/未全量MQ，不能声称最终整合规模通过。完整逐文件证据recovery-seed-source-count.json。
- 真实seed body-file评论Issue4 URL6361347920、Issue3 URL6361348378；BE确认正在merge9aeb697。恢复/公平性源码早已独立交MQ，不因最终报告延迟下游。当前文档归档只说明真实边界，不新增实现。
- GitHub connector已实际重写PR17标题/正文为完整MySQL持久、恢复与生产合成数据范围，并再次attach_artifact成功，仍保持draft，不设审核通过。本轮代码已9aeb697交接，下面仅归档本岗报告/提示词/统计/评论与状态，结束释放槽位。

## ROLE-database-INTEGRATION-FIX-v1：实际整合规则字段缺陷
- BE实际全量整合报告312通过/2失败/3本地Rabbit跳过，两个seed失败为仍读旧内部rules.rule_version；原失败由BE保留integration-full-first.log，不将旧独立树seed通过等同正式整合通过。
- 干净fast-forward merge codex/integration 6217b8c，实际正式资源为version/effective_at/decided_by；仅seed.py映射rule_version=version并显式保存rule_effective_at/rule_decided_by，未改资源或测试文件。
- 旧t44_bench清单/hash不修改；资源/版本/参数不同明确StatementRejected并要求新空项目schema，绝不覆盖。原test_seed两个断言不编辑，仅实际执行2通过；Ruff check通过。
- 已请求root新建t44_seed_verify及同app权限供新资源真库生成验证；最小产品修复先交，不以尚未建库拖延BE全套回归。测试统一tmp迁移由root负责，本岗未新增/改测试文件。
- root实际建库并授权t44_seed_verify后，用同app四键凭据（不输出连接串）真实首次迁移/默认40项目6000任务9000依赖11400评审+3600决定成功，七态全量JSON/引用/轮次/指针/容量/DAG核验通过；正式rule_version1/effective_at/decided_by与实际资源逐项相符，rawhash63bda0d3...，重复manifest幂等。生成3.835s、校验24.554s仍仅模块执行耗时。完整integration-formal-seed-mysql.json。
- 旧bench当前新资源调用明确拒绝，前后计数与manifest完全不变，integration-old-bench-guard.json；不更写旧hash。未改测试文件/路径、未清现有库。根已先merge e06，此次只证据/报告/交接元数据checkpoint，随后释放槽位。

## ROLE-database-REVIEW-FIX-v1：C-P4源码checkpoint，未运行
- 收到root转派审核C-P4：旧checker名称集合会误收同名结构变化，这是检查器错误接受而不是已发生实库漂移。没有读取/改动tmp/reviewer/957或任何独立tmp/private-*资料。
- 干净fast-forward同步7ce7171；限定语义比对有序索引列/unique/排序/前缀、index/unique双视图冲突，FK源列/目标schema/表/列/动作，CHECK用冻结语法AST规范化保留AND/OR优先级、字符串大小写与函数参数，无法识别则拒。MySQL NO ACTION/RESTRICT及同schema引用合理归一化；不靠去掉所有括号宽松比较。
- 956已先向root占号，实际文件tmp/backend/persistence/956_schema_semantics.py以纳入现有tmp/backend收集；含自岗Inspector形状回归与仅显式t44_review且业务表为空的变更/恢复探针。未改957或冻结DDL/API。
- 性能限制到达前只读查看过MySQL Inspector正常输出以核真实反射形状；root限制后没有跑pytest/真实MySQL迁移/seed/构建，只编辑、源格式化与Git/日志。源格式化不是lint或测试通过。t44_review已建但本岗尚未使用。
- root明确性能窗口含400并发和后续两个600秒批次，要求先提交“未运行、待性能窗后验证”可审checkpoint并暂交接释放槽位；遵此不把C-P4标为已过。seed row-builder减重复未启动；当前统一规模仍超5100，不声明达标。
- 文档岗M2真实问取已原文短答当前发布5849b10/e06及旧模块证据边界，并补同步后的路径993_foundation/989_rows/988_mysql/975_seed；旧日志命令保持当时真实路径。明确当前C-P4进行中，不为文档重测。

## ROLE-database-REVIEW-FIX-v2：真实GHA失败与最小修复
- 收到新续派并原样归档prompts/ROLE-database-REVIEW-FIX-v2.md。安静窗口未获结束通知；仅远端日志读取、源编辑和Git，不运行本机pytest/数据库/seed/HTTP/构建。
- 原始run39938428158（PR merge）及39938417442（branch3ed）都为static失败；下载原始job日志、run元数据及static artifact的bandit.json/static-console.log，保存在ci/review-fix-v2/。两者Ruff通过，Bandit B105唯一命中migrations.py:68，token与'('比较误判口令；contracts/coverage/frontend任务成功。
- 修复只把解析器局部变量token改lexeme，词法/语义/断言不变，无nosec、无门禁或测试削弱。保存失败报告/hash和实际命令差错于original-failures.json；不把下载成功当测试通过。
- 本checkpoint提交后交给托管CI；t44_review受控结构改动/重复迁移拒绝/恢复验证仍未执行，C-P4未关闭。seed去重在下一小阶段，当前未改seed。
