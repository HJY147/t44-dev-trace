# 独立验收 v3：机械绑定阶段回执

本段所有列出运行均未进入业务验收或正式负载，不能作产品通过、产品失败或性能结论。

精确 SUT：`bc5aef9c62393134582affb7a690acb33ac2b833`。环境基线：`f118f9dd35bc2cde69affe235f5a499d03a396fc`。原 H 保留；本段机械 H2 为 `edeadc0d96c418d6034e84011c594c95fd4b7e4e`。

| 范围 | 运行 | 环境就绪 | 入口退出码 | 最终恢复 |
| --- | --- | --- | --- | --- |
| functional | [40025696201](https://github.com/HJY147/t44-dev-trace/actions/runs/40025696201) | True | 2 | True |
| operational-faults | [40025699738](https://github.com/HJY147/t44-dev-trace/actions/runs/40025699738) | True | 1 | True |
| formal-transition | [40025704012](https://github.com/HJY147/t44-dev-trace/actions/runs/40025704012) | True | 1 | True |
| formal-contract | [40025707671](https://github.com/HJY147/t44-dev-trace/actions/runs/40025707671) | True | 1 | True |
| formal-escalation | [40025712404](https://github.com/HJY147/t44-dev-trace/actions/runs/40025712404) | True | 1 | True |

五段均在账号初始化控制边界阻塞：实际返回码 0、stdout 70 字节、stderr 0 字节，stdout 非空且不是可确定的 JSON。驱动保留阻塞，没有靠忽略不确定输出制造成功。26 个功能整例、4 个可执行运维故障整例和3个正式性能组仍未完成；600秒稳态负载均未开始。最终恢复为 true 仅说明该次环境恢复回执，不算故障用例通过。

另已在完全替换传输的离线合成 wire 样例上通过24项独立驱动投影及失败边界校验，不接触网络/数据库/应用，不算 SUT 用例。按原冻结契约修正任务 factory 的 `data.task` 投影；原失败留存。机械 H3 为 `68ce0174d4f1a3f7430d9e9affdab0a1af833af1`，原功能、故障、正式引擎及入口文件不改，浏览器业务断言不改。

下一步依赖明确的中性控制 stdout 语义或 JSON-only 返回；当前不会重复启动同一未解决阻塞。浏览器范围另行执行和报告，不混入本表。

仅此 MD 与同名 JSON 明确公开。原始案例、驱动、日志、密文解密内容均由测试岗私存，没有人工参与或人工批准声明。
