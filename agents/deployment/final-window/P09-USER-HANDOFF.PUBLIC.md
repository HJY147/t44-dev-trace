P09 用户亲自执行交付（本地准备，未远程运行）

P08 原失败 `PREPARATION_LATE_NO_OVERRIDE` 保留；P08 没有 INSTALL/790/独立 QA 正式测量。当前没有 P09 远程结果。保持两台节省停机，待用户决定开机。不能使用 `55a4c081` 的 `P09-USER-APP-CLONE-FREEZE.PUBLIC.py` 或 `P09-current-resume-cost.PUBLIC.json`：它们是旧账期草稿，包含已过期 boot/03:00，均不在本次有效 manifest 内。

本次只测 source90b 一轮 P，不做 F/Word/重构。S=T0+10、E+23、G+25、C+30，400 clients、60 warmup、600 steady、13分钟测量窗及原所有门禁保持不变。两台原 VM、磁盘、P08原件保留，不购买资源。全部云命令由用户执行，本文的 Python 生成命令在本地执行。

1. 用户开机前，总协调先重新核平台保盘定时 StopCharging 配置（原两实例/不强制/保盘），安排新的实际 cutoff。只能记录真实创建/生效配置；不得写已实际触发或权限完全验证。旧 OOS 03:00 不能当未来保护。随后由用户开机。
2. 用户分别在 APP/LOAD 粘贴 `P09-USER-APP_FACTS.INLINE.PUBLIC.sh` / `P09-USER-LOAD_FACTS.INLINE.PUBLIC.sh`。APP 从盘上实际 P08 四工具逐原 SHA 派生新副本，无 freeze/QA/服务生命周期动作；LOAD 只采真实 boot/NTP、原 image/resources、PUBLIC9件 SHA。LOAD resource probe 是 network-none 短暂容器，不向 SUT 请求。两条事实脚本均小于16KiB。APP facts 校验 `P09-FACTS-CHECK.PUBLIC.py --app ACTUAL_APP.json --load ACTUAL_LOAD.json`。
3. 总协调根据本次真实 boots/facts SHA 填 `P09-FEE-TEMPLATE.PUBLIC.json`，独立新 fee 的内部 cap50，3元余量；不沿用旧 origin。平台 proof 绑定相同实际 cutoff。LOAD事实超过120秒应在尚未 freeze 时重采，不改任何已冻结时钟。命令：

```sh
python3 P09-USER-COMMANDS.PUBLIC.py freeze --root-reviewed-facts --app-facts ACTUAL_APP.json --load-facts ACTUAL_LOAD.json --fee NEW_ROOT_APPROVED_FEE.json --platform-proof NEW_PLATFORM_PROOF.json --output USER_APP_FREEZE.sh
```

用户执行生成的 APP 命令前，**云助手执行超时设900秒（原180秒不可用）**。输出也会报告 `required_cloud_assistant_timeout_seconds:900`。脚本只停精确 P08 launcher（不存在则如实接受 not-found），再启动新 P09；连续前台运行只读 collector，最多600秒。开始立即 flush 一行完整 early JSONL；若初始文件尚无，会在三件 PUBLIC齐备时再发 early；bootstrap新件齐备立即发 ready 并退出。运行中即可复制完整 early 行给总协调提前核7roles/resources/import/source并准备独立 target 审批，无需等结束再点击第二次观察。CloudAssistant需要支持读取运行中完整 stdout 行；本地 mock 未证明远端UI流式展示能力。若只能任务结束后取stdout，最多等新bootstrap出现即结束，仍不需第二次collector。

4. 将两行完整 JSON 保存为 `COLLECTOR.jsonl`，立即本地解包：

准备状态可能由进行中变为就绪。解包器将每次 `preparation.PUBLIC.json` 原字节按 SHA 保存在 `preparation-observations/<SHA>.json`，输出的 `preparation_observation` 指向当前行原件；顶层同名文件保留首次观察，不能当成最新状态。时间窗口、导入回执、bootstrap 仍不允许变化或覆盖。重复处理相同原件不产生新版本。

```sh
python3 P09-COLLECT-UNPACK.PUBLIC.py --jsonl COLLECTOR.jsonl --output-dir NEW_P09_PUBLIC
python3 P09-USER-COMMANDS.PUBLIC.py load-prepare --root-reviewed-facts --load-facts ACTUAL_LOAD.json --bootstrap NEW_P09_PUBLIC/LOAD-bootstrap.original.PUBLIC.json --qa-target NEW_QA_TARGET.json --qa-approval NEW_INDEPENDENT_QA_APPROVAL.json --backend-import-receipt NEW_P09_PUBLIC/backend-import-receipt.PUBLIC.json --qa-public-pins REVIEWED_NINE_PUBLIC_PINS.json --output USER_LOAD_PREPARE.sh
```

收到 ready 后立即给用户执行 LOAD prepare（超时300秒）。early时先完成能做的 source/import/target审查；ready 时仅补本轮真实 packet/env/identity。prepare仍检查 S−30；原 transport/adapter 仍检查 packet≤300等门禁。若迟到，失败原件保留，绝不改钟/覆盖/自动继任。prepare复制原9件PUBLIC（含不运行的F入口），原INSTALL/790/独立ENTRY prepare，嵌入并回报P09 helper原SHA；工具不读取QA PRIVATE。prepare输出包括原 defaultfalse grant 原字节+SHA（无令牌），不要手抄21字段。

5. 仅独立 QA 对完整原默认 grant 批准 `allow:false→true` 后：

```sh
python3 P09-USER-COMMANDS.PUBLIC.py load-arm --root-reviewed-facts --load-facts ACTUAL_LOAD.json --prepare-receipt ACTUAL_PREPARE_RECEIPT.json --grant INDEPENDENT_APPROVED_GRANT.json --output USER_LOAD_ARM.sh
```

用户必须在 S−30之前执行 arm；新 helper SHA 绑定 prepare回执及LOAD实际文件，无第三次facts刷新。定时 S+1 执行原ENTRY；仅 S+1≤实际now<S+20接受，不能晚启动。原21字段默认值仅allow一项可变；原adapter/ENTRY/core未改。timer已arm不等于已经发压，通过必须以原独立报告为准。任何失败真实输出，不自动追加一轮。

本地检查：`python3 -B tmp/753_deployment_final_window/test_p09_user_handoff_local.py`。测试包括真实collector主循环的虚拟366秒延迟、365秒截断JSON、永不出现/截止/超时、两行原字节解包；完整grant差分、S+1边界spy、四工具派生函数fixture及生成器链。它们不是远程演练，不证明镜像、盘上工件、云助手输出流式展示或正式压测成功。实际4件预镜像 SHA 在用户 APP执行时校验，未本地伪造为已读取云盘。

审核窄修：freeze 在任何 put/stop/systemd-run 前实读 `/proc/stat` btime，与 fee 中 APP 当前 boot 精确比较；LOAD prepare 同样比较已审核 LOAD facts boot，重启后旧 facts 不可用。collector 首行仅 PUBLIC 文件立即 flush（元数据标记 pending），随后补完整 early 元数据；子命令共用 `min(总600秒,S−30)` 截止，每条最多5秒，Docker selected-format一次批量 inspect，命令超时明确 UNKNOWN，不作为无其他 writer 证明。DB counts/scope 尚在写入则 pending；总协调应使用 metadata齐备且对应本轮的 early/ready 行审核，UNKNOWN不可冒充完成。
