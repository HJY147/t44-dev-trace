# P18 实际现场证据独立核验

结论：本轮 **direct 诊断范围性能及原40秒内400后置通过**。完整全门禁正式验收不在本轮可声称通过范围；原direct准备豁免保留。历史轮次结论不作修改。

独立测试角色在读取实际结果前冻结主清单和初态聚合清单（提交5f0e322b、fb6a87a8）。仅离线读取本次回收密文、冻结规格、验证工具和密钥；未执行SSH、云操作、HTTP、SUT或重跑，未读取作者自测、开发日志或模拟结果。AGENTS含历史交接摘要，仅作权限和岗位约束依据。结果不依赖wrapper退出码。

## 认证和身份

RUN `r30posttools18`，产品源 `bcec3326b40814fdb1922bbfea7c29473b47ba47`。回收密文274039561字节、SHA-256 `63aaaf6a98ba52a185dacb2dbe3c93e2cbe51a98e1219c57a3cd830e2d8fcc35`，与receipt一致。认证解密后20文件逐项字节数/hash匹配内部manifest，5项输入hash全部一致。产品源与归档source、bundle、import receipt和环境身份对应。冻结工具10项hash匹配；有效runtime base9cf747/postfeffb8/compiledff9505/boot7e9bfc与归档result完全对应，binding `af93a6ffd956c0a2ae86362a6a0e13db9be589e8cfde7335195020cc3a7401b7`一致。旧environment runtime标识不冒充有效组合。

原始加密流footer、计数、压缩流结束和producer停止校验完整：148487条记录、1546004220明文字节、271924201压缩字节，其中148186次exchange。全部响应wire可解析，HTTP状态与record一致，运行记录错误0。没有补写或使用模拟数据。

## 从认证raw独立重算

400客户端、60秒warmup、600秒steady，400客户端均有稳态完成请求。按steady内发起请求计算RTT最近秩P95（ceil(0.95*n)）；完成时间落入原十分钟桶计吞吐。升级接口按冻结OpenAPI接受202，其余200。

| 类别 | 稳态请求 | P95 ms | 门限 |
|---|---:|---:|---|
| query | 24705 | 58.994292 | ≤270 |
| transition | 49404 | 81.731685 | ≤270 |
| contract | 24716 | 99.951703 | ≤270 |
| escalation | 24710 | 85.548265 | ≤270 |

共123535次稳态请求，稳态错误0。十完成分钟桶：12325、12345、12106、12180、12248、12539、12443、12528、12436、12373，全部≥1000。重算四类count/P95与归档摘要一致；摘要没有替代raw计算。

400客户端首次query均state2；各state/version/owner与启动inventory匹配400/400。首次BLOCK前state2为400，HTTP200为400。独立逐响应检查transition身份/owner/version/state/blocked_from_state、contract返回和升级事件去重快照无违例。未将源码初始化声明作为现场初态证据。

## 原40秒后置

从最后认证任务快照比较最终GET，400/400一致。逐页审计检查task/project范围、页集合完整、成功transitionTask的actor身份及本轮所有transition audit_id覆盖，完整400/400；缺失预期审计0、快照不符0、后置错误0。超过原截止的响应一律排除，本轮晚响应0。最后后置响应在steady结束后29.380077379秒，400 owner均在29.384364253秒前完成；30秒drain余量没有计作40秒内成功。

归档timeline进一步对应9174次HTTP dispatch/exit和9174次validation enqueue/await exit、400 owner完成、ALL_OWNERS_DRAINED、GLOBAL_CONNECTIONS_CLOSED、POOL_STOPPED各1。writer/footer完整，未遗留结果计入成功。

## 可复核产物与边界

`RECOMPUTED.PUBLIC.json`保存独立重算聚合，`RECOMPUTE_OFFLINE.py`保存本次离线重算程序，`ARCHIVE_FILES.PUBLIC.json`列20文件字节与SHA，`POST_LIFECYCLE.PUBLIC.json`保存生命周期聚合。原始响应、任务ID、会话和密钥仅留本机私有目录，不公开。重算程序需要私有材料，不能仅凭PUBLIC报告重建原始数据。

本轮证明以上指定版本、单次现场回收材料内的指标与后置；未补做MQ交付、数据库总量或其他豁免/未观测的完整正式门禁。未独立连接现场核验机器资源，归档预算声明不等同实际8CPU/8GiB资源验收。
