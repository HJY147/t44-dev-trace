# 实际审核修复派工与性能窗交接指令

执行者database AI，非用户亲改代码，不是事后优化版。

> ROLE-database-REVIEW-FIX-v1：恢复数据库岗，优先处理审核 C-P4。基于根7ce7171同步（随后将合入FE bfa1625），不改冻结DDL/API。迁移checker只比较索引/FK/CHECK名字，保留名字但改列顺序/唯一性/FK目标/CHECK表达式仍接受；审核原复现tmp/reviewer/957_schema_semantics_probe.py不可削弱。请修复真实Inspector语义比较及MySQL合理规范化，自己的新测试编号956起（先回报占用），隔离新库t44_review真实MySQL验证正确结构接受/错误结构拒绝，root将建新库，不动dev/acceptance/perf。尽早提交功能checkpoint，再补日志/报告/handoff/prompt和PR17真实交流。可做真正删重复/未使用代码减量，禁止压行/改计数/移业务配置/去功能。当前5944减FE83仍超5100，不可宣称代码规模已过。勿读或交流独立验收私有资料。

实际性能环境限制：
> 环境调度：FE已停止浏览器/构建，root图渲染即将结束。独立正式400并发10分钟性能窗口将在接下来开启；窗口期间请只做源码审查/编辑和Git/日志，不运行真MySQL迁移/测试、seed、pytest或构建；收到root窗口结束通知后再跑。C-P4先正确修复。后续真实减重复可考虑seed受信row-builder合并重复version/created/updated默认字段和FK上下文（不是改行格式），请按断言相同的seed回归评估；不保证仅此够规模目标。

实际后续交接原文：
> 收到956实际路径tmp/backend/persistence/956_schema_semantics.py，根下次更正分配表。性能实际稳态10:15:08–10:25:08 UTC，后面还需契约/升级两个独立600秒批次；因此可能需30余分钟无本机测试。请先提交可审代码checkpoint，明确“未运行、待性能窗后验证”，不用等到测试完成才保存，也可push draft让远端CI自然执行（不占同机压测资源）。然后暂交接释放槽，我安排prompt岗做资料整理；窗口结束正式续派你验证/修复与seed减重复。根不会把未验证checkpoint当C-P4已过或合并main。

本次产物：migrations.py语义比较源码、唯一新956本岗回归与显式专属review库探针源码，以及本岗状态记录。未读取/改动957或tmp/independent/private-*；在性能限制到达前只读观察过MySQL Inspector输出，限制到达后没有执行pytest/真库迁移/seed/构建。源格式化属于编辑，不当作lint或测试通过。
