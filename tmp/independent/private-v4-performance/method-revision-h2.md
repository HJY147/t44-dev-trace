# H2：接触SUT后的显式准备方法修订

原H=9f8b5eab4061c14f1b7a314cd418c2663a6b0634及六个原attempt保持不动，正式状态仍NOT_RUN；已自审公开有限摘要提交05d3dbf27375c9532cb69eed3bb9062eb21a378c。此修订发生在观察到准备超时之后，不称首次盲测、原H完全相同或纯机械fix。

本文件仅覆盖原cases-and-criteria.md中的工具准备预算和失败路径证据方式；原文作为H1历史保留，其他全部业务设计、数据及正式性能要求不变。中性依据为217d89779440086ab727d280a0900efad36bd2c0的specs/changes/acceptance-preparation-budget-rfc.md，hash见inputs/source-hashes-h2.json。尚未收到实际1800运行能力准确绑定前，不提交无效请求。

## 明确差量

1. 初始fixture setup整体工具预算330秒→900秒。这是测试工具上限，非老师验收条件；不以其变化回填原attempt。
2. 仅phase=setup的HTTP端到端上限5秒→30秒，同时显式给底层HTTP客户端相同上限。warmup、steady（包括其中辅助操作）、postcheck全部仍5秒；无thinktime、无自动重试、无失败忽略。超时、非预期HTTP/契约/业务拒绝仍真实记录并中止准备，不能把它们变成成功。
3. 仅新建项目响应后保留已确认项目ID作为失败只读审计范围。不改项目、成员、人力、迭代、6000任务、9000依赖、15000评审/决定的生成内容/数量/顺序和40项目准备并发。
4. 准备异常时先取消并收齐尚在执行的兄弟准备协程，再SELECT-only观察已确认范围的项目/任务/依赖/评审/决定数量，记录DB和调用时间。没有人为settle sleep、重试或业务写；服务端未完成提交可能随后结束，因此快照有窗口局限。若创建已提交但响应丢失，未确认ID可能不在该范围，明确保持unknown边界。观察失败或scope未建立不填零。
5. 同一失败路径显式取runtime-metadata及选择性runtime-usage；保留实际退出/完整性/字段及unknown，不据finished标记推完整，不将Docker扣缓存内存称RSS或样本当全程峰值。原正式阶段的采样方法与调度不变。
6. 为输出区分H2，增加方法版本与工具预算元数据，引用H2中性输入hash清单。私钥仍只留本机ignored路径，原RSA接收证书沿用。

## 保持与证据

18段自有源码逐字节比较保持：Evidence类（原数据/统计/分位规则）、数据plan/assessment/transition、三个正式operation、worker、phase_run、judge、正式资源采样与只读postcheck、身份/键和响应验证辅助等。nested build_project业务工厂除新项目ID证据一行外逐字节保持。共享HTTP helper除明确的phase timeout补丁外逐字节保持；整个helper和整个harness并非同字节，不能泛称完全一致。证明清单在records/h2-byte-preservation-proof.json，离线AST与phase表达式检查在records/h2-static-check.json；这些是源差量核对，不是SUT性能通过。

正式仍400闭环用户，独立90秒预热（30秒爬升+60秒满用户），完整600秒稳态，P95≤270ms、有效吞吐每分钟≥1000、零非预期失败；所有请求采样/失败计数、固定数据规模、业务载荷和成功判据不减。每类/每源须新空环境，R/H2/SUT分别记录；原H六次不被复写。新环境harness_timeout拟1800秒、job40分钟；能力是否可用以新准确绑定与实际返回为准，1800/900也不是完成保证。

H2前已知道两源准备阶段的超时及部分吞吐，故存在事后方法修订局限。S1/S2在H2必须相同工具预算、完整同规则fixture与正式方法；不同hosted机器/背景条件仍限制性能归因。原H无正式稳态，不能以H2数据构造原H前后提升或改变原结论。仅续尚未运行的正式范围，真实准备业务拒绝或新异常仍按实际结束。
