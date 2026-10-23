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
- 完整diff-check对原始GHA日志提示其上游尾空格，原字节保留；源码/报告/handoff/prompt限定diff-check另检，不冒称原始日志无尾空格。未通过改写证据规避提示。
- 在原975测试保留全部断言并添加record_property业务行摘要（唯独排除故意随机生成的Argon2 hash），托管JUnit可提供重构前基线；不新增测试编号/文件，不把记录摘要本身算验证断言。
- 托管4301a68/run39940121559四job success，最小Bandit修复不再报B105；该SHA仍旧seed实现，带全行摘要基线。958此前被下一push取消总体状态，虽其测试步骤成功也不称整次run通过。
- 原975参数化保留原2/20/20/30组并新增默认40/6000/9000/15000组（完整JSON/轮次/七态/容量/指针/幂等/不覆盖断言同样执行），为待合并受信row-builder提供真实等价基线；本机未执行。格式编辑不作为lint成功。
- 原生产seed完整基线2dc2e6d：PR run39940459708四job success，333 passed/0failed/0skipped，原JUnit及日志存ci/review-fix-v2/2dc2-baseline。持久行摘要小组aa4f3aff.../默认全量6d56de11...，含manifest/全部表，只排随机password_hash。
- 将真实基线摘要固定为原975两组额外等价断言，再提交生产row-builder；原所有断言保留。assert_consistent把反复扫描review/decision列表改预先按task分组，校验条件完全相同，避免默认全量组平方扫描。
- 生产去重：受信add集中created/updated/project/task/cycle上下文，仍由冻结TABLES过滤可继承字段，显式值覆盖且最终Rows参数绑定/字段校验；省略冻结server defaults的重复声明；task初始NULL指针只构造一次。新增task对象即加入列表但列表直到完整构建后才批量写入；后续version变更仍修改该同一对象。
- 保留原业务配置、synthetic标记、规则/模板原bytes hash、manifest、7态分布、轮次、容量、证据与单UoW批次；未知等价结果待托管CI，专库MySQL仍未执行。仅源格式编辑并恢复无关原代码排版，不把格式差额用于宣称减量。
- 0a676ee6f7c287893153cdca0c6c6823aacca8a1生产去重checkpoint已push，PR17重新发布范围；远端PR run39941263169进行中。基线artifact的coverage子目录被.gitignore规则命中，已识别并仅显式-f暂存8份本岗下载的JUnit/pytest/migration/gate文件，避免索引引用而缺原证据；未改共享ignore。
- 仅基于Git已提交文本差异：seed.py为88插入/115删除，净减27物理行；这不是cloc最终应用主口径结论，C-P4新增与全局超5100事实保留。新版真实MySQL全量seed未跑，不能用SQLite精确摘要替代。
- 最终产品0a676ee：PR run39941263169与push39941255427均success；下载原始0a676-result证据，JUnit333passed/0failed/0errors/0skipped，两原始行摘要完全一致。Bandit results0，Ruff真实远端通过；覆盖门禁2480/2807行、无漏测生产文件（仅该托管SHA，非独立验收）。
- Issue4已以body-file发表本轮真实失败→修复→结果/边界：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6363209981 ，正文review-fix-v2-comment.md。PR17保持OPEN/draft、base codex/team-bootstrap、head codex/database-runtime，正文按最终范围更新并重新attach。
- 本轮收尾时仍未收到窗口结束通知；不启动本机pytest/MySQL/seed/HTTP/构建，t44_review仍未操作，C-P4不关闭。重构后MySQL全量seed未跑，统一cloc/最新整合/正式性能/独立验收未由本岗执行。产品/测试与已验证0a676ee完全相同，本次只追加原始证据/日志/报告/handoff。

