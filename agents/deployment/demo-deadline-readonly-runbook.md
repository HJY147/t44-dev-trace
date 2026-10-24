# app_20261023_234943_3f9bad 到期只读交接

原截止固定为2026-10-24 03:49:43.904838UTC（北京时间11:49:43.904838），不延长、不重启。03:17:43.706369UTC快照仍serving/ready；这不是4h结束或cleanup成功证明。T44已PAUSED，不建新automation或续跑。

自有run目录：`.agent-worktrees/.runtime/native-demo-20261023/runs/app_20261023_234943_3f9bad`。自有操作目录：`.agent-worktrees/.runtime/native-demo-20261023/user-demo-20261023`。以下均由总协调到期后按需人工只读，不建立新轮询/执行流程。

1. 先读已有`run/state/serve-status.json`，只投影phase/at_utc/started_at_utc/deadline_at_utc/duration_seconds/source_commit/capability_ready/stop_reason/additional_rotations/最终success/cleanup_success。serving或cleaning不能代写finished，也不能以截止已到推定成功。
2. 看操作目录已登记的`serve-driver-receipt.json`是否实际生成（本快照尚未生成）。只取actual_exit_code、结束时间、external_driver_wait_confirmed_runner_exit及实际unconfirmed字段；null/缺失保持未确认。不要执行driver、862、863或post脚本补造。
3. 仅在自然退出/末次receipt后，按既有流程生成结果的实际存在情况读取`serve.stdout`末次summary及`post-receipt.json`、`post-run-proof.json`。这三项到期前不能假称已存在；当前后两项尚未生成。只投影run/source/controller/duration/start/deadline/finish/stop_reason/success/cleanup_success及后置身份/端口布尔，不公开完整argv、凭据、SQL行、通知内容或嵌套原文。
4. 区分controller末次summary、外部driver确认实际退出、post提取结果三种事实：提取失败不自动等于serve失败；summary cleanup布尔也不能冒充外部runner已退出。任何缺失/矛盾/异常报告root，原失败保留，不代写success。
5. 后置九protected对照仅当原有`protected-after-finish.json`/`protected-comparison.json`实际存在时读，与原`protected-before-serve.json`比较PID/UID/start/pgid/commandSHA/监听地址。这只是离散时点，不证明期间连续无变化。缺失时报告待观察，不能运行全局脚本填补。

本阶段不连接浏览器/HTTP/SQL，不访问独立应用数据/private，不发信号、stop、kill，不更改livecopy/凭据/无关服务。若结束后需要进一步动作，交root按实际状态决定；本runbook不授权续期或新运行。
