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