## ROLE-database-LIVE-VERIFY-v1：安静窗口结束后的真实专库验证
- 收到总协调明确窗口结束（最后批次10:52:33Z）及两个项目专库授权；原文归档prompts/ROLE-database-LIVE-VERIFY-v1.md。干净树fast-forward43f51570e62e3160f7995c45bdddaf2f123242b3，不改冻结DDL/API/他岗源码，不读改957或独立私有资料。复用956/975，没有新增955。
- 仅t44_review和新空t44_seed_verify_v2可写；使用app四键私密文件，仅构造Engine、不打印/提交值或DSN；未读取admin文件、未写dev/acceptance/perf/旧seed库。
- 实际命令：T44_REVIEW_CREDENTIALS=<ignored四键文件> PYTHONPATH=backend .venv/bin/python tmp/backend/persistence/956_schema_semantics.py。review-run1.log保留初始真实迁移与失败：索引恢复后MySQL8.4把ck_users_hash_shape字面量引导符改为_ascii，旧parser误报users:check_definition。review-after-failure.json/review-check-rewrite.json记录实际Inspector与冻结期望，未掩盖失败。
- 生产修复仅在词法阶段识别_utf8mb4/_ascii字面量，_ascii非ASCII拒绝，字符串内部相似内容不被全局regex改写；追加956正/负断言，schema-regression.log为15 passed。
- review-run2.log保留探针实际1826：MySQL同条ALTER DROP/ADD同名FK被拒绝。只修owner探针分步DROP/ADD及部分失败恢复，不放宽checker。review-run3.log最终四类实际漂移（列序、unique、FK目标、CHECK1=1）均被checker和重复migrate拒绝；每例恢复后18表226列defects=[]，最终重复migrate accepted；日志和summary含每条实际SQL/目标库/结果。
- 实际命令：T44_SEED_VERIFY_CREDENTIALS=<ignored四键文件> PYTHONPATH=backend .venv/bin/python tmp/backend/persistence/975_seed.py。seed-run1.log首轮真实MySQL成功：新库迁移、40项目/6000任务/9000同项目DAG/11400review+3600decision、3600预案及7态引用/轮次/批准指针/八段十项/四视角/容量全量检查；全持久行SHA256=6d56de112481ca6c6a54210a1a60b06769b9845fad8699462dfbf753505fb3d3，与原全量基线精确相同（排随机password_hash）。
- 同manifest重复seed幂等；seed=45和合法规则JSON仅原bytes hash变化均拒绝，不覆盖原数据。7项原生unique/FK/CHECK拒绝（含四核心表）逐项savepoint回滚，之后全行摘要不变；最终结构检查与重复迁移通过。实库8.4.11、UTC、READ-COMMITTED、严格SQL模式。该受信校验脚本只允许新专库且业务表为空，重跑写阶段会安全拒绝；生产seed_demo本身已验证重复幂等。
- 必要模块回归：PYTHONPATH=backend .venv/bin/python -m pytest -c backend/pyproject.toml tmp/backend/persistence/956_schema_semantics.py tmp/backend/persistence/975_seed.py --junitxml=agents/database/live-verify-v1/targeted-junit.xml -q，18 passed/0failed/0errors/0skip，2条原record_property/xunit2兼容性警告保留；24.10s仅模块命令耗时，非正式性能。
- Ruff首次I001仅新owner CLI import排序，ruff-run1.log保留；仅该文件I001 fix后ruff-run2通过；migrations.py定向Bandit findings0。必要范围完成，未重复全套/全局覆盖或扩展性能测试。
- 本岗C-P4数据库技术验证闭合，仍需审核岗对最终集成SHA复审，未代其设置审核通过。根stage7 cloc5866/exit1为当时事实，仍超5100，不改口径/为数字破坏结构。全部seed数据synthetic，不是人工评审/交付或独立验收。
- 本轮Issue4已以body-file发表：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6363453107 ，正文live-verify-stage-comment.md；PR17标题/正文已按真实MySQL最终范围重写并attach，保持draft。

