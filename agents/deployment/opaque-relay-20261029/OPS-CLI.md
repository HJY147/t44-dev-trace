# 29日后半程最短操作

部署AI只准备工具，尚未云上执行。源码固定，原13件工具不变。新的目录和授权单次、失败保留前缀，不能重跑或新造S2。操作者逐步保存原stdout及exit，再提取完整PUBLIC对象，不可把多条JSONL交给一次json.loads。

两台执行 `install-ops.PUBLIC.sh`，落 `/root/t44-r9/ops-r29-01.py`。原20文件及relay须已安装；APP worker须真正产出 `/root/t44-r9/r29-app-prep-01/complete.PUBLIC.json`。已有LOAD keygen则不再运行。新脚本编排一小时成本窗；当前总协调实际给定 `cost_stop_utc=2026-10-29T04:56:19.801Z`，它不是原GEN12Z截止，也不是session TTL。脚本不会替总协调进行云端保盘停机。

本地运行 `python3 build-ui-command.py OPERATION --public-input 实际PUBLIC输入.json --output 全新脚本.sh`，输出完整UI命令长度含300说明必须≤16000。它只读取根提供的公开对象、压缩编码，绝不操作云。省略 `--public-input` 仅适用于尚未做过的load-key。

1. LOAD已完成原keygen时，保留 `PUBLIC-790-KEY` 原stdout。否则仅一次 `python3 -I -B /root/t44-r9/ops-r29-01.py load-key`。私钥留LOAD，禁止复制。
2. APP执行 `app-resource`。输入 `{app_ip:实际私网IP,load_ip:实际私网IP,cost_stop_utc:实际根预算截止,load_key:完整PUBLIC-790-KEY}`。自动安装APP公钥到 `/root/t44-r9/r29-ops-app-01/public.pem`，启动原resource18449，原seal封装非凭据marker。输出完整 `R29_RESOURCE_ONLY_OPAQUE_HANDOFF` 密文公开对象。
3. LOAD执行 `load-resource`，输入上步整个公开对象。原open的handoff位于 `opened-resource-only/mirror/private-mirror-handoff.json`，核原marker后才启动原资源镜像。输出 `R29_RESOURCE_MIRROR_PRESTARTED`。此时没有S1/S2/session/matrix。
4. 总协调明确批准这一轮短诊断后，APP执行 `app-stage1`。输入 `{root_admit_pressure:true,load_resource:完整R29_RESOURCE_MIRROR_PRESTARTED}`。重新核实际状态、roles、CA和镜像，签一次原pressure grant、只运行原S1，生成APP配置并先启动APP relay18447。输出 `R29_S1_AND_APP_RELAY_READY_NO_S2`。默认无该true值就拒绝；没有正式性能授权。
5. LOAD执行 `load-start`，输入上步整个公开对象。核原工具、当前Python镜像和已有资源字节，生成原LOAD配置，先启动原relay LOAD worker。该worker以原CA及APP IP收到HTTP425（原producer未ready）才保存 `LOAD-ready.PUBLIC.json`，外层核其PID等于实际systemd MainPID后输出 `R29_LOAD_TLS425_POLL_READY`。不能用单纯dispatch成功代替此ready。
6. APP执行 `app-producer`，输入 `{root_start_producer:true,load_ready:完整R29_LOAD_TLS425_POLL_READY}`。核nonce/source/binding/grant/成本截止，原APP配置不变，异步仅启动一次原producer（RemainAfterExit=yes保留终态）。LOAD已等候；原S2完成且全部片/SHA通过后，密文自动传输→原receiver→原consumer一次，无GUI搬运。此步是执行，不是压测成功。

读结果只看原文件，不重跑命令：APP `/root/t44-r9/r29-ops-app-01/08-producer.unit.stdout.private`、相邻stderr、原export；LOAD `/root/t44-r9/r29-ops-load-01/relay-load-state/consumer-once.stdout.PUBLIC`、相邻private stderr、`result.PUBLIC.json` 或原始失败prefix。外层unit `t44-r29-relay-load-01` / `t44-r29-producer-01`。成功receipt也仅表示consumer完成，性能阈值须从原8000请求证据审核。

原consumer有open60s+mirror15s+load300s；relay父级420s、异常精确owned清理最多90s、落盘30s，消费前独立成本余量≥540s。producer派发前仍需>960s；传输按原600包年龄/会话实际expires检查，原330秒control总余量不改。任何超时/非425失败保前缀停止，必须回收证据并由root停止原两台保留盘，核自动释放为“-”，不删卷、不再开新迭代。

本地验证仅Python3.10语法（在3.12解析）、shell语法、6个helper/source小检查；没有整链Linux/systemd/资源/原consumer测试。初次fixture /var软链接被canonical guard拒绝，改为resolve fixture；guard没放宽。一条本地封装命令的heredoc终止符误写，Python解析失败且未改文件，随后正确重跑。这些不是产品缺陷或云压测结果。
