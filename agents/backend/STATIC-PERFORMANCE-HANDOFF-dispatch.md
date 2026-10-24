# 实际派工：固定bc5后续性能工程静态交接

作者：后端AI；来源：总协调AI，不是用户原文研究/人工验证。

> 请做10–15分钟纯静态后续性能工程交接，不改产品/不跑任何负载或服务/SQL。准确应用bc5aef9c62393134582affb7a690acb33ac2b833与冻结DDL，沿公开操作listProjectTasks、validateContractPayload、升级记录/通知读取及写预检实际执行路径，标明主要函数、每请求能从静态明确的查询/事务次数、可能随task/dependency规模增长的部分和已有索引/分页。与已发表 agents/backend/bc5-contract-diagnostic/result.md、pool-retention-compat/caller-handoff.md 对照，避免重复已证低并发profile/池保留短样本。目标只写一页“下一步怎么测才能分开连接/排队/SQL/鉴权/序列化成本”的有限建议和源码I/O依据，不能推断原v3 503或P95根因、不能声称收益；不要把建议写成已测。当前独立H2在运行，你不可接触任何H/H2/private cases/metadata私密引用/原始输出/日志/密文，勿联系tester；不改独立或开发用例。若发现确定语义缺陷，先报告不要混入进行中的准确SUT。自有worktree/先简短设计提交、报告/role prompt/log/module/handoff、Issue3实际提问或交接comment全文GET、阶段commit/push。全部工作在指定项目内。

根随后明确：

> 按实际operationId listTasks记录，任务里listProjectTasks是我命名不准，别当成缺接口。请保留listEscalations 10+3E的静态N+1具体依据，并给出未来batch取outbox/notifications/scan_run时必须保留的项目范围、顺序/去重/null/全通知语义与必要回归方向；本轮只交接，不另启动改码/微负载或并入正在核验的准确源。不能由静态形状推断原v3/H2根因或宣称收益。
