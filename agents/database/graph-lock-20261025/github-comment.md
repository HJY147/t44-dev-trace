数据库 AI 阶段交接：公开 fresh MySQL 分层分析 + 有限项目锁开发探针（不是性能修复/独立验收）

先设计9e0caf2，工具源e631936→3e11b1a。生产Runtime/Rows/DDL/池/锁净改动0；本岗不连接本地旧库/13306/云，不接触独立私有case。Runtime候选与HTTP业务race归BE，freshCI归root。

root已核官方40169575755/head81c909ad753aee7179ee0c464349a07273092fc0后公开mysql-before.json；本岗独立核原JSON1387070字节/SHA b17f0fd502f9342ec11f9ae12064edccb11f139b3a90997c6be022f5ec333a9e。真实Linux MySQL，应用HTTP路径经TestClient/ASGI，不是外部部署入口延迟。56/56 request_id+operation一对一join，48measured（每操作12），4warmup/4cProfile分开。

- 每请求cursor SQL get/list/contract/transition为9/10/4/27或29（各6）；映射行9/28/4/21或22。cursor wall/CPU均值ms依次2.969/1.651、3.953/2.279、1.208/.678、8.796/4.720；Rows inclusive5.416/3.933、7.246/5.378、2.246/1.621、14.505/10.364。不同层包含重叠不能相加。
- transition两次Session commit inclusive4.225ms/CPU.469，底层commit3.785/CPU.165；不能据非CPU残差推定锁/fsync/旧云根因。mapping与codec成本另存完整摘要，没有删除审计或缓存实时鉴权。
- 实际QueuePool5+10/timeout10/recycle1800/prepingtrue。observer装在fixture第一次连接后，physicalconnect/timeouts未观测；postdispose checkedin0不能证明期间没连接。

锁候选只START/UNBLOCK/REWORK项目S、其余_PROJECT_LOCK仍X；session→idem→project→members→target+pred保持，S不升级，门后membership重查保留。共享前驱仍X串行；前驱回滚双向线性化由BE的HTTP业务测试另核。sorted IN/ORDER BY不足以证明InnoDB实际加锁全序，EXPLAIN/有限并发passes也不构成全域无死锁证明。

可执行 tmp/833_database_performance/833_mysql_lock_probe.py，SHA46dc00a57ff79ec51c0d8bcc92dd32c5bdcb76e794c8c9417c89bbb2c42256fb，6个低层probe待root审准freshCI运行。真实Runtime.prepare/auth/locked_scope、两物理连接，P_S精确requesting/blocking/table/index等待边；parallel还观察两projects RECORD GRANTED S。包含反向id不交集、两共用pred串行、writer排斥、pred最新状态、同版本CAS；120s限时，专库/CI/localhost且拒13306，输出排他，无token/DSN/SQL正文/LOCK_DATA/绑定值。直接合成状态不是批准业务历史，低层不是HTTP验收。

离线join+本地同8个工具guard检查通过；首轮7pass/1fail为测试stderr bytes/str TypeError，原JUnit保留，修text=True后同8通过，最终源8pass0.40s。三新脚本Ruff通过。报告/原统计/三个JUnit/verification/prompt在 agents/database/graph-lock-20261025/。本岗未运行MySQL锁probe/新HTTP/云，原三502、0完整正式组、规模超限和人工出口均未关闭。
