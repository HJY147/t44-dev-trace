Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-USAGE-v1

补充runtime-usage准确超时边界：实现仍8983e4c098849c7e9be8869c3bb42bc2697ccadd，逻辑/JSON合同未变。stats本身有15秒预算；前面固定六项验证，每项Compose ps-q有10秒、inspect有15秒各自预算。整个命令没有统一15秒总deadline，不能宣称总耗时≤15秒；子进程启动/解析也有实际开销。调用方须自行给足覆盖多步验证与采样的超时，以返回的started_at_utc/finished_at_utc观察实际总墙钟；不称采集零开销或零负载影响。

README“有界runtime-usage”已明确这一多调用预算边界。本轮仅文档/封档，无运行逻辑、合同、资源、旧metadata或控制变更；不新增或重跑已通过15项，不跑Docker/HTTP/SQL/信号/真实采样/压力，不读取独立资料。原CLI红、Ruff初败及最终合成通过原件均保留，真实环境采集仍待准确绑定后的调用方执行。
