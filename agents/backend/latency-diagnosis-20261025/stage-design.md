# source935最小stage包装器（先设计）

本阶段仅开发诊断工具，非产品改码或独立验收。根独占云UI，当前只写tmp/810_latency_diagnosis和本岗记录；本机只用指定backend/.venv解释器跑owned桩/SQLite，不读任意runtime凭据/独立私件，不接云或旧13306。根将另给新可抛schema、专用user/env、三角色/20任务/合法serviceP1，工具不猜ID、不DDL/seed。

包装原source935 create_app和原Factory/engine；入口按显式诊断开关、产品关键源SHA、精确DB/host/port声明及新schema前缀校验，模块导入不创建app/engine/连接。产品Runtime/API/SQL/响应状态/body/header不改；同步handler仍原线程执行，不新增工作线程/重试/事务。

外层ASGI只透明包receive/send：ingress、body最后帧返回、response-start、末body send返回、app返回与异常类；不保存消息body/headers/token。只显式x-t44-diag-sample:1且有界选择记录，记录原X-Request-ID及原route operationId。同步handler时钟在真正worker线程，thread_cpu仅同一同步调用边界有效，不把async eventloop CPU算单请求CPU。原Server-Timing漏handler前和最后wire/render/send，工具分别补边界，不叫差值纯网络/排队。

SQLAlchemy监听只目标engine的before/after cursor及handle_error、checkout/checkin；不读SQL正文或bind，不写execution参数。原pool.connect包络包含checkout/建连/preping，不叫纯pool等待；另在该QueuePool的内部queue.get读取真正队列get耗时（含队列bookkeeping，非纯OS睡眠），若接口不存在必须明记UNAVAILABLE，不能填0。pool size/checkedin/checkedout/overflow为原方法非原子快照，checkin回调发生时点不冒“已归还后”。SQL相位与handler/Runtime相位inclusive重叠，不相加。

日志每worker单独O_EXCL|O_NOFOLLOW固定fd、0600，有界记录、无payload/DSN/SQL/binds，记录UTC+perf_ns和同线程CPU。测量开销非0，文件write在app返回后，单独测其耗时/失败；故不把诊断运行直接当正式延迟。观察/落盘异常不得替换原HTTP/SQL异常，必须在诊断终态标INVALID并由根判数据不可用。close恢复所有补丁/监听；lifespan与atexit双闭合幂等。

必要因果自测：透明ASGI逐字消息/错误同、body/线程/send顺序、并发请求ContextVar与ID不串；真实SQLite SQL events、真实QueuePool占用及1连接受控等待（无sleep推定成功，以Event释放）；异常路径保原异常、无敏感bind留痕、import无t44/app/连接。根source935容器Python3.12才执行新MySQL四路径1client×20及40/400短诊断，existing-event escalation不能用stub替代。400/600/270/零错正式门槛保持。

交付gzip+SHA的单JSON段≤18432字符，根可独立解压核hash。先最小源码checkpoint，再封实际红绿/命令/报告/prompt/Issue；不触发全CI/新依赖/新agent或云操作。
