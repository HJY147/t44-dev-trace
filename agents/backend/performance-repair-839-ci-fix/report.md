# 5cc首次CI失败 → 精确账本同步候选

后端AI诊断/修改；先847256e范围、32cb991设计，新test-only source **ead155e6204de9004bc968e9b9648358cfed75f8**。原PR44头5cc856d保持，生产Workflow不再修改，应用根对5cc逐字同；全部非记录diff只有985_mysql_http.py。

## 原始失败与真实归因

官方run40087756354绑定head_sha=5cc，coverage120854051910/服务契约120854052090原日志已只读获取。原ANSI bytes两gzip、raw/gzip SHA和解压逐字核验在raw-manifest.json；最初gh API拒绝转义输出exit1另记，随后显式原始输出GET不是CI rerun。三类已知敏感模式检查0匹配，不把该有限检查冒全能脱敏保证。

唯一失败是985原账本两个参数，实际分别(20,5,2)/(22,5,2)，旧期望(22,5,2)/(24,5,2)；均与候选少两个无必要SELECT一致。端点200/schema检查已过，实测打印均2UoW/2acquire/2commit；**后续auth/closed/replayed断言在旧失败位置之后，两个case当时没有执行，不能凭静态保留就称已绿**。没有这些日志支持的业务回归/环境故障，实际失败属于开发统计期望未随计划查询变化更新。

全suite原560pass/2fail；contract原177pass/2fail，integration原91pass/2fail，彼此重叠不相加。原5cc的源码clear/本地36绿和Docker另run成功不抵消该failure，不重跑/覆盖旧日志。

## 唯一修正及验证范围

新source只把block SELECT22→20、unblock24→22，及原“全部SQL不变”注释改为preflight鉴权/事务保留、Workflow省读。AST白名单证明只有两常量变化，原fixture/函数/其余全部AST节点相同；DML/control、3实时auth锁模式、2UoW/acquire、commit/rollback/closed、replay和其它RC/审计/幂等断言全部保留，plan/escalation/replay数不动。不是放宽精确等式、更不是降低270ms/600秒/零错误独立门槛。

本地仅原backend配置Ruff/format通过及collect-only收集5个参数/35 deselected；未执行MySQLfixture、无本地SUT/HTTP负载/云操作，不把收集写成5pass。此前36本地目标未重复。原应用计量6316来自5cc，新source应用逐字同，仅据身份沿用其规模边界：仍超1216、未达标，没有重跑cloc或新减量。

正常push自然触发新product **40088982094**，head_sha=ead155e，首次metadata为in_progress（new-ci-initial.json）。新真实CI须实际执行所有保留断言及全suite后再给结论；此处不预先填通过/完整覆盖。没有新Docker运行证明；原Docker的精确source适用范围不扩大。新source需root/审核单独核；PR44原5cc代码审核历史保留，main/云C不变。

核心原件：design.md、test-only-proof.json、candidate-binding.json、failure-extract.txt、raw-manifest.json、两job metadata/gzip；本次只读取明确开发CI，不访问任何独立839/private或向其发送信息。新结果将另行归档，原公开性能失败和5cc CI失败均继续保留。

## 后续终态封档：准确ead155e的新run（未重跑）

product40088982094/attempt1现completed/success，head_sha准确ead155e；frontend120857578995、coverage120857579219、static120857579266、contracts120857579310四job均成功。此前in_progress回执原样保留，不倒填成当时已绿。此段仅新平台原件阅读/归档，没有新测试、CI rerun、服务或云执行。

四个官方artifact ZIP先核官方sha256 digest/bytes再开，原ZIP只留ignored0600；沿旧18项选择名单取新原件、raw/gzip双hash和真实解压逐字核验，未复制旧结果。coverage/contracts成功job原ANSI日志另gzip保存。原件/metadata/manifest在records/ci/40088982094，汇总records/validation/composite-dependency-ead-ci.json。

实际JUnit full **562/0failures/0errors/0skipped**，contract179/integration93/fault19各零（markers重叠，不相加）；原账本block/unblock/plan/escalation/replay五参数在full/contract/integration全部实际passed，因此原失败位置后的保留断言这次确已执行。44Python生产文件与准确ead Git集合逐一相同/excluded0，行2641/2960=89.22297297%、分支663/828=80.07246377%；coverage原combined87.2228%不冒行覆盖。FE89通过/0失败或pending，20TSVue与Git全集同，行364/390=93.33%、分支821/932=88.09%，不扩到CSS/HTML。

**Docker范围仍分开：** 原40087993372官方API head5cc、success，是旧PR44运行；本次没有ead Docker新run，也没有新增实际PR merge-checkout证明。5cc↔ead的backend/frontend/deployment/scripts/.github/compose/specs等源码roots逐字同，只支持明确Git源比较，不能把API head冒checkout或把旧Docker改名为ead通过。当前ead不含后来已整合Nginx候选（nginx文件仍与云C同），新product也不证明Nginx修复。prior-docker-scope.json明确该局限。

上述开发门禁不取消旧5cc CI失败或839公开短窗性能失败，不证明502根因/600秒达标/规模达标/独立验收；代码仍6316超1216（原准确测量+应用身份沿用，本次未重数）。生产/测试/配置不再修改，新E只封官方新原件与终态，整合由root另决定。
