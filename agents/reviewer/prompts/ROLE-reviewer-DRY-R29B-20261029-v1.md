# ROLE-reviewer-DRY-R29B-20261029-v1

操作者：固定审核 AI；决策/集成者：总协调。审核岗不是独立验收测试岗。

## 实际派工原文

你是固定独立审核岗（不是独立验收测试岗），仅本地代码审查/窄行为复测，不操作云、不读任何PRIVATE、不联系独立测试岗。仓库 /Users/yang/Desktop/nothing/软件开发大作业，先读AGENTS.md。从root f7ee5d3f 建 .agent-worktrees/reviewer-dry-r29b / codex/reviewer-dry-r29b，只写审核四件/报告/必要tmp767若已占用查号。两个候选待审：后端41a111f270e949326202b8af5770db8aa7102e82（源起点a92e；products仅reviews.py抽_latest_assessments helper，两调用展开模块AST应同，净减3；最终文档head a13f74f1021e67ea5cb35c2b69ab94f5651bca79），数据库8f29030756139061341e0a636c8774ca790964bd（源起点a92e，migrations.py四个原catalog查询由三元组改label有序映射，应保SQL/expected/顺序/缺陷全部不变，净减4；数据库岗最终交接尚在准备）。不需要重复全CI或云测试；独立核实际diff/调用时机/异常/SQL顺序与元数据，必要有意义的同输入行为对照。审核实际通过范围/发现/未核内容明确记录；不把7行说成规模达标/性能改善。跨岗只同root，GitHub Issue3/4可写限定审查结果，用户已授权项目内沟通。给P1/P2和是否准入，保持同业务接口、冻结契约、原测试/断言，不能代root集成。尽快先review verdict再封四件提交push。

## 后续更正原文

更正测试号：后端766、数据库765已使用，新的审核测试请使用tmp/764_reviewer_dry_r29b（先查冲突），不要767，以满足用户新文件编号递减。保留最初派工更正记录。仅新测试目录号，其他审核范围不变。

## 实际执行改进及对应产物

- 先核完整产品 diff 与冻结文件/原测试字节边界，再把两个限定语法变换归一成完整模块 AST；避免只比较两条查询的局部截图。
- 使用自有20个后端同输入轨迹和8个 catalog 情形；真实 Call、原错误、查询失败、四个 SQL 位置异常与连接上下文退出均比较。序列化隔离及 metadata-derived catalog fixture 的限制如实声明。
- 首次运行50检查通过；随后只完善审核 fixture 的 insert 后回读，并加22个明确结果断言，最终72检查通过；产品/原测试未改。
- 按固定 cloc 2.10 与原应用范围独立复计。二候选的组合仅为临时字节投影；不由审核岗集成。
- 先向 root 发送限定技术结论，再封 `reports/reviews/dry-r29b-20261029.md`、岗位三件及 `tmp/764_reviewer_dry_r29b` 的原始输出。
- 未扩编 agent；没有访问云、PRIVATE 或独立测试岗。没有把本轮局部探针称为独立验收。
