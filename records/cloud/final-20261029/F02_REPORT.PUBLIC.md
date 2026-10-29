# F02 独立结果：测试工具初始化失败，业务验收未完成

运行标识 `r30finalf02`，实际记录时间为2026-10-29T15:43:02.800716Z至15:43:03.326325Z。被测源为 `356f29983c904e949245aedfad464efc1bf7b63d`，契约1.2.0。结论是 **INCOMPLETE / QA HARNESS SETUP FAILURE**，不能记为产品验收通过，也不据此登记产品缺陷。

## 已核事实

原结果保留：PASS 0、FAIL 1、UNEXECUTED 19，`blackbox_full_acceptance=false`。失败项为SETUP。`operation_count=37`仅表示HTTP操作被观察；多数来自无凭据负向请求，不代表37项业务功能通过。43条原始HTTP记录包含37次无凭据请求，均观察到401；另有4次200、1次403及初始化的1次422。这些有限观察不替代完整安全或功能验收。

SETUP发送 `POST /api/v1/projects/1/iterations`，请求体匹配冻结 `IterationCreate` Schema，但请求记录中没有 `Idempotency-Key`。冻结契约的该操作要求此请求头。服务实际响应422 `PARAMETER_INVALID`、`audit_id=16`、`violations=[]`；工具按成功201作断言而失败。响应未给出缺失字段级说明，不能声称服务器明确指出missing-key。可以确定的是：QA工具发送了不满足冻结契约的创建请求，因此本次失败不能证明有效业务请求被错误拒绝。

独立工具根因已由自己的源码和冻结契约确认：自动幂等头判断仅查 `parameter.name`，而契约通过本地 `$ref` 声明参数。初始化未得到迭代fixture，之后核心状态、依赖、评审、发布/回滚、故障、通知等19项保持未执行。37次无凭据观察后，auth组合用例也因缺迭代fixture未完整执行。

## 版本与证据

- 原功能工具SHA：`31933375c0a1029c3887f6f5755070ead57e7d474ec9f71dca39674986d1a50f`。
- 原环境派生文件SHA：`863c52d9e761a7d49ec25787c409bf50e2c75ef56f134624ffb7a8ae65825fe3`；实际max_seconds=249。
- backend config：`sha256:a3f4bf81c8275dc949a91485097cb210a06f3880b5476cb05dfd2f98018d192d`。
- source manifest：`50684876e08d74e8579e99b30cd3f53b676f5e4367cadbc3bfa610714ce6b088`。
- backend bundle manifest：`1ddafb7aaa1c552172cc5a0c0f48881412a8fa1fabbb400037854f4bba77a6a2`。
- F02原始导入收据SHA：`cb3e0d09847534791ea9c822c43b9b2e0912385b924f622351268500c7a520e5`。
- 冻结OpenAPI SHA：`6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478`。
- 原始功能证据SHA：`e1fabdcccf6e4b0230b63c1ef89019e193d3566d66bed2612950ebdc3e3acd5b`；65条记录已完整认证。
- 本地加密备份：22117字节，SHA `9ee4313809075be379c1a84d35a0879a96160b9a7b2f0b66f4e5c1095eff32d8`；6个内部文件解密后SHA全部核对，核验收据见 `F02_BACKUP_VERIFICATION.PUBLIC.json`。钥匙、会话、私有用例和日志未发表。

## 工具修正与剩余工作

原F02、原胶囊及原4a5工具交付清单保留，不追改旧结果。单独发布 `F_PARAM_FIX_01/`：只在自动幂等头判断前解析本地参数引用；冻结用例、业务断言、契约、产品和性能core均未改。新工具SHA `f877292eaf951ebf7609e23d7e010ce50d2d0cb7218a3f6f1a4dbf035037b453`。离线捕获38操作及1次显式key请求，18个必需幂等头操作与只读例外均符合冻结契约；未重跑SUT。

F03须使用真实新环境、独立运行目录和新的单次准入，不能复用已过期F02许可。F02没有正式400并发性能结果；性能、代码规模、覆盖率、CI门禁、人工留痕及其他未核范围均不得由本次结果代替。
