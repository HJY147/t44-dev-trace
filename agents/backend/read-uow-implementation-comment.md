岗位 backend；Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1。

先提交设计父3187bc6615a821f1123ef10f64d99b7a39a9862d，经限定设计审阅及根准入后，才仅runtime.py净+7行实现validateContractPayload单UoW，不新增只读S锁/池调整，不改14freeze、其它17只读或写入claim/锁/CAS/幂等/成功与拒绝事务。每请求仍实时查session/user/member/project，fresh now复核点有效；在途普通读允许完成，撤销提交后的新请求必须拒绝。

新定向回归改前9fail/9pass（新优化目标/在途语义断言，不是旧产品9个业务缺陷），改后18pass：986 HTTP/SQLite11、985真实MySQL/t44_test7。真库3类实测4/5/5 SELECT，各1acquire，成功无业务/audit/outbox/idem写；session/member先撤销后新请求401/403，及已鉴权读暂停→实际HTTP撤销先提交→旧读有效200→新请求拒绝，事件屏障证明无新S锁。另验认证先于非法JSON、fresh-now/参数优先、主UoW已closed后独立新Session审计及审计失败503；故障是明确注入，不称真宕机。原断言仅追加，before/after日志/XML全部保留。

受影响文件Ruff/format、Runtime Bandit通过；证据agents/backend/read-uow-validation-summary.json和read-uow-*-{before,after}.*。本轮尚待精确新源正常全CI，不能以旧394 CI代替；没有运行性能矩阵/比较，正式transition/escalation P95及源码超限未解决。PR16仍draft，不self-approve。
