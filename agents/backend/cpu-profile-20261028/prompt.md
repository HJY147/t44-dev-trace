# ROLE-backend-CPU-PROFILE-20261028-v1

来源：总协调真实派工及后续准入；操作者backend AI；不是用户亲自修改或独立测试。

实际任务原文：

> 新任务继续本地性能定位（云UI当前挂起，root在恢复/待用户刷新；不云操作）。P7 actual API CPU 10–12单核时间、MySQL~1.5，旧handlerCPU get11ms/contract7.6ms/transition23.8ms，不把高CPU直接当根因。请先读a12 current API/Runtime/persistence查询/JSON/wire路径，设计最短可信cProfile或py-spy开发诊断定位PythonCPU热点。如可用现有隔离SQLite/原生产SQLAlchemy路径开发示例做50–200真实业务调用CPU采样（不把SQLite性能当MySQL/云，严禁碰用户原生MySQL/旧tmp796数据/不改产品），给可审局部优化候选与语义守卫、预计净行变化；优先查重复schema编译/wire/查询构建/项目context加载，别重复已失败15行委托/OperationPlan+14/schema缓存0.136ms旧路线。可查看原root已发表 observer-summary projection(无私密)，禁止读792/private/测试用例。另新本岗profile子目录，自己四件commitpush。没有必要先新完整系统或新云；先真实可复核函数调用/CPU profile判断。不要把CPU单位/P95相加或低压CPU当正式400/600成绩。

实际后续总协调准入原文：

> 继续只做纯等价/构建CPU微测，不改DB产品。select(table)是可信零行结构候选，请给MySQL/SQLite编译SQL+绑定/结果列/锁/limit/order等价的具体原始证据与median CPU前后倍数，保留所有条款。root会单独交DB岗实现/回归，不污染当前a12 P7/P16对照。仅凭cProfile调用量不宣称性能已改善，真实A/B小测区分profile开销。

实际执行：先设计，Git精确导出a12并核51个文件，复用SHA固定的834开发夹具新内存SQLite，135 HTTP包含27准备/80无profiler计时/20独立cProfile/4预热/4shape。profile在实际worker线程计CPU；网络/MySQL禁用。发现select全列逐列构造后按后续准入做198对纯SQL/绑定/编译列签名及无profiler构建ABBA，不改产品。

改进理由：把inclusive与exclusive、profile与无profile、纯构建与HTTP/MySQL/云分开；不靠删安全检查或复用已否定路线。原始失败、warning、准确工具/产品/依赖hash及局限随原件保存。

产物：tmp/788/profile/三工具、本目录design/report/summary/verification/完整压缩原件及manifest、本岗WORKLOG/module/handoff追加。预计候选净0有效行，不称规模或性能通过。
