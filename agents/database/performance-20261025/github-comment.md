Agent-Role: database AI
Prompt-Ref: ROLE-database-PERFORMANCE-20261025-v1

请求级诊断首阶段已提供，先设计df6fa10；准确工具 source edc3e2a32a4e657964155d5137c251a0d972d586，模块 tmp/833_database_performance/833_database_trace.py，SHA256 4edbf24779794a826bbe754ccad26890ea4c5c1d3f13f05778bad0e52ec307a9。install(engine)/request(operationId,canonicalUUID)/snapshot()/close() 已与后端真实对齐。没有生产、DDL、池/认证/锁/API或冻结变化。

同6项hook/SQLite/导入/异常/恢复检查在时钟修正前后均通过，不累加成12独立测试。有限实际Rows两次各6请求（页1/20/100各A/B、每请求2SQL、每次242映射行），仅临时toy SQLite；pending0/checkedout0/disposed，完整样本保留。初版CPU端点取在UTC格式化后出现约1–2us偏差，修正读序且原件不改；它不是产品提速A/B。初步数字不用于MySQL/HTTP/270ms正式成绩。

输出UTC/perf/mono/threadCPU及inclusive分层，SQL仅verb/已知表/shapeSHA，不存正文/参数/DSN/token/异常消息。engine acquisition不能称纯pool等待；PyMySQL buffered cursor execute不能称纯server/锁时间。Rows/UoW单engine与Result proxy支持范围写明。旧19配方/71 Rows不重跑。

本机无Docker，不连现存/未知库；下一步仅由总协调fresh GitHubActions MySQL service的t44_diagnostics专库与后端有限HTTP组合（≤10min），当前本岗未执行MySQL/HTTP/云。公开839的502/0完整正式组、规模6316超限均未关闭。报告 agents/database/performance-20261025/report.md，原始样本/验证在同目录。AI操作不记作学生本人执行。
