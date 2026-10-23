# bc5 契约入口一次开发诊断：设计先行

作者/预定执行者：后端 AI。基点3b9c907c，应用固定bc5aef9c62393134582affb7a690acb33ac2b833；本轮只改955工具和本岗记录。此文件提交时未运行。

## 问题与范围

只读总协调明确公开的stage06-formal-blackbox.md/json：三正式组P95 9512/3086/8272ms，失败1021/0/2；错误正文/同次服务资源未知。未跟其私密路径或驱动引用。此诊断仅契约校验、单worker、自有MySQL与本机同进程客户端，不能解释三正式组或证明270ms达标。

按原955一次orchestrate：baseline原API不包裹、timings仅进程内观测、profile仅3个独立候选请求；前两段各1/8/32并发，各3秒；profile单并发最多3请求、3秒截止。baseline前必要新增一个本岗合成项目/成员/迭代/任务及登录session，不重seed/清库；另3请求sanity必须HTTP200、valid=true、violations为空、business_guards_executed=false。三候选仍createTask/transitionTask/createReleaseAssessment结构，不是三个正式接口负载。160秒总controller截止、子进程finally正常收尾，仅自有18083/进程。

## 工具静态差异与观测边界

原955 SHA d5a984eb10cd2d15d139f2b9f64b389fad37b5acecf7ada688dedec3f80a7b29。当前Runtime仍保留原authorize/claim等入口，因此原包装兼容；契约单UoW实际不会调用authorize/claim。新增只读计时/计数，不改输入或返回值：

- client记录>=400时顶层结构化code，仅异常类；不存响应body、参数、Token/口令、完整SQL。
- FastAPI routing.run_in_threadpool派发前→包装同步入口计observed dispatch-to-entry，ContextVar由AnyIO传播；每目标请求须恰一入口、runtime记录须存在。它含limiter等待、调度和线程启动，不能叫纯队列；缺失/多入口不当有效分解。
- authenticate、schema构造、原HTTP schema遍历/业务dispatch/runtime均记录inclusive wall及同线程CPU，嵌套值不相加。原始ASGI接收await只计wall，包含事件循环/消息等待，不当网络纯时延。
- engine.connect仍是checkout+可能池等待+新建连接+初始化+pre_ping等整体；dialect.connect/pre_ping另计inclusive，pool checkout只计次数。其差值仍混有初始化/池内部等，不能冒充poolwait。dialect.commit/rollback单独计调用，cursor事件不含这些协议命令或COM_PING/DBAPI直接初始化SQL。
- SQL仅cursor实际执行的动词类别/次数/wall/线程CPU/错误，不保存语句、参数；cursor wall含网络/服务端执行/锁等待，不能进一步精确拆SQL锁。cProfile默认elapsed inclusive时间，热点重叠，不能称exclusive CPU或将其相加。
- server process CPU/wall为整个段（含启动/空闲/登录bootstrap等）；client另计，不能套成逐请求CPU份额。逐请求runtime threadCPU可与runtime wall比较，剩余仅未归因等待/调度，非全是SQL。

源/import/resource hash必须绑定工具commit并与bc5对应Git对象核对。读取私密profile-environment.json后显式覆盖PYTHONPATH为本树backend；数据库须双重为t44_profile。先检查18083无监听；仅对本库连接作information_schema.PROCESSLIST计数（排除自身），非零即停，不探测其他库。既有0600账号只读；fixture/token只在ignored私密输出，不提交。公件显式挑选原metadata/jsonl/pstats及清单；所有失败保留，不重复整批。

## 执行形式（设计提交时未执行）

单次控制器从私密env读取设置，覆PYTHONPATH后调用：

`<backend-venv-python> tmp/backend/955_perf_profile.py --execute-stage-b --mode orchestrate --seconds 3 --credentials <既有0600profile-credentials.json> --output <ignored本岗新目录>`

实际argv无DSN；外围捕获exit与UTC、占用预检和生产字节核验，最终只查自有18083是否关闭。不启动930/870，不调SQL/锁/池/线程或生产，不把缺失503记已定位。结果若完整则离线按request_id关联client/server、nearest-rank P95、逐请求相同分母的phase均值/CPU与分类cProfile；若controller失败保留原件并仅解释可核子阶段。所有结论限定一次3秒开发诊断。
