# ead SQL账本两常量与新CI限定复审

## 1. 对象与历史

固定AI审核岗，ROLE-reviewer-BACKEND-LEDGER-EAD-v1；独立worktree codex/review-backend-ledger-ead，直接从精确 **ead155e6204de9004bc968e9b9648358cfed75f8** 建立，先scope ee2d453。比较源 **5cc856d6fa94b1fdde32605543b53822f9747f00**，原源码审核187ca2a86565f228fda89e59526cdb257af3d5ad原样保留。先行新设计32cb991，前置开发E **01b184f4ac306a106fb6432ee8067f9993ead002**；终态E待总协调明确发布后追加，不自行读取未发布资料。

## 2. 需求与唯一变化

原5cc经限定源码审查只删除不消费依赖的Workflow读取；旧985精确SQL账本尚假定所有原SQL保持。新source只把block SELECT22→20、unblock24→22，DML5/control2不变，另改一条历史注释；plan/escalation/replay数、精确actual==expected及其它断言不改。该修正对应明确删除的两个无用SELECT，不是降低独立270ms/600秒/零错误指标。

## 3. 字节与AST责任边界

本岗实际Git检查：ead相对5cc的backend/t44、frontend/src、deployment及.github字节差异为空；tmp/backend只有985_mysql_http.py。将这两个SELECT Constant恢复旧值后，整份985 AST与5cc完全相同；源码hash与开发test-only-proof.json吻合。原应用审核只通过这项byte identity被引用，不重新包装为新性能证明。审核岗没有改任何产品/开发测试。

## 4. 输入、输出、兼容

985的fixture、五个参数、业务请求/schema及expected结果输出保持；只更新精确查询数量。实际block是pending任务阻塞，unblock是从pending阻塞回pending，对应域不消费依赖。保留代码统计真正SQLAlchemy语句而不是预设gateway值；测试计数包含实际锁读，不能当所有协议/网络往返数。新应用零diff，因此API/DDL/RC/鉴权/事务实现亦无新差量。

## 5. 断言保留与旧失败事实

985:946仍精确actual==expected，947保留正常3次实时auth锁模式/replay2次，948保留每UoW closed/commit1/rollback0，949保留replayed，951保留正常2UoW/acquire及replay1；整文件其它RC/事务/审计/幂等断言AST相同。

本岗核前置E官方旧coverage/contracts两份gzip及解压raw双SHA。原run40087756354确实在(20,5,2)!=(22,5,2)及(22,5,2)!=(24,5,2)处失败；200/schema已过，打印2UoW/2acquire/2commit。其后947–951在两个失败case中没有执行，不能把静态保留说成旧绿。原5cc失败、报告和PR44 COMMENT不回写或抹除。

## 6. 执行与证据

本岗仅Git/AST/公开开发原件hash检查；测试、SQL、HTTP、MySQL、服务、负载、CI触发均0，不读独立839/841/852/private，不联系独立岗。自有static-delta-audit.json和initial-E-file-hashes.json记录准确source/原件绑定。前置E只Ruff/format与collect-only，不冒称5参数本地执行。

总协调转达11:19:23UTC新product40088982094四job success，这是实时状态通知；在本报告最初静态阶段，尚不将其替代终态原日志/artifact核验。准确新E公开后，只核所需源/门槛，不重跑套件。

## 7. 十项清单（静态阶段）

| 项 | 判定/边界 |
|---|---|
| 1 身份版本 | 通过：精确ead/5cc/前置E及新scope，AI审核非独立测试 |
| 2 范围 | 通过：唯一985两Constant＋注释；无其它AST差量 |
| 3 接口 | 不适用：应用字节同，接口无新增修改 |
| 4 DB兼容 | 不适用：无生产/DDL/RC/池变化，测试fixture相同 |
| 5 业务 | 静态无新增阻断：只修准备用于非依赖消费者的计数 |
| 6 鉴权 | AST保留，原失败后断言须由新CI实际执行证明 |
| 7 事务并发 | AST保留：DML/control/UoW/acquire/commit/closed/rollback不变 |
| 8 审计幂等 | 整模块AST相同；不将synthetic/static当正式运行证明 |
| 9 证据 | 前置E/raw hash通过；准确终态E核验待追加 |
| 10 完整准入 | 未作merge/global判定；6316仍规模失败，云性能未通过 |

## 8. 结论与后续

**ead两常量差量静态无实质阻断，终态门禁证据在精确发布后另核。** 原5cc/source187以及旧CI失败保持；不提前合并5cc/ead，不发布APPROVE或reviewer/stage success。源码计量沿用byte相同5cc的6316、净+6/超1216，未新跑cloc、不称减量；N07与云性能仍未通过，502/P95根因和600秒完整运行不是本轮结论。
