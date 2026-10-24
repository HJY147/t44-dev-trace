# 数据库模块：原developer fixture只读索引核查

本岗AI，ROLE-database-INDEX-READONLY-v1；先行设计0073a39后动作，基点b40d888/公开BE d834。只用原955/ABBA自有t44_profile、项目44/task6004，hash/0600/旧服务停止及归属通过。

- 一次00:44:34Z内联只读，14条应用层语句：4元信息/归属、三表各SHOW INDEX/CREATE、四普通EXPLAIN；连接已rollback/close。正常驱动会话初始化不混入SELECT计数，无数据库/数据/DDL/DML/ANALYZE/服务/全局设置变化。
- task_dependencies真实无task_id前导自动键；其复合FK由project前导索引满足。但tasks多3个自动FK键、notifications多1个，不能按显式DDL概括实际索引。原字段及官方依据见agents/database/index-readonly/report.md/result.json。
- 单列依赖+ORDERid估算type=index/key PRIMARY/possible_keys NULL/rows9216；project+task对照ref复合键/rows1且filesort，产品未改。其他两普通计划也保存；不运行被解释查询。
- Cardinality/rows只是统计估算，不是COUNT/实际扫描或时延，原fixture不代表6000任务分布/400并发、正式根因或收益；当前app可见连接不证明跨账号全局。无产品全套/coverage/独立验收/性能结论，原失败/规模/人工材料边界保留。
- 原fixture bytes未变，生产/specs/tmp相对b40d888差异为空；未读独立材料/联系测试、未增改测试文件。操作者AI，非用户亲改。
- [Issue4真实评论](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6377715017)已精确GET全文逐字核对；本岗plan/result/static-comparison/report/summary、日志/实际prompt/handoff全部归档。本阶段无需后续SQL/负载，交接后释放。
