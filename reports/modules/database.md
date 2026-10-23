# 数据库模块报告：恢复与合成数据交付

## 当前范围
- 岗位database；实际prompt ROLE-database-RECOVERY-SEED-v1，沿D004/v1冻结实现；初始化TASK限制已被总协调后续实际派工更新，旧日志保留当时事实。
- 独立树.agent-worktrees/database / codex/database-runtime；产品checkpoint 9aeb69795f67239b04352125f4b7db0427ce1272，PR17仍draft，未宣布审核或独立验收通过。
- 18表226列Core元数据、真实迁移、受限Rows/Pred、hash-only入口、outbox/通知与持久scan已实现；本轮补confirmed恢复、claim公平性、生产seed。
- 未改冻结DDL、共享锁/pyproject/其他岗代码，未接触独立testing资料；只merge总协调12f7141获取实际CLI与真实资源。

## 入口与事务
- backend/t44/persistence/README.md列精确签名；migrate(engine,expected_database=...)只初始化明确项目空库并核版本/摘要，重复不破坏数据；技术版本表为非业务例外。
- factory每次独立Session；每新连接UTC/严格SQL/READ COMMITTED，正常commit/失败rollback/总close。CommitUncertain保留，cleanup不证明未提交。
- Rows支持固定表列、绑定值、查询/分页/锁/CAS/update/delete/count/savepoint，以及同形参数insert_many/update_many；未知标识符/表达式/无where写拒绝。
- session→idem→必要project→members user_id→tasks id→children锁序不变；依赖变更先项目锁串行查环。成功业务/audit/outbox/idem同事务，拒绝先主UoW释放再独立审计由backend Runtime编排。
- 已移除无生产调用的CoreGateway/TableBinding（105行）及可选IdempotencyStore（124行）；原断言迁实际Rows/Runtime，不删功能或弱化测试。
- 新owner接管换token必须fence旧worker；纯租约到期不自动新增业务拒绝，已按root澄清撤回早先缺陷推断，未越界改服务。

## 消息/扫描实际对接
- recover_confirmed(*,confirmed_before,now=None,limit=100)由固定MySQL JSON_TABLE+NOT EXISTS先排除完整旧事件，不占候选limit；同event锁内复查，仅真补缺才3→4。
- consumer/fallback/recovery沿相同事件锁序，完整消费保持confirmed，原通知已读/处理不改，旧token为stale_owner、迟到confirm不能回退。
- claim公平性先真库复现旧低ID事件反复retry致后升级3轮饥饿，再改pending next_attempt_at,id / leased lease_until,id；沿已有索引、SKIP LOCKED和token fencing，不改DDL。
- ScanStore start/get/recoverable/page/checkpoint沿UUID唯一、规则快照、固定cutoff、单调游标；升级/游标分事务靠唯一(task,schedule,level)重扫去重。
- MQ本人已接线并实际cherry-pick恢复；直接交1602f3597408d3b477dd9ef55a33145565556e12与8b60b7146f6bb33a850be697edb39995347f5c14；接口未改签名。

## 生产合成数据
- seed_demo(factory,*,projects=40,tasks=6000,dependencies=9000,records=15000,manager_username='synthetic-manager',seed=44,anchor_at=None,template_path=None,rules_path=None,batch_size=250)；真实backend CLI seed-demo已接线并执行退出0。
- 新t44_bench真MySQL首次迁移/250批单UoW生成40项目、6000任务、9000同项目DAG依赖；11400review+3600decision=15000，预案另3600。
- 七态6=2400，其余1/2/3/4/5/7各600；全量JSON模型、八段十项、四风险视角、轮次/批准指针/决定引用、自审身份分离、依赖父已交付且时间先于后继、人力容量核验通过。
- 模板raw SHA256=4fdaad483abe00a41335546f11dda58f8b87da66cf5d158521c24c125d99f199；规则raw SHA256=279c55934adf59362cb0119e59f8ca41aeb826611fabafb7f006d0000bdb8720，来自实际配置，不编造占位hash。
- 返回seed/version/anchor/配置hash的manifest_sha256；这是生成描述摘要，不冒称整库内容或随机密码hash可重现。重复同描述幂等、不同seed拒绝，无删除覆盖。
- 所有对象及证据明确synthetic，SYNTHETIC-DATA.md说明不代表真人评审/真实交付；函数无明文密码参数，新账户只持久合法Argon2id hash，不输出秘密。

## 真实执行与边界
- 官方MySQL8.4.11 app权限；test用于恢复14项回归通过，bench用于真实全量生成/校验、Runtime和公平性；未动acceptance，未清空dev/test。
- 恢复首轮2失败12通过源于共享库旧缺通知影响夹具断言；原记录保留，隔离confirmed时间窗后14通过，不删他岗数据。公平性修前真实失败/修后通过各自归档。
- 当前Rows迁移后的原18基础断言+3Rows+2seed共23通过；实际Runtime同key并发/接管/旧owner/final-request/冲突真库回归通过。不同批验证未合称最终SHA单次全套通过。
- 实际全量生成3.781s、增强一致性核验24.014s仅模块执行耗时，非正式性能结论。真实CLI重复入口exit0、不同seed拒绝；日志seed-mysql-bench-run1/final.json。
- Ruff final退出0；SQLite仅可移植夹具/生命周期、mock仅连接初始化，不能代替MySQL约束。CI双环境保持DATABASE_URL+T44_DATABASE，缺配置fail不skip。
- cloc2.10按公开政策核9aeb697应用4582行，本岗持久Python1500行；此树仍旧FE且未全量MQ，不替代最终整合总计，未调整格式/统计口径凑范围。
- 未运行本轮最终全局suite、RabbitMQ网络、全局覆盖率、正式压测或独立验收；下游/总协调须在最终整合SHA实际执行，不能用本岗模块证据代替。

## 记录与交接
- 日志agents/database/WORKLOG.md，实际prompt归档ROLE-database-RECOVERY-SEED-v1.md，交接records/handoffs/database.json；AI实际改码与用户采用方案分别记录。
- 实际Issue4恢复回复6360999718、公平性回复6361197315；seed最终正文seed-stage-comment.md已发表，具体URL见交接。
- 本岗实现/模块验证已交产品checkpoint，后续等待根整合、最终规模和运行门禁结果；不联系独立测试或发审核成功。
