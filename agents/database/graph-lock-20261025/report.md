# 数据库阶段报告：真实 MySQL 成本分层及锁候选探针

数据库 AI；设计 `9e0caf2` 先于源码 `e631936`，最终探针源码 `3e11b1a`。只改 tmp/833 与本岗文档，生产/DDL/接口/池/锁语义实际改动为零。BE 拥有 Runtime 候选和 HTTP races，root 拥有 fresh CI 准入和运行；本岗没有连接任何 MySQL、旧云或 13306，没有执行并发探针。

## 真实 MySQL 公开样本

root 已核官方 run40169575755/head81c909ad753aee7179ee0c464349a07273092fc0 的 artifact12589763159，ZIP123428字节/SHA3de3e3bcef1952f0736da762fcbe76f045eccf9e014a1ab90aba1e7bb80e8650。本岗只读取解压后的公开 mysql-before.json，独立核文件1387070字节/SHA b17f0fd502f9342ec11f9ae12064edccb11f139b3a90997c6be022f5ec333a9e，不另声称自己下载/核 ZIP。

环境为 Linux/Python3.12.15/MySQL+pymysql，SQLAlchemy2.1.6；observer SHA4edbf24779794a826bbe754ccad26890ea4c5c1d3f13f05778bad0e52ec307a9。真实 FastAPI HTTP 契约路径经 TestClient/ASGI/同步 worker，数据库为真实 CI MySQL；不是外部 Uvicorn/Nginx/socket/公网延迟测试。

离线脚本严格 request_id/operation 一对一 join 56/56，无 drop/pending/phase errors/cleanup errors。4 warmup、4 cProfile 不混入统计，48 measured 为每操作12次。完整机器摘要见 mysql-before-summary.json；所有时间为每请求阶段合计的均值，单位 ms，格内 wall / thread CPU，**不同阶段包含重叠，不能相加或当互斥占比**。

|阶段|getTask|listTasks|validateContractPayload|transitionTask|
|---|---:|---:|---:|---:|
|cursor execute inclusive|2.969 / 1.651|3.953 / 2.279|1.208 / .678|8.796 / 4.720|
|Session execute inclusive|4.776 / 3.293|6.110 / 4.242|2.001 / 1.378|12.932 / 8.793|
|Rows execute inclusive|5.416 / 3.933|7.246 / 5.378|2.246 / 1.621|14.505 / 10.364|
|mapping next inclusive|.202 / .184|.229 / .193|.065 / .057|.405 / .362|
|from_db_time codec|.068 / .049|.260 / .169|.027 / .020|.163 / .114|
|engine acquire inclusive|.463 / .291|.566 / .366|.235 / .139|.420 / .263|
|其中 pre_ping|.374 / .201|.457 / .255|.193 / .097|.333 / .175|
|Session commit inclusive|.747 / .448|.752 / .459|.351 / .218|4.225 / .469|
|其中 DBAPI commit|.330 / .164|.317 / .159|.155 / .083|3.785 / .165|
|DBAPI rollback（含 reset）|.261 / .124|.259 / .120|.120 / .057|.278 / .138|
|UoW exit inclusive|.832 / .532|.844 / .552|.390 / .257|4.321 / .565|

- 每请求 cursor SQL 数依次9、10、4、27或29（各6次）。前三组全 SELECT；transition 平均28 cursor事件/26 Session execute，源码savepoint/release也经过cursor，不能把两者计数差当漏采。读取映射行分别9、28、4、21或22；mapping next 另有正常 StopIteration，不等于行数。
- getTask/listTasks 各两次 session/user/membership/project 读取，不删除或缓存这些实时鉴权来减少次数。listTasks 两个 tasks SELECT 对应页和count；没有据此认定 N+1。contract 是单 UoW/4 SELECT，不经过 Workflow transition，锁候选不覆盖它。
- transition 六次 BLOCK、六次 UNBLOCK（从公开驱动循环核对，observer 本身不记录 action/body）；项目/依赖相关形状数随 action 不同。12次各保留 audit/outbox/idempotency insert 和 task/idempotency update；未建议删除审计。
- 获取次数2/2/1/2，ping次数相同。实际池 QueuePool size5+overflow10、timeout10、recycle1800、pre_ping=true。快照在 dispose 后，因此 checkedin0/checkedout0/overflow-5 是结束状态，不能推断期间无连接。fixture 先已连接，observer 后安装，physical connect 和 DBAPI timeout profiles 没采到，保持未知。
- cursor 在 PyMySQL buffered 模式可含网络取原始行；mapping/codec 仅后续消费。Rows/Session/cursor相减不命名“纯SQLAlchemy/Python”或纯锁等待。transition commit 的 wall 大于 CPU，是本次样本里的非线程CPU时间，未采 fsync/服务器/锁因果数据，不能证明是哪一种等待。

