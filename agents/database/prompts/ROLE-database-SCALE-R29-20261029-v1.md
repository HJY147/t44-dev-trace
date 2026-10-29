# ROLE-database-SCALE-R29-20261029-v1

操作者：数据库 AI 岗。当前调度指令实际执行；不是用户亲自修改代码或独立测试结论。

## 本轮调度原文（原样保存）

你是T44数据库岗位，项目只 /Users/yang/Desktop/nothing/软件开发大作业。读AGENTS.md，独立worktree codex/database-scale-r29，从 codex/resume-coordination-20261029派生。当前严格有效代码5898/65files、上限5100超798，用户要求实际达标，禁止压行/minify/将实现挪计数排除区/删功能断言。前端岗另在优化FE，不跟你写同目录。本岗任务：认真查 backend/t44/persistence 的1672行重复实现（migrations374 seed326 rows293 delivery159 schema117 scans103 engine93 uow86 accounts61等），找可实现的正常可读抽象或重复schema/投影/编码去重，先做一个保持完整数据库语义的实际候选，争取净减100–250有效行而非只提建议。不能覆盖已应用迁移内容/校验和或更改schema/接口/错误码/锁序/撤权重验/事务/审计/造数规模，不引入SQL解析DSL、移到外部库/文件以规避计数；若历史SQL校验和必须保留则说明不能改，重点现行适配/seed算法共用结构。所有原测试文件不改，真实运行相关模块原测试/原MySQL如环境有才测，若无MySQL诚实区分。新增必要测试tmp/769_database_scale_r29（根分配769）。只改本岗persistence目录及4件/prompt；跨后端业务目录先提接口由后端owner，不擅改；严禁碰独立QA目录 tmp/772/PRIVATE 及783/792PRIVATE，不联系测试岗。正在云测旧f7版本，你仅本地候选，不集成/开云；用户授权阶段commit/push。报告前后同口径cloc真实净减、完整语义风险和验收证据；不能靠格式化或未实测估算声称减行。先真正读代码尝试一个结构候选，十分钟给首个实证进度。

## 执行约束与改进理由

- 先核验精确 Git 基线、AGENTS、原 source_count.py 和固定 cloc 2.10 hash，按已提交文本计量；不把 SQL/配置/测试混入应用口径。
- 先真正实现列投影共用候选并实测，migrations374→377/净增3，否决而保留差异和原测试结果。
- 当前候选只简化校验和保护下的固定 DDL 适配：同一声明序列构造 Table；按真实声明边界分段，替代输入格式不再需要的通用逗号/引号扫描。
- 新增旧源逐项差分、18表双方言DDL/列/索引、四种未审文本变更拒绝检查；全量原测试不改。明确格式依赖和未来新DDL版本需要重新审核适配器。
- 不用无证据预估作减量；本轮真实仅净减11，争取100–250未达到，最终是否集成由总协调决定。

## 产物对应

产品：backend/t44/persistence/schema.py；新增自测：tmp/769_database_scale_r29/769_schema_equivalence.py。
证据：agents/database/scale-r29/；岗位四件：WORKLOG、modules/database、handoffs/database、本提示词。
