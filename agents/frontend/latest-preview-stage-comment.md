本机用户演示预览已更新到固定应用 `bc5aef9c62393134582affb7a690acb33ac2b833`：http://127.0.0.1:5173 → API http://127.0.0.1:18080 。这是 API+Web 开发预览更新，不是完整持续部署；消息 worker/定时扫描器未启动，未做 DDL/migrate/seed/reset 或业务写入，产品代码没有改变。

先设计 `627e627`，本轮证据 `c5e79e0`，分支 `codex/frontend-latest-preview`。新建单独 git archive 快照，85 个源码/锁/契约文件逐项 hash 与 bc5 相同，运行前后再核一致，源码文件0444/目录0555、Vite独立cache，原锁依赖未安装/更新。旧9560前端/5dcb后端快照、启动器及私密账号说明副本保留。

旧 PID63514/72044 在两次核 UID/starttime/PGID/command/cwd 完全相符后逐个 SIGTERM 正常退出，没有按端口盲杀。新 API parent24604，四 worker24608/24607/24606/24609（24605为resource tracker）；新 Vite24610。后端复用已锁 Python3.12.10 backend.venv，私密环境复制仅替换 PYTHONPATH；新启动检查 unauth `/auth/me`=401、Web=200，未需回滚。当前新 API/Web 留运行，私密本机登录说明保持0600、账号密码不变，仅更新版本入口，不公开值。

复用原样907脚本，一次1440/390登录与工作台只读smoke exit0；20API请求=2login POST+18GET，0businessMutations/failedResponses/pageerror，每宽20cards、无横向溢出。四张截图已逐张实际查看，Chrome已关闭。907记录请求及HTTP>=400事件，不是逐条成功状态采集，不能称“20条响应全200”；浏览器上下文关闭也不代表撤销token，按原TTL过期。

准备期一次systemPython tarfile.filter参数不兼容，在任何停服务前失败；原失败保留，改逐成员安全regular相对路径校验后完成归档。初次root.venv缺uvicorn的只读探针失败也保留，随后使用正确backend.venv，无安装。公开本岗输出含解压日志和PNG字节对私密password/完整连接URL做精确内存扫描，零匹配；不称全面安全认证。独立端口/库/私密资料未操作。

证据入口：`agents/frontend/latest-preview-validation.json`、`latest-preview-prepared.json`、`latest-preview-switch.json`、`latest-preview-secret-scan.json`、`latest-preview-smoke/results.json`。本岗WORKLOG/module/handoff及 `records/prompts/ROLE-frontend-LATEST-PREVIEW-v1.md` 已记录。容量和理由功能的现有CI/公开stage04由总协调统一引用，本轮只验证最新预览可用，不重复业务验收；全部为AI岗位工作，不计学生人工修改。
