Agent-Role: frontend
Prompt-Ref: ROLE-frontend-FOUNDATION-v1
Refs: #2

本阶段已经实现真实 Vue 3 + TypeScript + Element Plus 工程与“留痕”工作台骨架，包含项目、交付任务、迭代排期、评审与发布、通知、审计入口，桌面侧栏/移动抽屉、可访问标签和焦点、未连接/空/加载/错误反馈组件。没有假业务数据、业务成功提示或 API 调用。

实际代码：`frontend/`；依赖与 pnpm 锁只在本目录。`pnpm install --frozen-lockfile`、`pnpm typecheck`、`pnpm build` 成功，构建输出 `frontend/dist`；5 项基础反馈/导航模块测试通过。原始结果：`agents/frontend/foundation-validation.log`。

无界面 Chrome 实查 1440×1000 与 390×844：页面无横向溢出、桌面任务导航与标题焦点、手机抽屉导航和关闭通过；零浏览器错误、零 `/api/` 请求。截图和结果：`agents/frontend/screenshots/`、`agents/frontend/headless-foundation-result.json`。桌面 CUA 曾被 Mac 锁定阻断，后续改用预装 Chrome headless，不表示手机真机检查。

契约/DDL仍在审核，尚未收到总协调冻结消息，未进入业务联调。登录、项目数据、任务流转、排期、评审上线、通知、审计业务均未实现；没有业务覆盖率、集成或独立验收结论。后续自测应覆盖全部 `frontend/src` 业务源码及真实客户端错误/重试、权限按钮和关键表单，不排除未测组件。

请部署岗确认：生产静态目录 `frontend/dist`，站点根路径 `/`，页面使用 HTML5 路由需要非 API fallback 至 `index.html`；业务保持同源 `/api/v1` 且保留路径，API 失败不能转成 HTML。目前前端已按此配置，双向确认待回复。
