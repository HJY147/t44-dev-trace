# P17 初始查询条件聚合

仅离线重新认证P17原始流，并读取其中400个初始warmup query响应；400个客户端各恰好一条，均HTTP200且无query错误。

| 观测字段 | 计数 |
|---|---:|
| transition任务state=2 | 232 |
| transition任务state=3 | 168 |
| state=3且blocked_from_state=2 | 168 |
| owner匹配已认证启动sessions的expected developer | 400 |
| owner不匹配 | 0 |
| state/version/blocked_from_state/owner_id缺字段 | 各0 |
| blocked_from_state显式null | 232 |
| state/version/owner_id显式null | 各0 |
| query与启动inventory任务state一致 | 400 |
| query与启动inventory任务version一致 | 400 |
| query与启动inventory任务身份一致 | 400 |

状态、版本均无不一致或缺字段。owner仅公布匹配计数，不公布用户身份。完整字段计数见同目录 `INITIAL_QUERY_AGGREGATE.PUBLIC.json`。这里描述实际初始条件，不推断其形成原因、产品缺陷或修复方案；这些query不是最终快照或后置验收。没有任务ID、凭据、私有响应正文或测试案例公开。未联网、未读取开发日志、未修改原始证据。
