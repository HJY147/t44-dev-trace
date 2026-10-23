# 当前前端资源深链能力边界

依据：frontend/src/router.ts 的路由只来自 navigation.ts 的工作区页面；WorkspaceView.vue 的 selectedTask 是组件内 ref，任务打开时不写 router/URL；项目选择在workspace内存，TaskDrawer根据project-id/task-id发权威GET。已有URL /tasks、/notifications 是页面入口，不是指定项目/任务的资源深链；没有已实现的任务ID query或path参数约定可提供。

因此不能把猜测的 /tasks?task_id=... 或某个 /projects/... URL 当已支持产品能力。独立已发布报告对该步骤记环境阻塞，不是已证明的权限漏洞；本岗不改该结论。

如作业/产品确需可分享资源定位，可另立明确需求：设计带项目/任务ID的真实路由、登录恢复后只从服务端加载资源、成员撤销/403/404时清空旧详情、项目切换和乱序响应隔离，再提供中性URL约定供独立续验。此为未实施建议，本轮只修通知计数，不新增资源路由。

迭代空白选项：该报告对象为e8ceefe6。当前已有88e7df8把FieldEditor迭代标签改为asRow(i.plan).name，冻结夹具/组件和bfa真实HTTP回归可核对；不能声称这份独立报告复测过88e/b485。