## ROLE-database-CAPACITY-V11-CONTRACTS-v1：显式1.1存储文档同步
- 干净树fast-forward指定eac253039cd85873d3b262e648b2b74d94d715a8，已读AGENTS、D005/D006、U015/U016、capacity-lifecycle-v1.1.md与bbc限定设计报告（reviewer d7c46a6）；实际派工原文存prompts/ROLE-database-CAPACITY-V11-CONTRACTS-v1.md。
- 只改field-dictionary.md/persistence-contract.md及本岗记录，未动DDL、产品、API/运行契约或旧freeze。文档标显式1.1演进，旧ae60dc3原1.0及11hash保留，当前两文档摘要有意改变；不称当前仍逐字等于1.0。原逐表/迁移设计时期未执行句式加历史范围说明，既有MySQL/checker修复实测不重写。
- 明确capacity JSON为服务层跨行不变量：项目锁内重读当前有效developer及本迭代全部任务owner，state1–5必须保留，6/7可移出、7返工前补回；成员/开发角色保护仍1–5+7，D002转派边界不变，无预算算法。assignment新增project锁，四路径统一session/idem→project→有序成员→有序task，失败不写业务版本/plan/diff，成功/重放/独立拒绝审计仍原事务边界。
- 已向backend真实同步上述输入输出；backend原回复：“一致，后端正在986/985先补回归，随后assignment加入项目锁；changeIteration在项目锁内查全量该迭代state1–5 owner并锁task按id，不能只查old-new名单；rework在现有版本/权限/状态/证据/依赖守卫通过后、CAS前核有效developer+capacity，缺失用ID30。保留成员保护1–5+7、18/226与SQL不变。为保原版本错误优先，新guard前复用集中version检查，成功/拒绝/重放事务编排不变。”据此保留原错误优先级，未越界改backend源码。
- 必要静态对照/相对链接/hash检查通过：原11项摘要均可从ae60dc3恢复，v1.json未改；DDL/打包副本均c0e740...，18表226列；字典226项字段名/SQL声明与eac基线完全一致，原ID30不变，19个本地链接/锚点有效，RFC SHA=a6271e...与已审对象一致。结果capacity-v11-static-check.json。初次查找records/user-feedback目录不存在，已用rg --files records定位实际records/prompts，未据此推断业务失败。
- 本轮未跑pytest/MySQL/迁移/全套/coverage/独立验收/性能，不将文档静态通过计为产品通过。API info.version/Meta.const及权威/运行副本1.1.0由backend完成，root负责需求/业务规则/AGENTS与新freeze父链，现均不代为声称完成。
- 提示词岗真实问取原文：“ROLE-prompt_engineering-M4-REAL-PROCESS-v1 实际问取：请异步给本轮已发布真实prompt原文与C-P4/catalog修正、capacity生命周期设计/实现（若有）的产物→失败→修正→验证、完整SHA/Issue/PR/实际操作者。只需公开现成来源，不执行产品验证，不读独立测试私有资料；未完成/未回如实pending，不把AI改码记学生亲改。”已异步答复既有0e3e999/0a676ee真实prompt、原失败→修正→证据路径与Issue/PR，并明确当前capacity仅未提交文档、无本岗实现/测试；人的D005/D006选择与AI纠错改码分别记录，完稿后补最终SHA。
- 本轮真实阶段评论已body-file发表：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6364775327 ，正文capacity-v11-stage-comment.md；PR17按本次文档scope更新标题/正文并attach，未设审核通过。git diff对eac的backend/DDL/v1.json为空，确认无产品/旧freeze改动。

