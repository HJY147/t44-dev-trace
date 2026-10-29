# T15新F provider实际结果与迟到scope交接

后端AI，2026-10-28。设计96e67dbd；T15初源080ac190；正常启动审计修复d281c108；小段安装0a8aee3f；精确组装/一次发行cc4b579c。代码/账户发行/独立功能结论分开记录。本岗只本地开发与读取root逐文件授权的PUBLIC，唯一云操作者始终root，无独立private、用例、私钥、测试内部讨论读取，无新云账号/费用/自动重跑。

## 目标与本地证据

新F精确绑定be1975a7625eae32bf8aaae7e1f2de7d7aef8b20968aa5552320b22202258a9f，DBt44c_r28funcgen01_f/projectt44-cloud-r28funcgen01-f，sourcea12e9e70b963bacafda3242bb6d82e53ee912ff1，22443/CAde9b2e80...11243b，10:30Z。T15 PRIVATE schema SHAf8fe6a24...fd187b，T16真实收件key SHA cf8c47e7...ee3205/nonce d5385c...c366b；旧F包、旧接收key及原790七件/manifest均保持。输入T44FENV1 crypto与原c89d0300逐字同，K/口令/token只进程私有内存/stdin，不在argv/env/UI。未来证据cipher cap877539328B仅记录，不沿旧3GiB、不把输入AES key作为独立证据key。

初16本地目标全绿后，本岗从公开controller源码发现idle strictTLS无tokenGET会走原Runtime.rejection并正常写AUTH_REQUIRED audit；原provider全表=0假定会阻挡健康新F。先080ac190新增真实Runtime匿名getMe→401/audit→CLI五用户回归，实际1红/0error；d281c108修复为所有非audit业务/身份/服务表初始空，已有审计逐行保留且允许追加正常审计。没有删除审计、修改authstore时间、弱化业务或身份空表条件。原新回归test AST保持，最终17唯一目标全绿/零fail/error/skip（7协议/guard+10 CLI/Runtime，包括真实60秒等待）。红原XML无损gzip+双SHA/roundtrip保存，未strip失败内容，旧原件留本地；after-startup-fix.xml和verification-final.json为新证据。

两个完整PUBLIC安装命令12099/13562字节，均<18000；写新provider790-t15-window1030-01，O_EXCL且核全部6文件，manifest c222fff9fa2770eb779b685328f02b505a0324c3a6c188f6a5d79dc1eb247a71。初次git add提示全局*.pem忽略；只对已核625B、BEGIN PUBLIC KEY的精确PUBLIC公钥-f加入，不加入私钥。一次发行命令8628B SHA89c87b6c...a32817，Python3.10 AST核过；宿主源码/输入hash校验、data-only admin UID10001、180s且不超过stop、超时核owned label/image才停止自己的容器。root实际执行该命令成功，非本岗云运行。

## root实际发行（PUBLIC已逐SHA核实）

root安装invoke t-hz071e5agphcutc/t-hz071e5b9r3ut4w，实际all_six_verified；F真实neutral18字段3916B SHA9bda817d...c6dad2、runtime receipt2769B SHA91f46a88...4271b。源归档采用实际绑定f2a8ad128021760b01529855d6d92100c529a51d9a5087a77ee37f56fcd99822，未换内zip c4。API image完整sha256:475a1dd0240ad89519403e2c4ee4859fa68314e63879a8349e8ac4143926b39d；实际4worker依据Config.Cmd，不冒称枚举子PID。初实际6角色running/restart0，scheduler当时absent，不能写7角色已运行。

root发行invoke t-hz071e5xg8zcpa8：5不同身份、7不同会话、audit9、其余业务0、待撤销会话仍active。短会话原Runtime(Settings60)合法新INSERT/audit，同一F authstore；created10:08:19.891766Z→expires10:09:19.891766Z→observe10:09:20.002312Z，原getMe401 TOKEN_EXPIRED，原auth row不变。主TTL3600保持，未seed/预revoke。descriptor SHA43bd1c03...1c9c6c；仅密文4902B SHA0c141c220cda75aecd6b2e1c6b0c3150df34c170acc7996ed6d5cb25a373f199交root搬运。根PUBLIC发行receipt2725B SHAff15f265...f1a32。此为中性材料发行成功，不能替代独立功能/安全/审计/性能PASS。

## 实际scope时序：停止后不补封

| UTC时间 | 已发生事实 |
| --- | --- |
| 10:13:49.666953 | root单次functional launcher启动 |
| 10:13:51.208507 | 实际SERVICE_SCOPE_REQUEST，nonce393263e1...b833c，project_ids[1]，iteration_ids空；SHA1334c794...3facf1 |
| 10:15:50.382290 | root原GEN scheduler-token project1成功 |
| 10:15:51.441769259 | functional容器自然退出0；非OOM/非hard-stop，业务结论待私证据 |
| 10:15:57.400893 | root scheduler-start成功，已晚于容器退出约5.96秒 |

本岗只本地生成10420B scope密封命令草案，SHA534f3b7946431675871adcabbf7796fb7c4aed73c3bfff1e1e9b58ccda709daf；未发送root、未部署、未执行、没有生成或返回sealed回复。root核实会话结束后立即要求停止，本岗遵令不补封、不发callback、不自动重跑、不把尚在准备写成实际成功。原字节保存在provider-t15-actual-scope-seal-once.DRAFT_NOT_EXECUTED.txt，原可运行文件名改为STOPPED说明，防止误用。草案不作为已审可复用工具；它只检查10:26墙钟，不证明supervisor仍live，后续必须另新nonce/context/授权和进程存活准入，不能重用此会话。

root唯一授权T18 PUBLIC4b841bdd...31ce9确认PROCESS_FINISHED_AWAIT_PRIVATE_VERDICT与pending_request_count1，原supervisor nonce核同；公开终态NOT_PROVEN_PENDING_PRIVATE_EVIDENCE，退出0不等于PASS。约120秒时序不能独自证明失败根因，独立岗仍需解封私证据。本岗未读该私证据，不能将迟到scheduler启动记作会话内applied验证，也不能把缺少sealed回复伪写为业务API失败。

## 流程缺口与真实提示词记录

本岗先前仅准备了scope wire codec，没有在SUT准入前交付通用、参数化且已装好的完整callback桥；实际nonce出现后才编码并处于临界路径，这是准备不足。下一次应把实际request仅作为数据填入早已验证的provider桥，同时在执行前核真实supervisor/nonce/存活状态，而不是靠将来截止时间推定仍可回调。此为AI岗位工程记录，不是学生本人亲笔经历或其研究报告。

另有一次先前建议S1命令从本岗runbook猜fixture790-v3-01，root核实实际fixture790-01且未采用错误命令；本岗已明确承认并留痕。root自行实际新S1/producer02只改split/export两字串，无S2旧提醒，不把本岗错误命令当已执行。临时误建项目外空/tmp/unused已仅对本岗创建且确认空的文件删除，实际产物均留项目；不复现无关路径文件。

产品/原790冻结/旧F/旧云记录/独立原件均未修改。当前阶段只完成材料发行、如实中止迟到scope；未完成的通用callback桥、独立功能结论、正式性能及代码规模由root后续按实际证据处理，不宣称整体交付达标。
