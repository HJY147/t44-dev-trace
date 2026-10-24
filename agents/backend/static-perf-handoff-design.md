# 静态交接范围先行

分支codex/backend-static-perf-handoff，从本岗干净b081653起，应用与bc5逐字相同。先提交此设计/实际派工，再只读本岗API/runtime/services、消息通知门面与冻结DDL/接口；依据既有开发诊断result.md及池兼容交接，不再跑profile/ABBA或任何服务/HTTP/SQL/安装/测试/统计。

输出一页函数I/O→静态SQL/事务账→规模/索引/分页→待测区间。次数必须声明主体/成功新key/重放/是否批量为空等前提；参数化cursor、SAVEPOINT、commit/rollback、ping/checkout分别列，不把SELECT计数当全部网络往返。无法由静态确定的cost明确未知，不使用运行中独立资料或推断原正式根因。所有建议尚未执行，产品/用例/锁/冻结不变；若见确定缺陷只报告不修。Issue3原文交接并GET回读，归档日志/模块/交接后释放。