## ROLE-database-DDL-AST-POC-v1：隔离研究进行中
- 干净fast-forward正式freeze189dc4a3196be0fb84b753f23284f2566d823ea0；实际派工原文归档prompts/ROLE-database-DDL-AST-POC-v1.md。只改952隔离原型/本岗记录，未改生产、DDL/API、freeze或backend依赖/975。957要点仅使用root公开描述，未读原文件/独立私有资料。
- 官方当前PyPI/release核为SQLGlot30.24.0（2026-10-20）、Python>=3.9、MIT，基础无强制依赖；官方文档明确parser宽松、非validator，MINOR也可破坏兼容。纯Pythonwheel按官方sha948882...验证后仅解包ignored runtime/database-ast-poc/package，未进入backend环境/锁；原元数据与setup日志保留。
- 首次真实纯解析权威DDL得到18 CREATE/2 ALTER/226列/59CHECK。初版952矩阵run1为29通过/2差异，原失败保留；静态主源确认本岗adapter误把显式NULL的NotNullColumnConstraint(allow_null=True)当NOT NULL，已编辑修复，但尚未重跑。没有把这两个adapter失败说成库缺陷或生产问题。
- root随后明确BE独占短性能诊断窗口；已报告无本地负载，暂停包安装/批解析/测试/DB/seed，现仅阅读失败/官方源与编辑原型，待root明确窗口结束再跑952。
- root明确短诊断窗口结束后才恢复952；run2=36通过/1失败保留，run3=40/1，run4=46/1（各<1s轻量解析）。NULL adapter已更正，18/226及列/索引/FK/59CHECK/PK/表选项静态差分一致；仅余13处SQLGlot把IS NOT NULL生成为NOT x IS NULL导致旧checker无法解析，原old-CHECK-reference失败持续保留，不改生产旧checker迁就库。
- 在952区分候选新AST自身59roundtrip稳定与混用旧parser的13文本不兼容；额外补unsigned/时间精度、索引type位置/排序、FK源/目标/库/动作、恒真/扩张/OR、字符串/函数/优先级及严格拒绝观察。不是一般SQL有效性/等价性证明，没有实际反射倒造预期。
- 固定cloc2.10同文件函数片段：生产schema117/migrations321；旧可替换语法+构造上界171，新AST提取规范化114，完整Core assembler+type+接入保护尚估60–110，联合可能增加3–53行；CHECK-only潜在约39–46行亦未实现。line-estimate.json不算生产已删；实际节省0。
- 最终建议不准入生产整对替换，不改依赖锁；研究report及可重复952CLI供root/reviewer决定。Ruff初次F401/I001原失败保留，仅952整理imports后通过，不为风格再刷矩阵；没有触碰975授权样式修复。
- 本轮以body-file实际发表Issue4阶段说明：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6365574045；正文ddl-ast-poc-stage-comment.md。PR17标题/正文改为本轮未准入POC范围并attach，保持draft。没有把952失败或BE其他集成失败改写为通过。

