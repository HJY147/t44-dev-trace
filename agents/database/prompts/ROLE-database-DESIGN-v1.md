# 实际数据库设计派工归档

ID：ROLE-database-DESIGN-v1。发送者/决定者：AI总协调。实际执行者：数据库岗位AI。下文为本次实际派工原文，不是用户原始提示词或优化版，不计作岗位初始化提示词演进。

> ROLE-database-DESIGN-v1：用户已采用业务规则并要求继续开发。现在由你负责数据库完整设计（本轮不迁移，不写模型代码，不碰根 Git 索引）。项目 /Users/yang/Desktop/nothing/软件开发大作业；Issue #4；固定岗位规则仍适用。读取 AGENTS.md、specs/requirements.md、specs/business-rules.md、records/decisions/D001*、D002*、原始 specs/sources/T44-taskbook.txt、当前 docs/reviews/review-protocol.md 及 backend 已有设计草案（不存在则向 backend 要接口字段）。技术 Python3.12、FastAPI 同步、SQLAlchemy2/PyMySQL、MySQL8.4。交付 specs/database/field-dictionary.md、schema.sql（完整可执行 MySQL DDL，但本轮不执行）、persistence-contract.md，重点四核心表逐表类型/约束/索引审查，统一 PK；枚举 tinyint；额外用户/项目/成员/迭代/排期diff/审计/幂等/outbox/通知/扫描表按必要性定义。以最小可实现设计为准，避免无需求膨胀。明确成功变更+审计+outbox一个事务；拒绝主事务先回滚后独立连接记录且审计失败503；相同幂等key并发唯一性、不同key同version CAS只能一次；扫描 unique(task_id,schedule_version,level)；消费 unique(event_id,recipient_id)；MQ confirm和fallback事务边界。review轮次/交付轮次与排期版本分开。与 backend 直接交流字段，真实问题/确认通过 Issue 评论（本地正文 body-file），不要联系测试。保持自己的日志/报告/handoff，归档本次实际任务提示词。完稿发我设计路径、待审事项、与 backend 的确认，明确未执行DDL。根索引现在仍由文档队列控制，不 add/commit/push/checkout。

实际追加指令同属本次设计任务，不冒称新增用户决定：

- 同项目依赖变更须project行锁串行，避免A→B/B→A并发成环；明确开始/解除依赖检查与task CAS锁序；成员撤销守至少一经理和活动任务责任人；直接告知backend。
- level从固定1/2/3枚举扩成tinyint范围1..255、实际有效值由版本规则清单决定；v1阈值与3级不变，不授权第4级。模板item改形状+版本清单，避免新增规则/项要求改DDL；规则原文/hash/生效/决定者可追溯。
- 账号初始化真实持久层入口拒绝非合法Argon2id hash，独立记录脱敏安全审计，失败503；DDL形状CHECK不能独自证明已记录。CLI口令哈希后调用入口是正常路径。
- 收到总协调续作：从已写schema/contract继续，不重做/换模型/扩编；优先字段字典、backend最后确认、真实记录及DDL静态核查，不执行、不迁移、不碰根索引。

产物对应：三份specs/database设计；本岗日志/报告/handoff；本岗Issue确认正文；静态自查原始结果。改进原因：在用户已采用业务规则后，将M0未冻结字段域收敛成完整可审设计；真实迭代包含会话撤销、锁序、版本/幂等与可扩展规则边界。AI所改不记为用户亲自改码。

## 同轮归档派工原文

后续实际派工ID为ROLE-database-DESIGN-COMMIT-v1；这是对已有设计的Git归档授权，不是业务设计迭代。总协调指定commit footer继续引用ROLE-database-DESIGN-v1。

> ROLE-database-DESIGN-COMMIT-v1：backend刚提交 b893353c9bcf45e833f70f56bf6f72025f611271 并明确释放根索引，现仅你获根索引独占。请仅归档已有设计，不扩展新设计：核对正确分支codex/team-bootstrap及空暂存区，显式add specs/database三文件、本岗agents/database设计日志/检查/任务归档/评论、reports/modules/database.md、records/handoffs/database.json；绝不加root共享台账/D003等文件。核对最新接口/会话锁序已一致即可，保留原失败。commit footer Agent-Role: database、Prompt-Ref: ROLE-database-DESIGN-v1、Refs #4 #13。Issue#4已有真实设计评论可补充本次提交范围/待审核，正文body-file保存。只commit不push/checkout/merge，不执行DDL不宣布审核。完成尽快返回完整SHA、评论、文件清单、真实自查/未验证并释放根索引，结束本设计轮。后续我会给你独立树编码任务。
