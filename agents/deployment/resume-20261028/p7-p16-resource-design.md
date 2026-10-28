# P7/P16资源与新P16准备的本地命令设计

只整理总协调下一步可用命令，不操作云UI/服务，不读取792或独立私有资料，不修改产品。来源为总协调回传真实APP/LOAD Running及P7 idle，以及总协调工作树中已公开generation/image/infra/bootstrap JSON；运行事实属于该执行者，命令计划不是新执行回执。

精确源a12e9e70b963bacafda3242bb6d82e53ee912ff1，目标actual镜像475a1dd0…；已核P7 binding eac4f526…、40/6000/9000/15000种子和最晚2026-10-28T07:30Z。派生generation SHA fd7d8cce…、resource SHA3d9f096f…、profile SHA f4842f54…由root提供完整值。将由原四模板纯派生重建同字节工具，作为CLI选项/时间/参数的本地校验，不读root私有profile。

P7当前6-role，无scheduler：collector仍逐轮记录七角色，scheduler必须真实missing/null，不能写0或正式7-role已齐。采样首CPU delta为null，后续缺值/重启/间隙如实保留。先APP采集＋LOAD镜像，完成warmup前确认真数值与从offset0连续镜像，封尾并收全wholeSHA后再停observer及owned SUT。

P7/P16不得并发运行：每代配置limits不是内存预留，合计可能超过32GiB。P7短窗结果封存/保卷owned stop后才开新P16的infra。P16用新namespace/DB/CA/4端口与相同源、seed44/anchor04Z、相同客户端矩阵，不能只把P7 worker数字改成16并覆写旧绑定。

各动作列出相对07:30Z余窗：新generation prepare及非stop/status的SUT动作本身要求≥600秒；建议新P16准备前≥1200秒，bootstrap/完整对照要另留实际预算。collector prepare需sampleUntil未来≥120秒、serveUntil≥sample+30秒且≤07:30；start需serve未来>30秒；cleanup stop/status必须允许过期后运行。计划固定sampleUntil07:28:30/serveUntil07:29:30，最晚07:20后不再启动/迁移/轮换新SUT，不延长旧窗口。

正式7-role/600秒另列未执行方案：独立中性准入、自然有效/过期/可撤销会话、真实scope及scheduler首scan、完整数值资源流覆盖warmup/steady/后置条件。790 fresh-create前提与scanner初始事件冲突，不能把本轮6-role工具直接挪过去或删断言。等待root实际7vs16结果再决定是否有充足同窗口或新许可，不能预填通过。