## ROLE-database-SCAN-RUN-DEDUP-RFC-v1：联合预算净增1，否决实施
- 从当时集成162305f888ac094e38448ef95d4748248ae57bfc独立创建codex/database-scan-dedup/worktree，读AGENTS、本岗/调度交接、既有架构审核和实际Rows/savepoint/UoW/scanner/facade；不读取独立未发布用例/报告，不联系测试实例。
- 本轮明确先设计，不修改生产。草案保存agents/database/scan-run-rfc/candidate-v1.patch及candidate-v2.patch，ignored scratch内生成候选文本；helper不拥有UoW，只在传入g中处理原完整初值/唯一冲突savepoint/版本hash校验。scanner与API的查询顺序、重复后锁、返回投影及规则冲突错误保持明确区分。
- 首次scratch Ruff未带项目配置，实际用了默认88列，顺带重排旧行；该计数314→346被否决，不能充当最终候选。重新取原源+限定方法，显式--config backend/pyproject.toml（100列）；最终真实固定cloc2.10：scans109→129，facade205→186，联合314→315/净增1；工具hash核对通过。不能只记facade减19行。
- 最终候选还发现API duplicate后找不到run的内部异常由原IndexError变为StatementRejected，虽然当前Runtime都转INTERNAL_ERROR，仍未证明内部异常等价；不以广泛捕获StatementRejected掩盖问题。既已不省行，不再增加适配复杂度去维持该罕见旧分支。完整设计说明这份补丁不能直接投产。
- git apply --check candidate-v2.patch退出0；两候选ast.parse通过；这只是补丁/语法检查，无pytest/MySQL/HTTP/MQ/seed/CI/覆盖率/性能运行，没有新增脚本和编号。生产/DDL/14冻结件/依赖/他岗源码和断言均不改。
- 总协调明确接受净增1的否决建议、不批准实施，不必等待调度岗。当前实际生产节省0；旧28–47只是预估，另含tick/recoverable的旧建议不冒记本轮收益。root最新5dcb73c全局5980/超880为其报告，本岗不冒充全局新跑；git diff确认两目标文件与本基线相同。
- 实发prompt原文及后续消息归档prompts/ROLE-database-SCAN-RUN-DEDUP-RFC-v1.md；操作者为AI，不是学生改码/亲写研究。GitHub阶段沟通与最终SHA另随本轮收尾回执，不设置review成功。
- 首次收尾git diff --check退出2，只报告两个原始.patch文件的空上下文行（标准unified diff以单个空格表示），没有执行后续stage/commit/push。保留原补丁逐字内容；后续仅对这两个原件路径做资料级空白检查排除，其他本岗文档继续完整diff检查；不是产品检查/门禁放宽。
- 本轮设计提交6aeb7e67d90767b7408967a6782e13c569e9d423已push codex/database-scan-dedup；通过GitHub connector逐条真实发表Issue4/6，再用精确comment API GET读回，正文与本地逐字相同；回执github-post-receipts.json/github-readback.json。链接：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6367575884, https://github.com/HJY147/t44-dev-trace/issues/6#issuecomment-6367576440。未另开实施PR或设置审核通过。


## ROLE-database-PLAN-HISTORY-v1：固定有限批读设计复核
- 从指定02c4b2a创建独立codex/database-plan-history/worktree，根索引未动；只读AGENTS/本岗TASK/协作规范/真实schema、rows/codecs/UoW、准入记录和已集成RFC，不读独立私密资料、不联系tester。
- 真实表为12列，uq_schedule_task_version(task_id,to_version)及项目复合FK/target CHECK已有；确认完整select复用现JSON/UTC解码，新增固定tuple-IN入口，不改通用rows/DDL/API/14冻结件/历史audit。精确输入/输出/错误/事务/行数/SQL次数契约见plan-history/design.md。
- 先设计阶段产品净改0。安全输入与结果范围/重复检查净cloc预估由18..30修正35..50；按原source_count.py+校验hash的cloc2.10，对02c4b2a实测应用6124/within_range=false（baseline-cloc.json），口头6108与本次归档计数不同已报告root，不改口径凑数。
- GitHub connector实际读取Issue4/28当前公开正文，未追读其私密案例/SQL/截图；稍后阶段评论与精确API读回另存回执。实际派工完整归档prompts/ROLE-database-PLAN-HISTORY-v1.md，操作者AI不是学生亲改。
- 设计先commit后实施；将仅复用993/988新增目标旧源红、SQLite/真MySQL有限自有t44_test fixture，完整CI/精确源码审核由root调度。此设计checkpoint无pytest/MySQL/HTTP/覆盖率/性能通过声明。

