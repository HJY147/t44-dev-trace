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

## 已启动但原start观察失败的单次续封包

根实际云证据：02-resource-start返回RESOURCE_STREAM_REFUSED，原因EXACT_OWNED_SYSTEMD_PROCESS_REQUIRED；不是daemon启动成功的receipt。随后根观测同一原unit active/running、MainPID49694/root UID0、当前argv逐字等于原start-plan，cmdlineSHA 29d073ef686a10b4956f3eeeaf775cede1f324972de5f4f57f1c9414a9939c98，raw已1,365,789字节；原start-result缺失。原因为何在初次观察时不匹配尚未证实，不能直接写成已证明竞态。

安装 `install-resource-continuation.PUBLIC.sh`（仅装新文件不执行），再运行 `python3 -I -B /root/t44-r9/continue-resource-r29-01.py --public-input-zlib-b64 '原app-resource同一个PUBLIC_INPUT_BLOB'`。它不重start、不重prepare、不重建namespace、不覆盖02，只验证原文件hash、unit plan和现时实际PID/root/完整argv/start_ticks/raw首记录。若这些仍成立且start-result缺失，排他记录有明确fresh-observation-recovered标记的真实当前receipt；已有则核对拒覆盖。不是伪称旧start返回success。然后只续尚未执行的03原seal与bridge/state输出，仍以marker密文接原load-resource。若argv有-I/-B等差异则拒绝；原代码没有argv重写，不能放宽原guard。

部署AI只做Python3.10语法及shell语法解析，未执行云恢复。以上云事实来自根转交原件及其实际观测；根仍须保存恢复步骤原stdout/exit并核验完成。

## 原status输出形状修复（必须换两个入口）

根实际APP原app-stage1在04成功读取GEN status后因不存在host_https而失败，尚未grant/05/06/S1。部署AI复核原GEN源码，status早返回仅success/resources；原resource control status则含action/unit/PID/progress，不含success。旧ops两个通用字段假设是部署编排缺陷，原失败/日志保持。没有改原13件。

APP先安装 `install-app-stage1-wrapper.PUBLIC.sh`，以同一个原PUBLIC blob运行 `python3 -I -B /root/t44-r9/app-stage1-r29-01.py --public-input-zlib-b64 'BLOB'`。新04b独立实际roles状态、新04c严格原CA/IP/端口访问原无凭据projects路由，实际401才继续原05/06。不会重idle或重原04；若05/06已存在就排他失败，不启动第二次S1。输出仍原公开bridge。

LOAD先安装 `install-load-start-wrapper.PUBLIC.sh`，以APP新bridge整个公开对象压缩blob运行 `python3 -I -B /root/t44-r9/load-start-r29-01.py --public-input-zlib-b64 'BLOB'`。04b按原resource status的action和unit取真实记录，核PID不变和raw字节，不伪造success字段，worker仍调用固定旧ops的load-wait。APP producer入口不变。

新增小检查直接解析原GEN/resource AST确认实际输出字段，并用相应形状代表性fixture检查新选择规则；没有用额外云尝试猜字段，也没有声称是Linux整链实测。工具仍须由根保存实际运行证据。
