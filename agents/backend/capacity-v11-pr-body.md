后端提供38个冻结HTTP操作、严格JSON Schema、opaque会话撤销、状态/证据/预案/决策及UoW幂等/CAS/审计/outbox。按D005/D006与189dc4a正式1.1冻结实现容量生命周期：转派接手人先有本迭代工时，capacity覆盖全部状态1–5 owner，6/7可移出、返工前补回有效developer与capacity。成员保护1–5+7、原错误优先级及写入事务原子性保持。

本阶段在设计-only父3187后，仅Runtime净+7行把validateContractPayload实时鉴权、原输入校验、fresh-now到期复核和原业务读取合并一个UoW；默认RC非锁定读、在途可完成/撤销后新请求拒绝。其它17只读、全部写入claim/锁/CAS/幂等/审计/outbox及14freeze未改，不缓存身份、不调pool、不删Schema。完整设计/实际选择和未应用原patch保留于specs/changes/contract-validation-read-uow-rfc.md。

新定向18项通过（HTTP/SQLite11、真实MySQL7），改前新目标9fail/9pass原件保留。三类别实际4/5/5SELECT、各1acquire；真实session/member撤销两种先后与新请求401/403、认证先于输入、fresh-now优先和退出UoW后的独立拒绝审计均有回归。故障注入明确限于模拟依赖/审计异常，未冒称实库宕机；原断言未删改。Ruff/format/Runtime Bandit通过，read-uow-validation-summary.json可追溯。精确新源5dcb73cc10c38deb14fae68d33318b04d538fecf的product39970988113已全success：412项/0失败错误跳过；contract114/integration70/fault11（可重叠），全部43个t44文件、excluded0，行2550/2872=88.7883%、分支78.7371%。原coverage/JUnit/metadata见read-uow-ci-*；旧4c20的394只属历史源。

工具245的隔离单worker短诊断18289主样本+3sanity有效，但整体controller最终RuntimeError/exit1仍保留；修工具后仅离线检查，未重跑矩阵。新UoW实现没有延迟收益数据，原400VU/600s/4worker正式性能、transition/escalation P95、独立复测及3500–5100源码规模尚未通过。PR保持draft，不self-approve。

Agent-Role: backend
Prompt-Ref: ROLE-backend-CAPACITY-V11-IMPLEMENT-v1; ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1
Refs: #3 #12
