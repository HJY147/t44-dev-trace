# r30manualp12 独立复核结论

**整体验收：NP／不接受。性能明确FAIL：四类P95均超过270ms；后置断言亦未全部完成。** 完整cohort仅证明原测量完成，不代表验收通过。

source为90b734f65ce6ee9f5c217e885bc7ea4857e32b48，另绑定已审schema supplement31bef8ab5b87feb864b18d58bd7e791dd96d41e20a05b5abe06a5d783648e8d8。实际触发2026-10-30T14:34:25.342503Z，早于本岗14:40:00Z准入截止；密封内本轮grant、environment与实际触发绑定复核一致。

| 项目 | 独立核验结果 |
| --- | --- |
| cohort与时间 | 400客户端；60秒预热，另计600秒稳态；592个稳态资源采样均alive400 |
| 请求计数 | 稳态内发起482100；稳态窗口内完成481700 |
| 分钟完成数 | 51019、50137、49161、48800、47990、45257、47295、47648、47263、47130；全部≥1000 |
| 稳态请求错误 | 0；独立实际响应wire检查错误0 |
| 后置请求错误 | 16：1个TimeoutError、15个RemoteDisconnected，全部属于postcheck |
| 后置完整性 | final task snapshot398/400；完整成功审计383/400；另有post_budget_not_observed1 |
| MQ投递后置 | 未观察；不得据本轮去重接口响应推定新通知投递通过 |

| 请求类 | 稳态样本数 | 独立复算P95(ms) | ≤270ms |
| --- | ---: | ---: | --- |
| query | 96410 | 1065.937272 | FAIL |
| transition | 192829 | 1622.151004 | FAIL |
| contract | 96432 | 1048.957214 | FAIL |
| escalation | 96429 | 1205.121100 | FAIL |

P95按原冻结工具定义：请求起点位于600秒稳态内，延迟为完整响应读取结束减请求开始，使用nearest-rank第ceil(0.95N)项；分钟吞吐按完成时点分桶。400个请求在稳态内发起、窗口结束后完成，因此样本总数与窗口内完成数相差400；未删改样本。并发口径为400个存活工作客户端，稳态HTTP在途采样范围131至400，不能表述为全程400个HTTP同时在途。

备份认证footer、压缩流SHA与53件全文件SHA全部通过。原始证据再次按原Seal认证解密，gzip完整结束，认证footer记录数与字节数一致：544965条records，其中544296条exchange；warmup57041、steady482100、postcheck5155。四类计数/P95、十个分钟桶、稳态错误计数与原工具逐值一致。独立另从实际响应wire核对HTTP状态、完整响应、业务错误封装、request-id/replay和contract/escalation核心结果。没有重新执行SUT。

后置398个成功task读取由原始exchange逐客户端复算确认；383个完整审计为原固定工具的完整审计断言计数。所有原断言未获满足，不能将零稳态错误或完整cohort写成整体验收通过。原工具独立结论亦为NP。

原result内raw_plain/compressed是写入其自身result记录之前的快照；认证footer比该快照分别多39413和30394字节，符合原写入顺序。本岗以认证footer及完整解压流核最终完整性，未改原result。

公开详细数值见同目录CORE_RECOMPUTED.PUBLIC.json和FINAL.PUBLIC.json；53文件封存完整性源为本地.agent-worktrees/.runtime/manual13-live/r30manualp12.753backup及其receipt，cipher SHA为a4fb290cf53003f958c798d72eaaf63a048bf3f675dfa575bc6802d7c6fcf6c0，压缩流SHA为651fc3e8af4d00d09206006e1d86507b559d432d4daf8980128553db0af84c01。解密原件、用例、密钥与分析脚本仅留本岗PRIVATE，不发布。

本报告只分析p12；历史p11由原封存保留，未读取其内容或用于本轮结论。结束后全部本地处理，无SSH/云访问，无重试、无继任测量，也未提出新优化或重测。
