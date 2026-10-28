# v3-window1030：固定窗口副本与证据

后端AI，2026-10-28。root07:51指令，设计db9f1135、工具/差分验证源5a88d11a、完整小段安装源a8c1f7a2。旧v1/v2七件、manifest、33proof、旧云记录、F provider及产品均不改。上一轮模型容量中断不是代码失败；本轮实核工作树及继续既有本地会话，未重造旧证据。

新工具仅用于root全新r28p16gen02、source a12e9e70b963bacafda3242bb6d82e53ee912ff1、seed44/anchor04:00、新截止2026-10-28T10:30Z。root唯一云操作者；本岗未读取真实私包/env/runtime/独立未公开材料，未开云/收费/新CI。旧P16-01无cohort、旧P16gen02 init未UI提交来自root实际状态回传，不伪写为本岗云核实。

## 精确差分

七脚本只有790_bootstrap.py与edge/790_http.py各一处HARDSTOP datetime小时7→10（各增1字节）；其他五件逐字同。独立transport也只STOP小时7→10，其余逐字同。wire kind不改，manifest version3+新window及前链，原v2 SHA640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84仍精确。新manifest SHA `0ef08aab3e14887b703c9a2fa5e5265d60fbbcb4172d1d6deb20b5f746df048a`。

| 文件 | 字节 | SHA256 |
| --- | ---: | --- |
| 790_bootstrap.py | 13627 | `ad97e05519ae35c3457232f4b3cc0311342946b3eca88b61af9a37064c23d236` |
| 790_host.py | 13483 | `410d412d1bfa937932ba404cd11defd84cb82667531da8d1199c7651949cbcc6` |
| 790_load.py | 10279 | `a7a2cc62b9771fec669be39cdcef76a961b7b66e7acf518b017b6d3ad132bb63` |
| data/790_select.py | 5668 | `52739bea73c9a0cbb80b128706ae137be770c0a2cce267cce245e22a890df8bb` |
| data/790_stage1.py | 9342 | `e626b49194c5575e9983992d2028a27a23a1b05a381006d94b6fc912f29a63cd` |
| edge/790_http.py | 23918 | `c7ea44210a610d77559a8de54a2424d03c276e5c7e9c9e9746c0ab754cb6b415` |
| edge/790_stage2.py | 10719 | `bcd04539eef589b64ad2df2ef7c1da189a14630cbfe4747d65d1d730986fa57a` |

独立新版transport 12575B，SHA7e2dfb5b4c4fd3766769d4c5f15ac65fa8b61e7286e09ee402ff10fa650816f3；不覆盖旧4508b92 helper。协议里的600秒私包、15分钟S1、真实会话TTL、330秒LOAD准入、1×20/40×5/400×5、80/800/8000请求、逐请求截止/连接后重核/剩余socket预算、共享abort、prefix/失败停臂/不重试、鉴权/事务/业务/审计均字节保持。

## 实际检查

原33诊断目标在新10:30窗口/临界前后假钟与r28p16gen02/16worker数据下全绿，原49个assert AST在仅获准字面数据替换后等价，零删断言/函数；另13 transport目标（17断言）全绿。合46唯一目标，零fail/error/skip，保留原Starlette/httpx警告。完整真实a12 CLI/V2(40/6000/9000/15000)与原handler SQLite兼容仍运行，不把测试占位计时当性能。

790_window_proof.py先5a88提交再实际执行：raw exact allowlist、全AST、assert AST、v2保留、host3.10 AST均通过；verification.json SHA90bb7e480ac3f9607df8a75444d10b9a7d7a900c11ae8f77626d34f0d399582b。没有本岗云/MySQL/真正TLS负载/正式独立性能。首次lint/format误用根80列对旧100列代码报告格式与宿主Z解析提示，未自动修改任何副本；按原backend100列与原transport80列分别检查通过，Ruff backend配置及根严规则（仅bootstrap FURB162明确3.10兼容豁免）均过，未以改格式破坏最小差分。

安装命令本地另做6个子进程检查：3分片正向/同目录覆盖拒绝/旧bundle marker拒绝/独立transport正向，均符合预期，逐文件匹配新manifest；不是6个新业务测试。三个**完整可投递命令**含encoded+desc/包装分别13933、13792、16057 UTF8字节，transport完整6374，全部<18000；原记录JSON分别12046/11905/14170和5668。安装只新目录/O_EXCL，不混旧包，part3再次核完整7文件；实际云执行仍待root。

延长窗口会参与S1提醒稳定性筛选，不能仅靠同种子假定夹具相同。本岗在自己的开发SQLite（兼容链运行后、只读，不读任何云/独立私包）做窗口对照：候选提醒1680→1440，441个实际所选任务对位置变化0，pair-ID SHA两窗同31e40229c512c8722bae30d5a74e570ca67c3ad1c994ab153e9f06f62dd6c98a。此非新云S1 receipt；root仍须核实际新S1 selection_sha256与原P7公开4bf3514bf8feba68ca81b8e0baa7a13de85fcef095510f9d2f7c8d7e66ee5706一致，才称只worker差异。

## 交接

只先装全部/核版本与SHA并预建LOAD key，之后新phase原bootstrap/S1，再S2→新transport→LOAD即时连贯跑；不再把600秒耗在工具安装。runbook window1030-runbook.md。两臂仍开发6-role范围，正式7-role/独立600秒门禁不由本包替代。未来F另等真实新binding/schema/key后另版，不混旧F或自动改旧截止。以上为AI操作和实际记录，不写学生本人过程经历。
