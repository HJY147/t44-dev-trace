# ROLE-frontend-APPLICATION-v1 实际派工

发送者：AI总协调；执行者：frontend AI。以下是实际派工，不冒充用户亲自改码。

```text
开始ROLE-frontend-APPLICATION-v1完整业务前端，不再停壳。用户真实采用Q002方案，D004/U006已存，v1冻结ae60dc3，info.version1.0.0；总协调本地codex/integration整合SHA6afd13fd56d51f27b83ee9847b4e2b0dbd26cc73，含你f261基础、DB事务、BE领域、部署/调度/文档。共享git对象可merge该SHA到你干净独立树保留自身PR14，先安全merge勿覆盖未提交。所有工作继续frontend/与本岗记录，别改后端/spec；更新PR14标题正文为真实最终scope。实现登录/失效/退出、项目选择和创建/成员、迭代与容量、任务列表/详情/登记/负责人/排期差异/依赖/所有七态动作、八段十项评审证据、四视角上线评估+预案审核/经理发布回滚返工、升级历史、个人通知已读与处理分开、项目审计；对接冻结38ops的必要可见业务流程，别写固定假成功/假数据。继续蓝白“留痕”布局，真实中文操作提示、加载/空/403/网络失败/422字段错误/409保留表单并主动刷新，不把读通知当解除阻塞。字典/模板/规则来自API，页面不自己做升级决定或启动前端定时器。后端origin同源/api/v1，root会整合后提供实际服务用于浏览器端到端；当前可用可追踪fetch夹具做模块测试，不能称已真API联调。幂等键每次真实写意图生成，503/网络重试保留同body同key，改内容另新key；重放后GET权威最新状态；Token只用于Bearer，不进URL/日志/截图，不缓存口令；安全显示证据链接不v-html。权限可指导UI，服务端仍权威。响应式手机必要表格改卡片/抽屉，别整页横滚；成功提示说具体结果。
尽快与backend实际交流字段/错误/请求样例需求（Issue2/3），通知领域由messaging后续接入，UI仍你唯一负责。你自己维护package/pnpm锁，新必要测试依赖可加。使用实际Vue组件交互/状态/错误测试，整frontend/src的TS+Vue行覆盖>=80（全量分母，不能exclude未测页面），branch/functions另报不任加80阈值。类型/构建/有意义测试后做headless桌面+手机截图与浏览器错检查；占位fetch测试不冒充真后端。生产有效代码全产品3500–5100行，紧凑可用，拒绝代码填充/生成巨大重复文件。逐阶段自己commit/push PR14、保持真实失败日志/handoff/prompt；已有PR已attach，不需另建。所有代码在自己worktree索引，不联系/读取独立testing内部资料。容量中断从文件恢复，不换模型。先交付实际页面功能，再紧凑记录。
```

后续实际steering：总协调提供真实18080服务和ignored0600账号文件，明确只headless读取、不输出或提交凭据；要求手机卡片、真实中文标签和布尔控件、用户提示避免术语。最终要求尽快提交并释放槽位，消息/升级门面接好后再回归。这些反馈来自AI总协调，不算人类亲改或自动归类幻觉。

上下文到代码：冻结契约→contract.ts/forms.ts/OperationForm；重试与凭据约束→api.ts/workspace.ts/LoginView；全部业务入口→WorkspaceView/TaskDrawer；中文与手机卡片→FieldEditor/RecordList/styles；测试与真实联调隔离→tests/、application-real-browser.mjs及各结果。
