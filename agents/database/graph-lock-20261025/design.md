# MySQL 分层诊断和项目共享锁候选设计

数据库 AI，2026-10-25。先设计，未授权直接改生产。输入仅为 root 已核官方 artifact 的公开 `records/ci/40169575755/mysql-before.json`（source 81c909ad753aee7179ee0c464349a07273092fc0，文件 SHA b17f0fd502f9342ec11f9ae12064edccb11f139b3a90997c6be022f5ec333a9e）。保留旧云未达标，不能用本次 Linux/顺序 MySQL 诊断追认旧云根因。

## 分层分析

离线脚本按 request_id 一对一对齐 56 个 HTTP/DB 记录，只统计每操作 12 个 measured 样本；warmup/profile 单独计数。报告 SQL 次数/形状/表、消费行数、各 phase 的 wall/thread CPU 均值和范围、实际 pool 元数据。Rows、Session、cursor、acquire、UoW、commit/rollback/reset 包含重叠；不加总成占比，不把相减后的残差称纯 Python、锁或网络。现有 observer 安装前 fixture 已连过库，physical connect/timeout profiles 缺失就标未知；post-dispose checkedin=0 不说明期间没连接。

## 候选边界和证明义务

BE 拥有 Runtime；唯一候选是 graph_lock 内项目门，`_PROJECT_LOCK` 操作仍 X，只有 transitionTask START/UNBLOCK/REWORK 用 S。UNBLOCK 的 pending 分支仍保留同样的依赖收集和目标/前驱 X，不额外缩小锁范围。

1. 完整顺序保持 session S（logout X）→owned idempotency X→project S/X→members S→target+predecessors X。prepare/claim 与拒绝审计的原锁/认证不删。门前 authenticate 的普通 RC membership/project 读不提供稳定授权；门后锁定 members 并重做 active/role 判断必须保留。
2. 所有图/成员/迭代/分配写操作均先项目 X；因此项目 S 持有期间图集合、capacity 与 membership 不会被这些写者改变。没有任何候选路径需要升级 project S→X。projects 本身当前无更新 API。
3. 门后目标和已发现前驱仍 X 至提交；同 predecessor 的读者仍串行，只有不相交的 target+predecessor 集合才能同时过门。前驱 rollback 可先于读者提交、或在读者之后提交；不能据此声称已开始任务永不出现后来回滚的前驱，那是原业务模型未定义的另一项不变量。
4. 两个读者可新增并行多行 X 竞争。`ORDER BY id`/sorted IN 仅是应用请求顺序，MySQL optimizer 可能先按其他索引取行再 filesort，不能据文本证明实际加锁全序。需记录真实 EXPLAIN/index 与 data_locks，开发并发覆盖相交集合/反向入口；有限样本通过仍非全域死锁证明。如果实际访问计划不能证明规范顺序，保留候选未准入，不为性能删 predecessor X。
5. audit/outbox/decision 的 FK 检查可能隐式 S project/task/user/assessment 等父行；project/task 已持 S/X 时兼容，但需要真实成功写路径验证，没有把显式 SQL 数量当所有锁。FK/auto-inc/record locks 的瞬时额外锁应按实际可观察范围记录，不推定不存在。
6. changeIteration/member/assignment 仍 X，不能越过候选 S；readers 不反向持 task 再请求 project。非图 transition 原来没有 project 门，是单独已有路径，必须检查其 members/target 与 graph reader 的相交组合。

## 真实 MySQL 开发验证分工

DB 驱动在 root 审准的全新 GitHub Actions service、独立 schema t44_diagnostics 内执行；明确 CI=true、localhost、库名三重限制，不访问 13306/旧环境。fixture 自建本次用户/会话/幂等/项目/迭代/任务，不清空既有对象。真实 authenticate、Runtime.locked_scope、Rows/UoW，两个独立会话/物理连接；Event/数据库锁等待观测控制暂停点，不用单纯 sleep 未结束推定阻塞。驱动限定时长，记录 UTC/monotonic、原异常类和 MySQL 数字错误码，不输出 token/DSN/绑定值或自由正文。连接全部 rollback/close/dispose，输出排他写。

低层用例：不同目标 reader 门重叠；reader 持门时 graph writer 请求 X 并有 MySQL wait 边；相交 predecessor X 阻塞以及释放后最新状态可见；相同版本目标的 CAS 一次成功一次拒绝；目标+前驱 EXPLAIN/已持 record 锁顺序仅做观测。baseline X 与候选 S 对照使用相同固定输入，不用吞吐数比较无负载门控测试。

BE 负责独立文件内真实 HTTP 业务 races：graph writer、predecessor rollback/START、capacity/revoke 先后、同版本 CAS 的状态/错误码/审计/事务结论。DB 低层 probe 不替代这些断言，不叫独立测试。root 负责组合 workflow 和 fresh service 准入；本岗不运行本地 MySQL，不开云。

先给可执行驱动/checkpoint，再等待 root 的唯一环境窗口；运行与否、失败与未知单独记录。任何优化只有在实际运行及正确性检查后再讨论准入。
