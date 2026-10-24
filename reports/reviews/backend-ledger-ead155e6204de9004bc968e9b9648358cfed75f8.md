# ead SQL账本两常量与新CI限定复审

## 1. 对象与历史

固定AI审核岗，ROLE-reviewer-BACKEND-LEDGER-EAD-v1；独立worktree codex/review-backend-ledger-ead，直接从精确 **ead155e6204de9004bc968e9b9648358cfed75f8** 建立，先scope ee2d453。比较源 **5cc856d6fa94b1fdde32605543b53822f9747f00**，原源码审核187ca2a86565f228fda89e59526cdb257af3d5ad原样保留。先行新设计32cb991，前置开发E **01b184f4ac306a106fb6432ee8067f9993ead002**；总协调随后明确发布终态E **14a61c4e771042adc6113942723782f71568e432**，本岗才续核该准确原件。最初静态待E阶段e30a8ba已push，历史版本保留；没有读取未发布资料。

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

本岗执行Git/AST/公开开发原件hash检查，并只读下载既有官方CI artifact；测试、SQL、HTTP服务、MySQL、负载、CI触发均0，不读独立839/841/852/private，不联系独立岗。自有static-delta-audit.json、initial-E-file-hashes.json记录静态阶段和前置E19份原件；终态E另26份manifest原件、15freeze及source/tests字节身份核验在terminal-E-file-hashes.json。前置E只Ruff/format与collect-only，不冒称5参数本地执行。

终态本岗通过GitHub connector独立读取run40088982094的4个官方artifact元数据与4job/steps均success；各artifact workflow_run.head_sha精确ead、run attempt1。为核实际ZIP bytes，本岗经官方只读artifact API另取四ZIP到0700临时目录/0600文件，四份大小与官方digest全部核对后才打开任何ZIP；逐一对18选中member与E raw/gzip双SHA及解压字节，全部同。ZIP仅临时读取后删除，未读取未选中member内容，不触发CI。live-artifacts.json、live-jobs.json和terminal-E-audit.json保留完整核验事实。

实际JUnit full **562/0failures/0errors/0skipped**，contract179/integration93/fault19各零；子集与full重叠不相加。ledger五参数在full/contract/integration均实际passed，所以原count失败位置后保留的auth/closed/replayed等断言在新run确实执行。coverage及contracts两job原始ANSI日志的gzip/raw SHA均核，git log -1实际checkout均为ead，不以API head代替checkout。

后端coverage44个Python文件与ead Git集合精确相同，excluded_lines=0；行2641/2960=89.22297297%，分支663/828=80.07246377%，不把combined87.2228%冒行覆盖。FE89全部pass、0failed/pending；20个TS/Vue文件与Git集合精确相同，总行93.33%、statement88.62%、function85.83%、branch88.09%，不扩到CSS/HTML。原始static/gate命令与suite gate全部exit0；覆盖门槛和配置没有变化。

终态E没有生产/测试变化；ead两nginx配置仍与云C逐字同，不含另外的Request-ID候选。**没有ead新Docker run或新实际merge-checkout证明**：旧5cc Docker40087993372保持其旧来源和局限，不改名/移植为新ead Docker证据。这里只闭合准确新product run门槛，不外推完整root组合、云或独立验收。

## 7. 十项清单（精确终态）

| 项 | 判定/边界 |
|---|---|
| 1 身份版本 | 通过：精确ead/5cc/前置E及新scope，AI审核非独立测试 |
| 2 范围 | 通过：唯一985两Constant＋注释；无其它AST差量 |
| 3 接口 | 不适用：应用字节同，接口无新增修改 |
| 4 DB兼容 | 不适用：无生产/DDL/RC/池变化，测试fixture相同 |
| 5 业务 | 静态无新增阻断：只修准备用于非依赖消费者的计数 |
| 6 鉴权 | AST保持；新run ledger五参数实际passed，后续鉴权断言已执行 |
| 7 事务并发 | DML/control/UoW/acquire/commit/closed/rollback AST不变且新case实际pass；不扩成新并发性能证明 |
| 8 审计幂等 | 整模块其余AST保持，准确开发suite实际pass；非独立/云验收 |
| 9 证据 | 前置E19/终态E26文件、四官方ZIP/18成员/两job日志/源码全集核同 |
| 10 准入范围 | 本次代码＋准确product开发门槛无阻断，可交root整合；无新Docker/完整组合证明，6316和云性能仍失败 |

## 8. 结论与后续

**精确ead＋终态E14a61的本次测试差量和准确product开发门槛核验无剩余阻断，可由总协调整合source＋E＋本审查并按流程验证新的组合。** 技术结论已先转达root，行政评论/封条不被倒写为当时已完成。原5cc/source187及旧CI失败保持；不发布APPROVE或reviewer/stage success，不代表main/课程整体通过。源码计量沿用byte相同5cc的6316、净+6/超1216，未新跑cloc、不称减量；N07与云性能仍未通过，502/P95根因和600秒完整运行不是本轮结论。


行政封条实际完成：精确ead/终态E14a61报告与独立原件核验commit fca3a3fa764c41f5f30ac61a645631a7784e2add 已push。Issue3 COMMENT6383718463实际发布，特定REST全文GET body逐字、Issue归属、完整source/E SHA核同；https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6383718463。回执github-comment-full-get.json/verification.json。仅限定代码+product门槛交root整合，旧5cc红CI/187保留，N07与云性能未通过；无新Docker/NGINX覆盖或global status。0本岗测试/SQL/负载/CI触发/独立私密读取或通信。DB修复已有独立审核岗，本阶段结束释放，不继续排队DB。
