# ROLE-database-FINAL-20261029-v1

本岗实际收到的总协调派工原文（不是用户逐字原始提示词）；没有把建议稿记为已执行新版本。

> 你是T44固定数据库岗，用户已明确今天把软件/性能/规模全部达标后备份核验并删除云服务器，不能再无止尽停机交接。主项目/AGENTS /Users/yang/Desktop/nothing/软件开发大作业，当前integration5868779e949adef066fe26bffbc4f2e8afee7649；建独立worktree codex/database-final-20261029。实际生产5880有效行/65files，严格目标3500-5100，backend/frontend另岗；你负责backend/t44/persistence/*，目标实质净减约350-450行兼顾性能（migrations370/seed326/rows293/schema106/delivery159/scans103/uow86/engine93）。先15min内给能落地的结构方案与净收益，然后自主实现/必要自测。不能压格式凑行/移动隐藏实现到不计数目录/删迁移验证安全门禁/弱断言/改变Frozen API或DDL/v1.2规则。原native CI796/FE89通过，需保持。旧native catalog替换Inspector候选009b...已净+15、回退，别重复；catalog有序注册-4已在产品0b。backend服务/域/API由其他岗别动，跨模块需要走root接口。用户授权内部重构，不要把常规选择变成新审批/RFC循环；schema.sql等冻结DDL原字节保留，DDL行为若需变更先报root。旧source0b actualmysql384/source686云资料只当历史，不触及云、不读任何QA PRIVATE/用例/工作日志。测试放tmp新756以下编号降序，模块原自测可跑，actual未跑明确；自己阶段commit/push，四件/真实prompt简洁记录，实际代码优先。当前2026-10-29 19:14 CST，今天尚4.7h。

执行中实际收到并采用的技术细化：

> 前端只能真实-9，backend初估120~200，所以不能只做几十行微改。请更深评估成熟SQL parser替自制CHECK Pratt parser约90行（sqlglot MySQL官方 https://sqlglot.com/sqlglot/parsers/mysql.html，可差分测试token literal/precedence/fullconsume，锁新依赖；Alembic check表达式不比较不能替代！官网明示限制）。规范化schema expected/actual签名表是否能收敛重复而非代码增多，seed声明默认上下文消重复。目标DB至少250~350才有机会全局，不能降native gate或DDL。成熟库标准功能复用为合法实质重构，不是把impl搬配置/压行。可选择不用sqlglot若不安全，给更具体路径收益。继续实际代码优先。

改进理由与产物：标准 MySQL AST 复用替换自维护优先级解析；官网明确 parser 宽松，额外保留完整词法、单表达式和 AST 边界。backend岗只精确添加新依赖锁，本岗只改3个持久化文件与新增755 owner测试。实际减74行，未把250–450目标写成完成。最终冻结/完整native CI由总协调继续，四件记录仅声明本地结果。
