# 数据库模块报告：保留池ABBA诊断设计中，未执行

- Agent-Role database；Prompt-Ref ROLE-database-POOL-RETENTION-v1；基点2a0f091，分支codex/database-pool-retention。
- 依据root61b23e6 pool-retention-diagnostic-rfc；生产精确bc5，不改backend/t44/默认池/冻结/SQL/锁/全局资源。
- 实际锁SQLAlchemy2.1.6；本地impl.py/base.py与官方rel_2_1_6逐字相同，source-verification.json可核。首次CA失败与保留TLS验证后的修复如实记录。
- A保留5+溢出10、B保留15+溢出0，每个单worker/单engine同15峰值；QueuePool懒建、满保留队列返还时close。B可能更多空闲会话/内存，不声称零成本或正式根因。
- 详细工具范围/阶段/失败/清理/精确命令见agents/database/pool-retention/design.md；复用955，不新编号。
- 预定唯一ABBA为A1/B1/B2/A2，每段并发32、1s预热+4s稳态，120s总墙时；所有错误保留，四P95不平均。
- 本岗当前仅设计/主源核对，未运行HTTP/SQL/负载；工具提交和离线验证后报就绪，实际比较等root明确窗口。
- 将使用t44_profile/18083/已有私密fixture，值不输出；不重seed或创建业务fixture，不开放独立私密资料。
- 后端实际协作与Issue4/3精确readback随工具阶段记录；开发诊断不是独立验收，操作者AI不计学生本人研究/手改。
- 生产净变更0，原正式三组失败/规模6307超1207/人工材料本人完成继续保留，不借诊断替换原结果。
