# 实际派工提示词

ROLE-database-PERFORMANCE-20261025-v1，数据库AI。

总协调实际要求：在ade5e4c独立worktree继续未达标工作；仅公开839联合报告和本岗公件；与后端同次请求关联execute/fetch/codec、UoW持锁/commit/reset、物理connect/preping/pool的可区分计时；不得记录自由正文/DSN/token/绑定值，不把inclusive叫纯等待。先设计再工具，只在freshCI明确专用schema窗口执行真实MySQL，不连旧云env/未知库，不凭相关性调池/锁或删鉴权审计。新脚本tmp/833_database_performance，阶段日志/报告/handoff/commit/Issue4留痕。

后端实际确认：在APIRoute真实同步handle(worker thread)内部传operationId及request.state.request_id，trace.install(engine)在fixture前装入，fixture/setup不计为请求；后端提供有限顺序HTTP/SQLite初测和全endpoint线程CPU profile。本岗不改api/services。

root随后实际限定：本机docker不存在，不连接现存MySQL；准入免费GitHubActions独立fresh MySQL service，schema固定t44_diagnostics；root负责workflow和编排，不改生产settings；诊断≤10min，非正式400×600。本岗先提供observer模块及精确source checkpoint。
