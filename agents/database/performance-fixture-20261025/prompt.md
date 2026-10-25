# 实际提示词留痕

ID ROLE-database-PERF-FIXTURE-20261025-v1；操作者数据库 AI，决策和授权来自root转发的本轮任务，不记为用户亲自生成数据/改码。

root实际任务：产品冻结c8，另一个全新性能schema t44_p829_20261025，仅读自己CRUD env，不读admin/功能库/独立case。先设计fixture-only helper，不改生产/DDL；40projects/6000tasks/9000dependencies/15000原seed records口径，5synthetic用户m/d/d2/r/x，P1/I1至少800，400distinct DEVELOPING future>48h、400disjoint active overdue，其他任务分散39项目、明确偏斜；全部FK/版本/基线/评审一致，generator/source/hash/seed/anchor真实，direct synthetic不冒业务历史。有限时间不足应保留失败，不堆未经审核大生成器。

本岗实际细化并经root确认：复用冻结_populate到显式Collector，不monkeypatch；选原400state2与400state1（无批准指针）集中，其他5200轮转，关联project_id同迁移；重建9000只指向同项目更小id且DELIVERED的边。保原11400review+3600decision=15000、assessments额外3600；d2只P1开发/capacity，x完全outsider。通用35FK及批准指针核验前后都做，输出逻辑hash与完整ID，随机密码hash不落输出、不冒物理库可重现。

08:07root为腾独立执行槽要求立即结束：本岗完成正在进行的push，源d8已远程，五原件未跟踪保留，停止库写。后续root明确恢复只封E/Issue/文档；08:15:44 root自行签5会话的事实单列，原auth_sessions0不回写。这次恢复没有新SQL或测试，不因报告需要补造执行。

改进理由：用冻结生成器和显式变换缩小新增逻辑，将分布偏斜、records定义、身份操作时间与逻辑摘要覆盖范围写清，防止把环境准备写成性能验收或真人经历。
