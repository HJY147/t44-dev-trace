# 请求 CPU 与阶段诊断设计（实施前）

后端 AI；基线 ade5e4c1998b4c2f014afde8c011645c6c5a7412。仅使用云839具名公开结论，不读取独立用例/日志/私有凭据。旧云0完整组、3个502、短窗超时及6316源码行继续保持未达标。

目标是找实际成本，不先假设缓存validator、去掉授权/验证或增加worker就能解决。生产代码本阶段不改。新显式运行诊断在 tmp/834_backend_performance；文件导入不启动HTTP/DB。

输入为公开合成账号/单项目/20任务、固定合法计划与4条路径：getTask、listTasks(page_size20)、validateContractPayload(category1)、block/unblock。先准备、不计入测量；各一条预热、每路径12条顺序计量，最后每路径一条单独cProfile。完全不是400并发/600秒/吞吐验收。

仪表在APIRoute.dependant.call的真实同步handle线程中启动，保留原函数和signature。记录request_id、UTC、perf_counter_ns、thread_time_ns。Runtime.execute、validate_request、Business.dispatch/validate_data、schema violations/validator构造、wire的临时包裹保留包含层级；exclusive只减直接子跨度，inclusive不能跨层相加。客户端wall单独记录，差值不叫纯排队时间。cProfile使用thread_time，只在最后独立样本启用，不能把它的延迟当无开销指标。

SQLite模式只本进程内存库及实际生产Gateway/HTTP适配层；缺MySQL锁/网络等。MySQL模式另要求CI=true、--allow-mysql-ci、显式DATABASE_URL/T44_DATABASE与期望新schema t44_perf_20261025一致且localhost；root工作流先建迁schema，驱动只读空库预检后初始化合成账号/实际HTTP。不读取任何旧云env或可选私有凭据文件。

数据库岗提供诊断Observer的install(engine)、request(operation,request_id=uuid)、snapshot接口；只记录statement形状/阶段和关联ID，不存参数、token或正文。若观察器尚未可用，首轮API纯CPU可先不安装，后续MySQL组合须明确装载的精确模块SHA。

工具提交后才执行；要求明确source SHA且实际导入源与Git字节相同。输出在本岗目录以O_EXCL/O_NOFOLLOW0600保留固定fd，失败写状态、保留原件、不重写旧结果。记录版本/源码hash/样本数、方法、所有实际异常。取得数据后再另设计最小热点修复和必要等价回归；不让本地CPU结果冒云根因或正式通过。