## 项目 S 候选的审查结果

仅 START/UNBLOCK/REWORK 将项目门 X 改 S 可以形成边界明确的候选：写图/成员/迭代/分配仍先 X，候选全程不得升级项目锁；成员和目标/前驱锁不删。项目 S、members S 和 target+predecessors X 一直持至提交，REWORK capacity 与成员变更不会越过项目门。门前 authenticate 普通 RC 读不提供稳定授权，门后 members S 的 active/role 重查必须保留。

前驱 rollback 若先锁/提交，等候 START 应读到最新回滚状态；若 START 先持前驱 X，rollback 应等待。这保证守门决策的线性化，不保证前驱今后不会回滚。目标/前驱 X 集合不相交的两个请求才有机会并行，共同前驱仍串行。FK 的 project/task 隐式 S 与已有 S/X 兼容仍需真实成功业务写路径验证，不能只看显式 SQL。

**未证明的风险**：批量 SELECT 的 sorted IN / ORDER BY id 不等于 InnoDB 实际取锁全序。不同 optimizer/index/数据分布可能改变遍历；原 project X 掩盖了新并发竞争。EXPLAIN/持锁清单和有限并发通过仅是观测，不构成全域无死锁证明。若需要严格全序，逐个 ascending 唯一键锁是另一个 owner 决策，会增加SQL和规模；本岗没有自行实现。InnoDB deadlock rollback 保原子性也不表示正式零错误目标已满足。

## 已交付但尚未运行 MySQL 的驱动

`tmp/833_database_performance/833_mysql_lock_probe.py`，SHA46dc00a57ff79ec51c0d8bcc92dd32c5bdcb76e794c8c9417c89bbb2c42256fb。只接受 CI=true/显式flag/localhost/t44_diagnostics，拒13306；使用冻结生产表迁移后的新service，自建独有 fixture不清表，直接DB合成状态不是完整批准业务历史。实际 Runtime.prepare/authenticate/locked_scope、Rows/UoW，两个不同 physical connection，第三连接查 P_S；Event持事务、精确 MySQL requesting→blocking connection/table/index wait边，parallel还要求观察到两个 projects RECORD GRANTED S，不以 sleep 未返回判阻塞。120秒上限；线程收尾/checkedout/dispose/异常类/数字MySQL码记录；无SQL正文、LOCK_DATA、token、DSN或绑定值。

六个开发case：不相交目标；target低/pred高与target高/pred低的不交集；graph writer实际project wait；两共同pred仍串行；pred先锁更新后读者观察最新state；同target同版本CAS一次成功一次VERSION_CONFLICT。EXPLAIN与持锁清单不是取锁顺序追踪。BE独立负责HTTP业务/角色/错误码/审计/撤权/capacity races，这些低层case不替代它。baseline参数update/原Runtime SHA8802416ee003a464a8433eed80890a1c2069550ff4717ca5e07a10cf2b840b48，candidate需root/BE提供新hash且参数share；源码本身不注入候选。

## 本地工具验证与原失败

- 离线join实际完成，输出 mysql-before-summary.json。8个本地工具检查覆盖 measured/profile分隔、重复/缺失/operation/drop/pending/cleanup拒绝、非CI gate在无效URL解析前拒绝，以及已有输出字节不被第二次运行覆盖；不是MySQL并发case通过。
- 首轮7pass/1fail为测试把 subprocess stderr bytes 与 str比较导致TypeError，原tool-junit.xml保留；补text=True，8pass见tool-final-junit.xml；最终3e11b1a源同8pass0.40s，tool-final-v2-junit.xml。不把重复运行称24个独立测试。
- 新三脚本Ruff check最终通过，format只处理新脚本，生产源码未格式化。只读路径猜测 store.py/unit_of_work.py、835glob、diagnostics.yml 不存在的退出保留在verification记录，未当产品问题。
- 实际prompt为 ROLE-database-MYSQL-GRAPH-20261025-v1，见prompt.md。[GitHub Issue4评论6394606519](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6394606519)由connector实际发表，再对单一ID精确GET，完整body与本地稿逐字相同；github-readback/verification保留实际响应与hash。

旧云三502/0完整正式组、规模超限、独立验收和本人研究报告出口均仍开放。本阶段提供定位与可执行验证路径，不称正式性能修复、共享锁准入或独立验收通过。
