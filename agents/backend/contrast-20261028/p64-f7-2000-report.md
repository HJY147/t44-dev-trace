# f7 P64 20:00新窗口派生记录

这是后端AI的新工具版本；root称14:21Z尚无F/P prepare、arm、infra、DML、API或pressure，本岗未执行云或SUT。产品仍f7，旧16:00包/20eb4ae3及原3红失败完整保留，不追认任何已消费case延期。root报告的镜像/CI成功不等于本工具正式性能通过。

新13运行文件位于`tmp/790_backend_contrast_20261028/p64-f7-window2000`，9文件逐字相同；另4文件仅3个datetime截止16→20、authority STOP字符串及EXACT窗口错误标签变化。manifest允许变化仅files/window_utc/supersedes_manifest_sha256/phase_GEN_sha256。源、权限、SQL、幂等/事务/审计、预算、原业务阈值均未改；seed44、04:00anchor、600TTL、330/90秒、80/800/8000和400active/no-think不变。旧两目录全部tracked字节通过Git20eb4ae3核同，包括原46用例及全部失败原件，没有为新窗口改写旧例。

新runtime manifest为`2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de`；新delivery为`305c5a722ee94d1339b2400a292bbc83416e6c40ba3c0a4b7fc49efdcfd41352`。安装目的`/root/t44-r9/p790-f7-2000-ui03`。root两阶段授权时序保持：真实infra/预算和prep→所有业务表空bootstrap→GEN idle及六角色/TLS/source→另新pressure grant/nonce→S1/S2。模板actual字段仍null/admitted=false，缺准入即拒绝，没有本次actual phase/grant/session。

部署公共commit c1303016a053d5b718d3df30ce5911d2e002c18c提供新GEN，30497B/SHA`9edafbbff0586b5f77a701bd37f715685fba4169abaae510474343af75a8b427`，目的`/root/t44-r9/v4-code-20261028-03/profile`。本地核原GEN只有一个STOP字符串变化；helper305f9eae…25dd82d及只读scope依赖e551…d5f7不变，后者budget复用路径没有16Z常量，实际deadline来自本次control/binding，不执行scope callback。

|片|raw字节|base64(raw)+300|完整UI+300|
|---|---:|---:|---:|
|1|9393|12824|12946|
|2|11750|15968|16090|
|3|11418|15524|15646|
|4|6194|8560|8682|
|5|10966|14924|15046|
|6|8354|11440|11562|
|7|9505|12976|13098|

`ui-partNN.PUBLIC.txt`已经完整包装，直接投递；`raw-partNN.PUBLIC.sh`只供root现有helper包装一次，不可双重base64。新7项限定检查首轮7通过，含13文件差分/Python3.10 AST、模板最小差分、真实部署GEN单常量差分、旧包/原例/失败字节、完整编码长度、实际outer→bash安装回放/拒覆盖，以及20Z有效/到期拒绝/旧16Z拒绝/阶段错误拒绝。未重复整套68或真实产品实验。首次Ruff发现两个自测subprocess.run缺显式check参数；补check=False，不改断言和运行工具；最终限定Ruff通过。两次本地JUnit分开保存，不合算14例。

本机Mac/Python3.12实际回放，host3.10只静态AST；没有Linux/MySQL/真实HTTP/独立验收/云账单或正式性能新结论。六角色短诊断不能冒正式七角色600秒。部署/实际环境/根grant仍待唯一root执行；完整命令和错误边界见p64-f7-2000-runbook.md。
