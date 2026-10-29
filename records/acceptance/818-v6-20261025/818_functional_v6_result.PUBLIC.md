# 818 functional-only 单次执行结果

本次业务验收结论：**NOT_PROVEN**。保留全部14项原始 case 状态：PASS 0、FAIL 0、NOT_PROVEN 14。

| 口径 | 数量 |
| --- | ---: |
| 计划 functional cases | 14 |
| 实际 SUT HTTP 请求 | 1 |
| 完整 HTTP 响应 | 1 |
| 已完成响应契约断言 | 0 |
| 完整 postconditions | 0 |
| fault / performance phase | 0 / 0 |
| 完整400 clients / 600秒正式组 | 0 |

唯一真实请求为 POST /projects，记录到完整 HTTP 201。随后中性 service/scheduler scope 交接未能在原120秒期限内证明完成，已完成 HTTP 原始结果保留；后续未继续发送 SUT 请求。未检视 provider 内部原因，未据此判定 SUT 业务缺陷。

原始 case 状态：

| Case | 原始状态 | HTTP请求 | 完整postconditions |
| --- | --- | ---: | ---: |
| F01 | NOT_PROVEN | 1 | 0 |
| F02 | NOT_PROVEN | 0 | 0 |
| F03 | NOT_PROVEN | 0 | 0 |
| F04 | NOT_PROVEN | 0 | 0 |
| F05 | NOT_PROVEN | 0 | 0 |
| F06 | NOT_PROVEN | 0 | 0 |
| F07 | NOT_PROVEN | 0 | 0 |
| F08 | NOT_PROVEN | 0 | 0 |
| F09 | NOT_PROVEN | 0 | 0 |
| F10 | NOT_PROVEN | 0 | 0 |
| F11 | NOT_PROVEN | 0 | 0 |
| F12 | NOT_PROVEN | 0 | 0 |
| F13 | NOT_PROVEN | 0 | 0 |
| F14 | NOT_PROVEN | 0 | 0 |

进程退出码0，仅表示冻结工具完成结果归档。08:43:36.703547 UTC 已结束，未越过08:44硬截止、未重跑、未清理、未改变冻结用例/oracle/阈值/等待条件。加密证据已完成认证恢复核验；原始请求、响应、credentials、keys与私有案例不公开。

保留可见副作用：新建 actual project ID 13；未发送创建任务请求。入场声明的12个已有项目未清理；未完成后续权威快照查询。

源 SHA：c8cea7e82805de5283ce67501769fa9a4efc1047。完整运行身份、逐项计数和 PUBLIC receipt/status 路径见同目录 JSON。
