# 未来新窗口的中性准备 CAS 修复

**本目录不是 r30window01 续跑授权。** 原窗口未发grant、guest已stop，root报告两VM已节省停机。旧四会话、失败prefix及原producer17/66ab、运输686保持原字节；不得复用或改钟。本次只在本机用合成数据验证。

本目录是原17 runtime文件的future副本，新增`escalation_readback.py`，新manifest仍为name→SHA和file_sizes形状，共18件。产品source仍0b；不改API、规则、CAS、DDL、计数、预算wrapper、角色或调度顺序。未来部署owner须审新manifest并将新增helper同字节放入同一代码目录；原producer17安装清单不能直接宣称支持18件。实际云/免费CI均未额外执行。

未来仅在root另外给出新run/原GEN binding/源及实际import证明、新窗口和真实scope/四session授权后，使用与原RUNBOOK相同的admin→HTTP→counts→assemble协议；所有输入默认false/null。HTTP入口只替换代码位置，原flags及输出新目录约定保持：

```sh
python -B /neutral-code/prepare_http.py --plan /neutral-input/plan.json --accounts /neutral-input/accounts.private.json --service /neutral-input/service.private.json --ca /neutral-input/ca.pem --output /neutral-output/NEW-http-result --import-receipt /neutral-input/import-receipt.json --binding /neutral-input/binding.json --root-admit-http-preparation
```

此处`/neutral-code`必须由owner安装**本目录新18件manifest**，所有/neutral-input路径必须是新实际挂载值，不从旧包回填；plan.gen_binding.path必须与实际binding参数相同。admin正式入口仍是root已审、真实9e预算锁覆盖整个固定子进程的wrapper，直接运行admin不授权。首次准备完成时间和expires仍按真实原值保留，不retime/重登/延token。

正常scheduler/consumer继续运行。每个内部升级POST保留原expected_version和唯一scan_run_id，只发一次。只有HTTP409且顶层code=VERSION_CONFLICT、完整冻结Error schema时，才追加正常GET规则、task、分页events、task。官方load_rules/select_window验证当前及整个窗口同级别；事件必须完整schema、同项目/任务/原排期、当前规则、唯一业务键。两次task间排期/plan/身份/状态必须稳定，version可真实递增；原409的current_version不参与构造Task。缺少或不一致就失败，不补写事件、不换任务、不把409计为2xx。

`requests/*.private.json`保留原HTTP409与完整错误envelope；`event-readbacks/<project>-<task>.json`为0600排他只读核对prefix，记录post_outcome、原冲突请求ID、真实task/event。consumer合法改变disposition/handled_count时采用实际GET原件，不回写POST旧值。外层失败保留已签会话与所有prefix，不覆盖/自动重试。最终完整400库存/6400实际任务口径、counts/权限/TTL/assemble严格门禁保持原样。

本地复核（不连接服务、不签发真实session）：

```sh
PYTHONPATH=backend /path/to/project-venv/bin/python -B agents/backend/neutral-r30-cas/verify-local.py
```

78项本地检查不证明原六个实际失败对象已有可采用事件，也不构成SUT/QA/正式性能通过。若未来希望等待正常scheduler首扫完成后再准备，可先只读观察；不能停测量期scheduler或假设它静默。本修复保持现有启动顺序，处理的是已发生且可由原GET原件验证的竞争结果。
