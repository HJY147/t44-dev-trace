# 原生应用有限能力证据

实际应用SUT：`bc5aef9c62393134582affb7a690acb33ac2b833`；成功运行的部署实现：`0a6da88c404c04515c3c07039f0e231908fddc0e`。归档提交另行标记，不能代替实际运行源。

| 入口 | 事实与边界 |
| --- | --- |
| dependency-driver-attempt2.json | 锁hash安装、pipcheck、frozen frontend、类型检查/构建真实11命令exit0；attempt1快速进程竞态原失败另存 |
| run1-analysis.json / application-driver-run1.json | 原exit1/cleanupfalse；两completed扫描间隔60.383994s、API4workers/UIproxy/TTL300/flock为局部真；DTO误解析和shutdown CLI异常保留 |
| run1-database-delivery.json | scan1/2精确关联16事件→16confirmed outbox→26通知，各收件人集合相符/fallback0；首轮实际两Pika连接raw gzip与离线红绿另存 |
| run1-post-stop-absence.json | 首轮后置PID/端口gone单列，不倒填原stop/cleanup成功 |
| application-driver-run2.json / run2-capability.json | 第二fresh环境真实exit0/cycletrue/cleanuptrue；新扫描3/4间隔60.303070s、轮换4→5后的scan5完成、锁持有、API4worker/HTTP UI代理、全会话回收/全停 |
| run2-shutdown.raw.*.gz | 官方shutdown --no-wait实际CLI0/markertrue，随后独立Rabbit退出/EPMD空再停机；保留原字节和SHA |
| 871-run1-correction.* / 873-affected-final.* | 23项本岗合成守卫及3项受影响broker停机守卫通过，原错误实现红绿保留，无关phase1守卫未刷次数 |
| private-receipt-index.json / final-secret-scan.json | 私密原回执SHA索引、公开/私密非秘密输出与压缩解码literal扫描范围hash；秘密和dump不提交/读取 |

二轮只读复核首轮既有16个eventIDs/26通知，当前manager鉴权API可读对应10个通知ID；明确不宣称二轮新publish。全过程没有迁移、reset、reseed、DDL、直接SQL改业务/去重。所有新端口已无监听，旧5173/18080/5175/18084/5176/18089/13306监听PID/地址前后逐项相同。

仅本地开发部署能力与HTTP UI/proxy验证；未做完整浏览器业务、独立验收、性能、云或生产安全批准。正常AMQP证据来自精确Pika源、实际连接及发布确认/通知关联，没有另查list_bindings表。原staging路径仍为plan-reason-api/source/backend，owner副本实际绑定本run/bc5a；未捕获staging运行前后字节hash，不额外声称该证明。所有部署输入、源码和拥有权仍需后续根明确绑定，当前保持停机。
