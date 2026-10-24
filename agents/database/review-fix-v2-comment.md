Agent-Role: database
Prompt-Ref: ROLE-database-REVIEW-FIX-v2
Refs: #4 #13

C-P4检查器修复保留冻结DDL/API：比较同名索引的有序列/unique/排序/前缀、FK源目标及动作、CHECK优先级/字面量/函数参数。旧问题为checker错误接受，未据此声称已有实库漂移；未读取或修改审核957及独立私有资料。

真实失败链：3ed的39938428158/39938417442均为Bandit B105把局部变量token与'('比较误判硬编码口令；原始job/artifact/hash归档agents/database/ci/review-fix-v2。958只改名lexeme，无nosec或门禁/断言削弱。4301a68托管39940121559四job success，332passed/0failed/0skipped；2dc2e6d/39940459708四job success，333passed/0failed/0skipped，新增默认40/6000/9000/15000组仍用原全部业务断言。

生产seed公共受信row-builder在0a676ee6f7c287893153cdca0c6c6823aacca8a1：集中时间/外键上下文、复用NULL指针、采用既有冻结server defaults；业务配置、7态/轮次/容量/八段十项/四视角/证据标记、真实配置hash/manifest和绑定批量单UoW保持。将原真实小/全量持久行摘要作为额外断言，只排除随机Argon2 hash；回归预先按task分组等价校验，条件不变。

新版结果：0a676ee的PR product39941263169及push39941255427均success。原始JUnit确认333 passed/0 failed/0 errors/0 skipped；小/默认全量的固定持久行摘要均精确相等，Bandit零命中、Ruff通过。原证据存agents/database/ci/review-fix-v2/0a676-result，不能把该托管结果替代专库实际漂移恢复。

当前边界：同机正式性能安静窗口尚未获结束通知，本岗未跑本机pytest/MySQL迁移/seed/HTTP/构建。t44_review受控真实结构改动/错误重复迁移拒绝/恢复接受仍未运行，C-P4不标闭合；新版真实MySQL全量seed也未跑。托管/SQLite摘要不替代这些验证，数据全为synthetic，非真人或独立验收/正式性能证据。Git seed净减27物理行非最终cloc，已知全局仍超5100，未称规模达标；PR17保持draft。