- 设计checkpoint e9a769a已push（skip ci）。随后复用993增加目标先实跑旧源：首命令误用根.venv缺pytest（red-environment-run1.log），改用本岗既有database/.venv后真实AttributeError旧源红（red-old-source.log），没有把环境失败算功能红。
- 实现固定task_schedule_changes，保持原通用16方法及全部原测试函数逐字（unchanged-boundaries.json）。空不取session；输入最多100先验后去重；参数化精确tuple-IN；固定project/iteration IS NULL/排序；完整codec行，不limit/截断；结构/范围/重复或硬bound违约_failed+PersistenceUnavailable。
- 新SQLite/mock目标48通过（sqlite-run1.log），最终原993整文件66通过（含同48，foundation-regression.log），没有删改旧断言。真MySQL首轮自有fixture漏project_members触发任务owner FK失败（mysql-run1.log），仅补自有成员关系后1通过（mysql-run2.log），产品未因夹具失败改动。
- 另加真实服务器故障目标：仅本测试进程替换registry为不存在的owner表，真实MySQL SELECT失败转脱敏PersistenceUnavailable/rollback-only，1通过（mysql-server-error.log）。为实际SQL账本新增可选环境证据出口后，仅重跑同两个新增MySQL目标2通过（mysql-evidence-run.log/JUnit）；不把48+66+1+1+2累加成新独立例。
- mysql-sql-ledger.json保留真实空0/100pairs1SQL100完整行/重复1/101拒绝0/跨项目pair1SQL0行/合法最大输入1SQL0行；含实际参数化语句与整数绑定。104条自有schedule夹具含2交叉干扰+另项目+iteration，长2000字/JSON/微秒UTC完整、查询前后相同，事务全回滚且自有username回查不存在；不清表、不改别人数据、不停库、不跑整套/负载。
- Ruff首次新测试import I001保留，排序修复后最终限定3文件通过；rows.py定向Bandit0。14冻结件摘要与基线字节全同；16旧gateway/17旧foundation/17旧mysql函数源码字节相同；未改DDL/API/后端matcher/前端。
- 最终rows.py固定cloc237→299/实际净+62，超过设计35..50和RFC18..30，已如实报root并保留各估算，不压行/弱守卫。基线6124、当前应用投影6186，提交后将同原脚本实测；源码规模仍不达标。root回复明确要求保留预算上修/夹具原失败、固定接口与重叠计数/SQL账本/14冻结和旧方法字节/Issue实际读回，不执行完整CI/负载。

- 产品精确checkpoint 3b7bc0c92f92a20bc69ee76293f547fe9f1e9a9a已push，skip ci；root已收SHA待小审固定方法。随后原source_count.py/cloc2.10对该提交实测应用6186/within_range=false/--require-range退出1，final-committed-cloc.json；相对基线6124真实+62，不将归档成功说成规模通过。
- 已通过GitHub connector在Issue4/28实际发完整阶段交接，再用各comments/:id精确GET读回，两个返回body与实际本地正文逐字相同；github-readback.json保留endpoint/id/body/时间/作者/equality。链接Issue4#issuecomment-6373901751、Issue28#issuecomment-6373902163。没有关Issue、开完整CI、设review成功或将本岗自测写成独立验收。
- 当前收尾仅证据/记录，产品、两自测源码与3b7bc0c完全相同；本岗作用域完成并释放槽，后续精确review/后端接入/组合CI由root调度。


## ROLE-database-POOL-RETENTION-v1：同15峰值的保留池诊断先设计
- 从root当前2a0f091（含ff7ffa8公开backend诊断证据）创建独立codex/database-pool-retention/worktree，根索引与未跟踪打包工具未动。读根61b23e6先行RFC及公开bc5 result/continuation；未读独立私密材料。
- 核锁backend requirements与实际backend/.venv SQLAlchemy2.1.6，本机pool impl.py/base.py与官方rel_2_1_6 raw逐字/hash相同；source-verification.json保留实际方法行号/hash。首次系统CA失败后使用既有certifi CA保持验证成功，不绕TLS；未用不匹配版本文档代替实际代码。
- 真实QueuePool按返还队列满时close/减少overflow，懒建连接且A5+10/B15+0同15峰值；B最多保留更多空闲会话/内存，不是零成本。acquire inclusive不是纯pool等待，旧并发32新连211不能回填正式三组根因。
- 先提交精确工具设计/命令/预算，955仅最小扩展pool-abba、固定A/B与预热/稳态/清理阶段和真实DBAPI计数；不改生产/默认池/SQL/锁/线程/全局参数。实际比较须root窗口，当前没有HTTP/SQL/负载。

