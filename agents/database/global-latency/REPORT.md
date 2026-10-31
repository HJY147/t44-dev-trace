# 公共数据库链路与计时边界

实际操作者database AI。基bceb7ec5（产品13ac），无云/SSH/SUT/QA PRIVATE访问、无数据库参数降级。当前没有确认生产高尾主因，不宣称修复P95。

原p12配对APP计时覆盖handle内部，contract单UoW仍约940ms P95；p13另有API15–18cores/MySQL3–4与写IO约3200/s中性窗口。不同轮次不能合并成单轮因果证据。contract仅一UoW仍高尾，不支持把所有慢归咎多次commit。SQLAlchemy Session.begin是逻辑开始，真正连接通常第一次execute才获取；checkout事件在拿到池连接后发生，不能凭checkout事件独立计算池排队。pre_ping不经过普通SQL statement listener，关闭它会改变断连恢复，不凭推测关闭。

实现仅新增可关闭的数据库分段诊断。共享t44.diagnostics由backend owner提供，request-local ContextVar，无SQL文本/参数/账号日志。active时db.acquire包Session.connection，包含pool queue/connect/preping/isolation合计；db.execute_fetch是execute到fetch/解码结束，db.statements统计已开始execute的gateway操作。commit/rollback/close各记wall和同线程CPU。disabled不显式提前取连接或读取时钟。SQLAlchemy错误映射仍覆盖acquire失败；不改变RC、SQL、参数、锁、commit/uncertain/rollback与连接释放。

限制：acquire不是纯池排队；SQL墙时包括网络、服务端执行/锁/I/O与Python线程deschedule，不能直接当MySQL锁等待。close可能含pool reset。db.acquire + execute_fetch + commit虽可求有边界的小计，但不得再与其父runtime span累计相加。SQL表达式构造发生在_execute外，归上层business CPU。事务内savepoint提交及uncertain后的cleanup rollback不单独计时；db.statements不是线上的全部wire SQL数。真实细分仍需MySQL performance_schema statement/wait/fileIO/lock与池指标同步证据，当前不能归因于硬盘或CPU不足。

现有989_rows/993_foundation SQLite69项通过，5个合成observer边界测试通过（默认无acquire/无事件；active计数；acquire/execute错误映射rollback；CommitUncertain保持）。共享diagnostics.py测试时来自backend owner未提交工作区，精确SHA见SOURCE.PUBLIC.json；根集成其准确最终版本后仍须整体检查。未跑native MySQL/完整CI/正式400并发。

官方依据：[SQLAlchemy2.1 Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)；[MySQL8.4 Performance Schema Summary Tables](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-summary-tables.html)。这些解释度量语义，不证明本项目主因。

## 后续GET候选原生RC检查（独立于初始计时提交）

backend实际dc556cd3候选Runtime SHA84309825b2e0a214130a0871cd493773aab07f36721dddf45311c9312e68345a：GET同一个RC事务中仍两次authenticate，中间validate。自建getrc1 socket-only MySQL8.4.11，原DDL+10任务最小seed，四项真实Runtime检查通过：validate期间另一个连接提交session revoke→401 TOKEN_REVOKED；成员inactive→403 PROJECT_ACCESS_DENIED；自然expiry跨界→401 TOKEN_EXPIRED；validate期间revoke且抛输入错误→422 PARAMETER_INVALID优先保持。驱动错误空，实际隔离READ-COMMITTED（server默认RR字段不是连接隔离），durability1/1。finally shutdown0/socket消失，无云/HTTP/完整suite/性能运行。SOURCE.PUBLIC.json为前一诊断提交的历史快照，native当前证据另见getrc1.PUBLIC.json与native_get_rc.py。

这证明有限真实RC语义反例未退化，不证明吞吐/P95改善。该候选持连接跨输入校验，可能增加连接占用；应联合db.acquire与validate wall/CPU证据决定，不把checkout/commit2→1当全局根因已解决。

## 当前合并源小型native HTTP分段观察

bf1de3ec的五个backend文件与e07eff0d DB文件在独立临时源码快照合并，全部文件SHA见NATIVE_SEGMENTS_SOURCE.PUBLIC.json。自建getsegments1 socket-only MySQL8.4.11/RC/durability1/1，原DDL及10任务seed。真实FastAPI create_app注入真实SqlAlchemy UoW+TestClient，原HTTP helper执行完整请求/响应schema。15项顺序观测（GET、contract、transition各5），另clockfault GET1和default-off GET1，共17HTTP；无HTTP监听器/TCP/TLS/Nginx/并发压力。HTTP engine为socket定制pool32/maxoverflow0，无pre_ping；与生产engine构造/池配置不同，不能据此测生产checkout/网络尾延迟。所有请求200且schema通过。

五样本handle.wall中位数GET2.291ms、contract1.186ms、transition7.190ms；只报告本地中位，不报告P95、不当生产根因。GET/contract SQLgateway计数9/4、commit1/1；BLOCK首样本24 gateway operations/commit2（含DML，不能叫24SELECT）。原始Server-Timing及client.wall在getsegments1.PUBLIC.json；NATIVE_MEDIANS.PUBLIC.json仅由这些数值派生。父runtime/handle与子SQL/commit span有嵌套，不求和或用各自中位组成百分比。

人工工具校准另用pool1/pre_ping=True的socket engine：刻意持唯一连接50ms→db.acquire52.873ms、threadCPU0.092ms；刻意SELECT SLEEP50ms→db.execute_fetch55.420ms、threadCPU0.311ms。这只是验证计时边界能将已知等待分开，不证明生产发生这两种等待。

诊断clock抛错时真实GET仍200，实际数据库update成功commit且重查version+1；没有误判CommitUncertain。另合成counter storage抛错时UoW commit1/rollback0/close1/stateclosed保持。default-off响应没有diag字段。运行原有Starlette/httpx兼容warning保留，不为刷绿换库。原生驱动错误空，finally server shutdown0/socket消失。无云/旧PRIVATE访问，未重复旧4项RC测试，没有正式性能通过或根因结论。
