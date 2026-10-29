已完成新完整本机演示的普通身份入口有限开发验证，应用仍 `bc5aef9c62393134582affb7a690acb33ac2b833`，目标 `http://127.0.0.1:5178` → API `http://127.0.0.1:18088`。本岗没有修改产品、服务配置、数据库或后台进程；不是新的独立验收、正式负载或完成4小时演示的结论。

- 从root `13cce419d5232126324ad88c88c26c60dd4a7334` 建隔离分支 `codex/frontend-native-preview`，先设计 `c300560`。原 `907_demo_preview_smoke.mjs` 缺少本轮页面/退出及完整status采集，保持字节不变、不运行冒充；先报总协调，正式分配 `tmp/frontend/861_native_user_preview.mjs`。新脚本80GET上界，网络守卫只允许普通登录/退出POST与必要GET，任何业务写入主动拒绝。
- 861首次一次exit0，1440/390均从2个已有项目选择project2，读取任务20卡、通知5卡（未读5/未处理5，仅查看）、审计20卡，再正常退出。实际70API请求/响应=66GET+2login+2logout，逐条真实status200、requestid70/70；业务修改、被阻断请求、requestfailed、pageerror、横向溢出均0。console仅4条Vite connecting/connected debug。
- 六张认证后页面截图已逐张实际查看，desktop账号显示遮挡，不截已填写登录框/密码，页面数据均合成；两次logout200后登录表单可见、认证shell卸载。Chrome于 `2026-10-24T00:10:43.616Z` 关闭。
- 9个保护端口的listener UID/PID/PPID/PGID/start元数据前后相同，只是两个时点的观察，不是连续监控。没有停止/重配旧5173/18080、新完整演示或独立环境，也没有通知标记、项目/任务/人力写入、reset、CI或全套重跑。
- 普通登录说明与ignored适配JSON均0600，值不公开，未读内部service凭据。已对本岗公开产物（含解压rawlog和PNG字节）做已知普通密码精确扫描，零匹配；截图另经实际目视，不称全面安全/OCR认证。普通login/logout本身可能写会话DB，后台MQ/scan也会继续推进，不能声称所有DB零写。

证据：`agents/frontend/native-user-preview-validation.json`、`native-user-preview-first/results.json`、`native-user-preview-first.raw.log.gz`、`native-user-preview-secret-scan.json`。准确bc5/92源文件身份依据已发布部署 `user-demo-operational-binding.json`，未冒称浏览器独立hash进程内存或读取私密runner。仅本次普通角色/project2页面，不代表所有角色/全部记录和业务再次验收。WORKLOG/module/handoff及真实提示词 `records/prompts/ROLE-frontend-NATIVE-USER-PREVIEW-v1.md` 已同步，全部AI岗位工作，不计学生人工经历。
