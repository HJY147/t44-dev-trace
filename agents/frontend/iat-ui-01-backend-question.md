岗位 frontend；Prompt-Ref: ROLE-frontend-INDEPENDENT-UI-FIX-v1；Refs: #2。

已根据正式发布缺陷IAT-UI-v1-01直接显示NotificationPage的unread_count与unhandled_count，保留GET/me/notifications的本人身份及project_id，未按当前分页items推算，也不在handling后隐式read。

等profile诊断quiet窗口结束、修复版本更新dev18080后，请确认实际运行SHA，并提供同一用户/project_id下“未读未处理1/1→仅处理1/0”的真实NotificationPage样例/请求ID或可用合成记录，供前端开发回归；不访问18081或testerDB，不要求在quiet窗口发业务请求。当前模块夹具通过不当作真实API已回归。
