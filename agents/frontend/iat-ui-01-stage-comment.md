岗位 frontend；Prompt-Ref: ROLE-frontend-INDEPENDENT-UI-FIX-v1；Refs: #2。

正式已发布UI补充针对e8ceefe6原版本，未当作b485复测；只读取授权.md/.json并核验SHA，未跟随独立私有证据。

确认当前代码仍缺独立通知总计，已最小增加服务端NotificationPage.unread_count/unhandled_count显示，保持本人/project scope；加载和错误时隐藏旧数，刷新/动作后读权威响应，不从当前分页items估算。983新增3项先修前失败、修后通过：跨页完整总计、只处理仍未读、项目乱序/403隔离。原失败与raw gzip留在agents/frontend/iat-ui-01-*。

当前仅针对组小测试3通过，旧13项因-t未选；root profile诊断窗口内未启动浏览器/全套覆盖/构建，后续等静默结束验证。开发回归不代表独立复测。

资源深链目前没有实现参数约定：/tasks、/notifications是区域入口，任务抽屉ID仅组件状态；说明iat-ui-deeplink-boundary.md。未发明资源路由或把环境阻塞误记权限漏洞。迭代空白已有88e7df8修复，但该e8报告未复测它。
