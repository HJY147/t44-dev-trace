# 留痕前端

Vue 3、TypeScript、Element Plus 与 Vite 的工程基础。当前交付工作台、项目、任务、排期、评审与发布、通知、审计页面骨架；数据入口未接通，不发业务请求，不包含示例业务数据或写操作成功提示。

使用 Node 24、pnpm 11.25.0，在 `frontend/` 执行：

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm typecheck
pnpm test
pnpm build
pnpm preview
```

`pnpm build` 先运行 `vue-tsc`，再生成 `frontend/dist`。`pnpm preview` 仅供本地检查，不作为生产服务。

部署约定：站点基路径为 `/`；静态资源来自 `dist`；HTML5 路由需要静态服务将非 API 的页面请求回退至 `index.html`。后续业务调用统一使用同源 `/api/v1`，反向代理必须保留路径，API 失败不可回退成 HTML。本轮没有 API 客户端或访问令牌存储，未进入业务联调。

空态、未连接、加载中与失败反馈由 `DataState.vue` 区分；403 不提供重复访问按钮，409 只发出刷新记录事件，不自动重发业务操作或换幂等键。导航包含跳转到正文、可见键盘焦点及移动端抽屉；页面切换后焦点移至标题。业务枚举、项目权限、依赖与超期判定在后续读取冻结契约和服务端结果后接入。

依赖方案已核对 [Vue TypeScript 指南](https://vuejs.org/guide/typescript/overview)、[Element Plus 按需导入](https://element-plus.org/en-US/guide/quickstart)、[Vite 静态部署](https://vite.dev/guide/static-deploy.html)、[Vue Router HTML5 路由](https://router.vuejs.org/guide/essentials/history-mode.html)。版本与解析依赖锁定于本目录的 `package.json` / `pnpm-lock.yaml`。