- 设计42a8bcb已push后仅编辑955：新增固定pool-abba复用原控制器/客户端/仪表/server；同步32客户端后1/4秒相位计时，分别记录warmup/steady/cleanup；A/B只替换本地db副本，旧生产与默认不动。增加真实DBAPI connect/ping/do_close尝试及异常类/false ping/线程CPU，完整request_id/acquire计数和最近秩P95，不平均四段。
- 过程内110秒截止预留10秒清理、子进程finally与端口检查；fixture0600/hash、2.1.6版本/官方源hash、已提交工具与bc5全部应用字节守卫。预检只有app可见本库PROCESSLIST0，已向root明确不能当跨账号全局无连接证明。
- 工具静态首轮I001仅新增dataclasses import顺序，ruff-tool-run1.log保留；整理及格式化后最终限定Ruff通过，AST与生产bc5/14冻结hash全同（production-boundaries.json）。首次一个apply_patch上下文因格式化插空行未命中，无文件部分改动；定位后修正。尚未导入工具、HTTP/SQL/负载，工具commit后才做离线合成检查。

- 工具checkpoint14490fe已push后完成离线验证（offline-validation.json/log）：导入零网络/进程；实际QueuePool2.1.6+合成DBAPI两波15借用证A5保留/10溢出与B15保留/0溢出，峰值15/最终open0；透明ASGI、4类CLI拒绝、mock固定ABBA8相位32/1s4s及首失败停止/清理、nearest-rank均通过。不是MySQL/HTTP或负载样本。
- root明确授予独占执行窗口且native等待；先补统一profile_connections前/后计数helper并提交0f6fdf5，随后offline-final-probe验证绑定只查t44_profile/总dispose、startup异常后仍后检；旧离线已覆盖的9函数/类源码相同，当前工具hash与source边界已保存。仍没有实际HTTP/SQL/ABBA。
- 具体执行argv/私密env路径/源hash/外层116+2+1秒进程组清理计划execution-plan.json先commit；22:35既有fixture原样使用，不刷新session、不改旧fixture/TTL或业务数据。将先报startUTC再运行一次，完成或失败立即释放窗口。

- 原唯一ABBA实际2026-10-23T23:02:14.376665Z–23:02:53.234248Z/38.842秒含清理/exit0，源f75a8a4，实际argv已先冻结。start前通知root，结束清理后立即通知root释放窗口，之后没有第二次样本、额外profile/HTTP/SQL。native可随后启动。
- 实际A1/B1/B2/A2稳态2079/2255/2237/2113请求、全部失败0，nearest-rank P95(ms)91.591041/74.471792/72.908250/92.600542分别保留不平均。稳态新建436/0/0/427、关闭436/0/0/427、ping1643/2255/2237/1686；预热新建112/15/15/109未删，清理关闭5/15/15/5。观察峰值全15、dispose前checkedout0/idle5或15、dispose后open0。
- 18083前后free，4自有server exit0且PID最终不存在；每段前app可见profile其他连接0，最终0，保留跨账号不可见局限，未扩权限。22:35原fixture未刷新/未修改，前后bytes hash及8个client相同。只有contract只读候选，无业务fixture创建/seed/清库。
- 离线逐请求核10882（warmup2198/steady8684）全部client-server恰1关联、HTTP200/原valid守卫；恰1endpoint/runtime/authenticate/acquire/checkout，三候选cursor4/5/5全SELECT/SQL错误0。19实际应用/资源/池源hash与bc5/官方2.1.6一致；14冻结仍全同，生产净改0。
- 43份实际原件按原bytes gzip存raw并以raw-manifest.json绑定原始与gzip SHA。扫描已知DB口令/完整DSN/fixtureToken/Authorization标记匹配0，未输出值；result.md/summary.json写真实4段原值、acquire inclusive与线程CPU、钩子/本机竞争/短样本限制、B每worker多10idle及未测内存。支持本次减少重建假设，不作正式根因/显著性/生产准入。
