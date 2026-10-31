# 可选双代理分层日志

默认部署文件完全不改。生成器不运行Docker/Nginx，不reload，不改worker/pool/CPU。只显式`--enable`接受原配置SHA与hop，生成全新文件；重复注入、错误hash/hop、缺原minimal日志或access_log off均拒绝。

```sh
python3 deployment/diagnostics/proxy_timing.py --enable --source CURRENT_NGINX_CONF --source-sha256 ROOT_VERIFIED_CONFIG_SHA --hop web --output NEW_WEB_CONF
```

TLS用相同入口`--hop tls`和其实际原配置hash。输出回执给source/output SHA，部署源Git SHA另记录；应用前先检查原配置仍同SHA，执行官方pinnednginx -t。开启需root选择独立只读mount overlay，保留其它挂载/资源/原配置回滚。此目录不生成现有Compose路径猜测，不自动装载输出。关闭时恢复原config挂载并正常校验reload。p12主要尾已在handler内，proxy观测用于界定剩余时段，不作为主要根因预设。

原`minimal`格式、四列request_id/status/request_time/upstream_time及所有原access_log保留。新增日志在每hop容器`/tmp/t44-proxy-{hop}.diag.jsonl`（先确认tmpfs），16k buffer/flush1s；按白名单response UUID尾00取1/256，双hop同response UUID可配对；缺UUID回退各hop自己的proxy ID采样，此时不能可靠跨hop配对。不得以全部流量写入诊断文件。约1000RPS/600s时每hop期望约2344条，实际条数随机且非硬上限。仅有限观察窗使用、观察退出后立即关闭并回收；无自动VMstop。若总量异常、tmpfs余量不足或日志开销明显应停止诊断而非改业务验收阈值。缓冲最后尾行可能未flush，采集应正常flush后记录完整性，不能说日志行数等于请求数。

| 新增列 | 含义/单位 |
|---|---|
| hop | web或tls独立代理层 |
| response_request_id | upstream X-Request-ID严格小写UUIDv4白名单；否则“-”，JSON escape |
| upstream_connect_time | 上游连接（TLS上游时含握手）秒；不是worker队列CPU |
| upstream_header_time | 上游响应头时间，秒 |
| upstream_time | 原upstream_response_time，收到上游响应的秒数 |
| request_time | 该hop读请求至完成发送/日志阶段秒数；含下游慢读取可能 |
| upstream_status | 上游状态序列 |
| connection_requests | 该下游连接累计请求数，可辅助保活解释 |
| handler_ms | 只接受app;dur起始数字格式，毫秒；整Server-Timing不写日志，格式不符“-” |

上游重试可产生逗号/冒号分组、多值和“-”；以上时间均作为字符串保存，**不可直接float整列或简单相减归因**。只有同一request/明确单attempt可算分层边界。两个hop request_time互相包含，不相加当总耗时。app dur使用本机monotonic，跨机耗时不依赖Date墙钟同步。没有body/URI/query/Authorization/cookie/SQL/payload或完整Server-Timing。

专用free CI `.github/workflows/proxy-timing-syntax.yml`仅对原web配置和app-campaign.nginx()生成的TLS配置派生、官方固定Nginx镜像执行nginx -t；用临时自签证书不监听，不起SUT，不build镜像。通过也不证明原p13现场nginx -T一致或诊断性能开销通过。官方语义参考：https://nginx.org/en/docs/http/ngx_http_upstream_module.html 、https://nginx.org/en/docs/http/ngx_http_log_module.html 。
