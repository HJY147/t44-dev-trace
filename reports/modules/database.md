# 数据库模块报告：独立默认池候选设计

- Agent-Role database；Prompt-Ref ROLE-database-POOL-DEFAULT-CANDIDATE-v1；基点5408c05377d4f0084c6ae4eb596351add2004b67，独立codex/database-pool-default-candidate。
- 已读root ac826 RFC及backend445015f一页交接，实际GET Issue4评论6376569009，设计与原输入见agents/database/pool-default-candidate/。
- 本checkpoint仅设计/范围，产品未改，不合integration/替换bc5演示。随后产品只改engine.py的pool_size默认5→15、max_overflow默认10→0；其他生产/冻结/SQL锁/超时鉴权字节不动。
- 标准六默认池峰90不变、保留上界30→90；partial size3从13峰变3，onlyoverflow2从7峰变17，双显式保持，不能泛称全部调用峰不变。内存/FD/全局余量未知。
- root已预留869，用实际QueuePool+合成DBAPI证容量拒绝/返还保留/复用/dispose与Settings真实lazy组合；旧993/930断言/955原件不改。
- 将先旧源新目标红，再实现两literal；本机不发HTTP/SQL/负载。候选完整真实服务suite/覆盖/容器恢复只跑既有hosted一次触发，不复用ABBA/旧CI。
- 原口径基线实测6307/exit1，预计有效行不变待候选实测；原正式失败/人工材料缺口保持。
- 产品push→product工作流，draftPR到integration→docker工作流各一次；精确候选head保留，CI回执在独立evidence分支，未通过准确源专审不合root。
