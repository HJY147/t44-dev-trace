# 数据库模块报告：两默认独立候选已实现，准确源CI待触发

- Agent-Role database；Prompt-Ref ROLE-database-POOL-DEFAULT-CANDIDATE-v1；基点5408c05377d4f0084c6ae4eb596351add2004b67，设计d4e152f，独立codex/database-pool-default-candidate。
- 产品只改MySQLSettings默认pool_size5→15、max_overflow10→0；exact-diff.json核严格两Constant/两行，其他应用/SQL锁鉴权/超时/14冻结/993/930/955原字节不变。
- 参数名/种类/字段次序和显式override保持；默认15峰不变，partial size3峰13→3、partial overflow2峰7→17；双显式3+2或旧5+10保持，不能泛称所有调用者峰不变。
- 标准六默认池峰90仍同、温态保留上界30→90，多最多60idle；额外CLI/健康/迁移/备份/滚动实例另计，内存/FD/全局余量未知，不能承诺503归零/错误分布不变。
- root正式预留869；旧配置新default目标真实红，实际返还5而非15。候选10案例绿（含同目标），实际QueuePool合成DBAPI证容量拒绝/返还/复用/overflow关闭/dispose及Settings真实lazy构造原选项；无HTTP/SQL/真实连接/压测。
- 限定Ruff通过。原930硬5+10不改；matching filename但无test函数，单独collect-only0/exit5，未执行历史负载，hosted实际JUnit待核。
- 原cloc基线6307/--require-range退出1；两默认预计行净0，候选提交后同固定脚本实测。原正式失败/人工材料缺口不变。
- 准确源将普通push触发product全suite/真实MySQLMQ/全部生产coverage，draftPR到integration触发既有docker恢复工作流，各一次；不复用ABBA/旧CI、不合root。精确候选head保持，CI证据另分支归档。
- 本阶段AI实现非学生亲改；准确候选SHA/PR/run/Issue3/4回执随收尾，当前不预先宣称CI通过/正式性能或生产准入。
