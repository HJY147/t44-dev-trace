# a12 Python CPU 开发定位方案（执行前）

源固定 a12e9e70b963bacafda3242bb6d82e53ee912ff1。当前岗位工作树的执行文件与其一致，但migrations有历史差异，因此从Git准确对象导出完整backend/t44到全新TemporaryDirectory，并验证每个文件Git blob identity；不把岗位HEAD混称完整a12。工具仅在tmp/788/profile，产物在本目录；不修改产品或原生环境，不读tmp796、792、私有验收或测试用例。

最短可信路径为既有834开发夹具的全新内存SQLite + 生产SqlAlchemyUnitOfWork/RowsGateway + FastAPI TestClient实际同步handler。沿用夹具建库/初始化用户，不运行其旧实验、MySQL入口或测试断言。准确夹具源码SHA e0a49e630957268195adc6d6f1cd924bf6481b533f7c3c276b3e832b21aeba49。

诊断进程禁用真实socket connect及MySQL engine构造；显式注入新SQLite factory/Settings，不读取.env。准备3用户/1项目/1迭代/20任务，准备27次HTTP不计时。getTask、listTasks、validateContractPayload、transitionTask四路径分别：1次预热、20次无profiler计时、5次cProfile、1次调用形状观察；主样本108次，含准备总135次。transition用manager BLOCK/UNBLOCK真实CAS/version/audit/outbox/幂等路径，不用固定成功或重放替代写。

计时器在FastAPI真正同步worker线程使用thread_time_ns；cProfile同线程使用thread_time，独立阶段，不把其成本混入80次计时。pstats独占CPU分组可相加但须明示互斥分类；累计CPU仅用于调用链排序，不相加。单独4次shape调用观测RowsGateway.rows参数键/锁、authenticate次数，不记录SQL绑定值/token/正文；shape仪表不进入计时和profile阶段。

先看函数独占/累计CPU及调用次数，再考虑局部候选：重复wire、schema引用遍历、SQLAlchemy表达式/缓存键构建、同请求认证上下文加载。禁止把旧15行委托、OperationPlan+14或validator构造缓存0.136ms重新包装成新收益。候选需要保留授权时序、读提交可见性、项目/任务锁顺序、CAS、幂等、审计、提交前schema与HTTP响应schema；预计净行数是静态估算，不是cloc达标或云性能收益。

SQLite不代表MySQL执行/锁/网络成本，Mac低压profile不解释400并发云根因，不是400/600秒/P95验收。真实输出、失败、源码/工具hash、依赖版本与限制一并保存。
