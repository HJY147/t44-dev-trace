# 同15连接峰值的保留池ABBA：数据库岗工具设计

数据库AI；实际派工ROLE-database-POOL-RETENTION-v1。基点2a0f091（含backend ff7ffa8），生产应用精确bc5aef9c62393134582affb7a690acb33ac2b833，根先行设计61b23e6。本阶段只设计、源码核对和955工具；未获实际执行窗口，不运行HTTP/SQL/负载。

## 锁定源码与可证伪假设

backend/requirements.lock与实际既有backend/.venv均SQLAlchemy2.1.6。本机pool/impl.py和base.py与官方rel_2_1_6 raw源逐字/hash相同，路径/摘要/方法行号见source-verification.json。首次系统CA检索失败，随后使用既有certifi CA且保持TLS验证完成核对，未跳过证书校验。

QueuePool懒建连，pool_size为返还队列最大保留数，_do_return_conn在队列已满时close本次返还record并减少overflow；不为某条连接永久贴“原始溢出”标签。_do_get与计数保护共同限制pool_size+max_overflow；dispose只关闭已归还的连接，不能保证替调用方关闭仍借出的连接，故结束必须checkedout=0后dispose并观察关闭。依据[官方池文档](https://docs.sqlalchemy.org/en/21/core/pooling.html)、[精确tag实现](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_1_6/lib/sqlalchemy/pool/impl.py)及[记录关闭实现](https://github.com/sqlalchemy/sqlalchemy/blob/rel_2_1_6/lib/sqlalchemy/pool/base.py)。

A=(pool_size5,max_overflow10)，B=(15,0)，每段一个engine/一个worker，因此负载期间单段总峰值预算仍15。B懒建最多保留15，可能减少反复归还/建连，代价是更多空闲会话/内存；不测服务端每连接内存，不声称成本为零。原公开并发32的211次新连仅是其短段事实，acquire含池内部/建连/初始化/ping/调度，不能叫纯等待或正式三组根因。

## 955最小扩展

- 新增mode=pool-abba复用原orchestrate的子进程/客户端/观测器；只接受A/B标签，在timings子进程本地dataclasses.replace(db,pool_size=...,max_overflow=...)，不修改MySQLSettings默认值、Settings、生产文件、SQL/锁/线程或全局参数。
- 固定顺序A1/B1/B2/A2。每段新server/engine，先32并发1秒warmup，再同样32并发4秒steady；每个client仍轮转原3候选。预热与稳态分开文件/标签/计数，不删预热连接成本。只读原私密fixture，不bootstrap/seed/清库/重建会话。
- 复用原逐请求acquire inclusive wall+同线程CPU、runtime/endpoint/SQL等观测；增加仅工具内DBAPI connect/do_ping/do_close包装，记录调用是否异常、wall/线程CPU、warmup/steady/startup/cleanup标签。close是实际dialect->DBAPI关闭调用观测，不把pool checkout当新建；清理关闭单列，不计入稳态关闭。
- 记录真实池有效值、checked-in/checked-out、物理连接观测峰值；每段结束先核checkedout0再dispose，元数据与原件保留。超过15、缺request_id关联、丢记录、类别错误/结构化错误、未知阶段或不完整清理标失败，不能挑有效请求掩盖。
- 每段导出client请求/类别/status/error_code/异常类、nearest-rank P95和成功吞吐，server关联与acquire wall/线程CPU、DBAPI各阶段计数、版本/机器/CPU/UTC/source/resource hash。P95四段逐项报告，不平均，不作统计显著性/正式270ms验收。

## 受限执行及停止

实际比较须等root明确窗口，当前仅就绪。只t44_profile、127.0.0.1:18083和1worker；env从既有私密profile-environment.json读取并覆盖PYTHONPATH为本树backend，fixture为原公开回执指定的bc5-contract-diagnostic-01/bootstrap/fixture.json，值不输出。启动前与每段前检查端口空闲、本库其他连接0；预检连接先dispose再启动负载，避免另加第16连接。仅过滤本库PROCESSLIST，不探别库。

工具先commit，生产/冻结/955脏树拒绝执行，生产backend/t44须逐字等于bc5。一次控制器墙时≤120秒；子进程timeout留10秒清理，server自身计时退出，finally TERM→有界wait→必要kill；每段后及最终核端口/自有进程。任何错误停止本次ABBA，保存已完成与失败段，不自动重试/改参数/另跑profile。

预定命令（只路径，无凭据值）：由受控Python读私密env后subprocess调用既有backend-venv-python tmp/backend/955_perf_profile.py --execute-stage-b --mode pool-abba --fixture <原私密fixture> --output <本岗新ignored目录>。命令不接受seconds/concurrency覆盖ABBA固定值，不在argv放DSN/Token/正文；本阶段不执行此命令。

工具提交后只做离线导入/参数拒绝/真实QueuePool合成DBAPI连接生命周期验证，无HTTP/SQL/本机负载；应用净变更0，正式三组失败、源码规模6307/超1207与人工材料本人完成边界保留。工具/离线通过不等于ABBA已运行；实际结果另阶段commit与Issue4/3精确读回。
