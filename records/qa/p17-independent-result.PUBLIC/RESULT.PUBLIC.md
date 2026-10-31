# P17 独立离线结果核验

结论 **NP：本轮未完成压测验收**。这是新鲜独立测试角色的离线解密核验；没有 SSH、云、HTTP、SUT、补验或重跑。清单在打开结果前冻结。没有读取开发日志、作者报告、提示词或自测脚本。AGENTS.md顶部历史摘要不可避免随规则读取，未作为本轮结果证据。

## 身份与完整性

RUN `r30posttools17`。source manifest、backend bundle manifest、import receipt 与结果均指向产品 `bcec3326b40814fdb1922bbfea7c29473b47ba47`。源清单及bundle清单SHA256分别为 `52d74144437ad77140ccb8cab44bf82c4826e4ba00b9d2dc04895f35100bcfd7`、`3e09cc1bfe5074832fbb61bc2e500f5b27bc23a987c3d68f9744dd650c126d29`，与结果identity相符。PUBLIC manifest所列10份PRIVATE文件逐一哈希匹配；四件实际runtime及binding与CLI_CONTRACT相符。identity.runtime_sha256是另一个字段，不能当作实际执行runtime单件摘要；实际四件身份见EVIDENCE。

494900字节密文SHA256 `1af91c64a99169f5ea12c0fce2a20872fb941e33cea6cf4115a26e12aaec2ae8` 与回执一致。verify_backup认证解密、压缩tar摘要、内部20文件完整集合和各文件摘要均通过。verify_raw逐帧认证、gzip结束、记录/字节/接收计数及完整footer通过：410记录、2326792明文字节、411433压缩字节。原始记录类型：406 exchange、cohort_start/load_resource/client_stop/result各1。result内writer计数是在最终result/footer前采样，不能代替最终认证流计数。

## 实际阶段与失败

cohort_start为2026-10-31T11:09:54.477064Z，400客户端各有query记录，说明已释放cohort并实际进入预热。406 exchange全部在warmup：400 query、5 transition、1 contract；其中1次错误。没有steady或postcheck exchange。

首次失败是transition HTTP 409，业务code `STATE_CONFLICT`、message `State conflict`，模板 `POST /api/v1/projects/{project_id}/tasks/{task_id}/transitions`。请求从11:09:54.615034Z至11:09:54.665249Z；expected_version=2086，响应current_version=null、current_state=3；前一query state=3/version=2086。随后11:09:54.665305Z记录client_stop `ValueError:ValueError:HTTP_409`，并设置全局stop。

冻结工具源码对应路径为 `post_runtime.py::_call_post` 第124行HTTP状态断言，第134–142行捕获、记录并重抛；继承的 `runtime.py::client` 第335–336行设置stop并记录client_stop。此为原始错误记录与源码控制流映射；备份中没有Python traceback文件，不把映射冒充实际回收的异常栈。没有SUT内部诊断证据，无法判断更深层业务状态来源或产品缺陷归因。

DRAIN_START monotonic_ns=150707129429，ALL_OWNERS_DRAINED=151532619849，GLOBAL_CONNECTIONS_CLOSED=151532643598。结果实际观测1.013942096秒。FINISHED仅表示工具清理结束；外层exit=2、clients_started=400均不是完整测量成功。

## 门禁逐项结论

| 项目 | 结论 | 证据 |
|---|---|---|
| 密文/文件/原始流认证与身份 | PASS | 上述本地核验 |
| 预热期间零请求异常 | FAIL（观测事实） | 1次HTTP409，触发全局停止 |
| 400 clients/60秒预热+600秒稳态完整测量 | NP | 启动400，实际仅约1.014秒 |
| 四类稳态P95≤270ms | NP | 四类稳态count=0/P95=null |
| 十个完成分钟桶各≥1000 | NP | 十桶均0，未形成稳态时间窗 |
| 稳态零错误 | NP | 稳态没有发生，不能以0样本断言通过 |
| 最终快照400/完整审计400，40秒预算 | NP | postconditions空，postjobs=0；未进入后置，无超时证据 |
| 整体正式验收 | NP | diagnostic classification且测量未完成 |

不把预热409直接等同于产品性能FAIL，不把未执行后置判为40秒预算失败。本轮没有可报告的稳态性能值；P17后置修复的现场有效性也无法判断。两台可停机的信息已由总协调交付，本岗不要求保活，不提出自动重跑。

## 核验操作与边界

本地调用冻结 `verify_backup.py BACKUP KEY --extract-dir PRIVATE_DIR`，随后 `verify_raw.verify(evidence,key,require_complete=True)`，独立按record/phase/class聚合并仅输出允许的脱敏定位字段。两项均成功。密钥、解密目录、认证原始请求响应与测试案例不随PUBLIC产物提交。仅交付本报告、冻结清单、脱敏统计及摘要。
