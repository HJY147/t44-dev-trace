# 公共数据库链路与计时边界

实际操作者database AI。基bceb7ec5（产品13ac），无云/SSH/SUT/QA PRIVATE访问、无数据库参数降级。当前没有确认生产高尾主因，不宣称修复P95。

原p12配对APP计时覆盖handle内部，contract单UoW仍约940ms P95；p13另有API15–18cores/MySQL3–4与写IO约3200/s中性窗口。不同轮次不能合并成单轮因果证据。contract仅一UoW仍高尾，不支持把所有慢归咎多次commit。SQLAlchemy Session.begin是逻辑开始，真正连接通常第一次execute才获取；checkout事件在拿到池连接后发生，不能凭checkout事件独立计算池排队。pre_ping不经过普通SQL statement listener，关闭它会改变断连恢复，不凭推测关闭。

实现仅新增可关闭的数据库分段诊断。共享t44.diagnostics由backend owner提供，request-local ContextVar，无SQL文本/参数/账号日志。active时db.acquire包Session.connection，包含pool queue/connect/preping/isolation合计；db.execute_fetch是execute到fetch/解码结束，db.statements统计已开始execute的gateway操作。commit/rollback/close各记wall和同线程CPU。disabled不显式提前取连接或读取时钟。SQLAlchemy错误映射仍覆盖acquire失败；不改变RC、SQL、参数、锁、commit/uncertain/rollback与连接释放。

限制：acquire不是纯池排队；SQL墙时包括网络、服务端执行/锁/I/O与Python线程deschedule，不能直接当MySQL锁等待。close可能含pool reset。db.acquire + execute_fetch + commit虽可求有边界的小计，但不得再与其父runtime span累计相加。SQL表达式构造发生在_execute外，归上层business CPU。事务内savepoint提交及uncertain后的cleanup rollback不单独计时；db.statements不是线上的全部wire SQL数。真实细分仍需MySQL performance_schema statement/wait/fileIO/lock与池指标同步证据，当前不能归因于硬盘或CPU不足。

现有989_rows/993_foundation SQLite69项通过，5个合成observer边界测试通过（默认无acquire/无事件；active计数；acquire/execute错误映射rollback；CommitUncertain保持）。共享diagnostics.py测试时来自backend owner未提交工作区，精确SHA见SOURCE.PUBLIC.json；根集成其准确最终版本后仍须整体检查。未跑native MySQL/完整CI/正式400并发。

官方依据：[SQLAlchemy2.1 Pooling](https://docs.sqlalchemy.org/en/21/core/pooling.html)；[MySQL8.4 Performance Schema Summary Tables](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-summary-tables.html)。这些解释度量语义，不证明本项目主因。
