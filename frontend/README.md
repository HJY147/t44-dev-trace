# 留痕前端

Vue 3、TypeScript、Element Plus 与 Vite 实现的研发交付工作空间。业务请求直接引用权威 OpenAPI，当前显式契约版本为 1.1.0：登录/退出、项目与成员、迭代容量、任务及依赖、七态流转、八段十项证据评审、上线评估与回滚预案、通知、升级历史、项目审计。表单按接口输入结构生成中文控件，字典、模板和规则从服务读取；不包含固定业务数据或假成功。

D005/D006 的版本变化见 `specs/changes/capacity-lifecycle-v1.1.md`，冻结父链以根目录 `records/spec-freezes/` 发布记录为准。`/api/v1` 路径保持不变；fixture 的响应元版本从权威 `info.version` 读取，不另行硬编码，也不改变评审模板等业务版本值。

Node 24、pnpm 11.25.0，在 `frontend/` 执行：

```sh
pnpm install --frozen-lockfile
pnpm dev
pnpm typecheck
pnpm test:coverage
pnpm build
pnpm preview
```

开发服务仅将同源 `/api/v1` 转发到本机 `http://127.0.0.1:18080`。生产构建输出 `frontend/dist`，由 Nginx 提供静态文件和同源 API 代理；非 API 页面需要回退至 `index.html`，API 错误不得回退为 HTML。`preview` 只检查静态构建，不替代生产反代。

会话仅保存在内存，刷新页面需重新登录；口令在请求后清空，不进入 URL、持久存储、日志或截图。写表单按真实操作生成幂等键，网络/503手动重试复用同一内容与键，修改内容才生成新操作；409保留表单并刷新，再由用户明确采用最新版本。相同操作重放后再次读取权威记录。角色、状态、依赖、审核与升级均由服务端判定。

手机使用任务卡片和详情抽屉，不依赖横向表格。证据通过纯文本或经过协议校验的 HTTPS 链接展示，不渲染 HTML。通知已读与处理分别调用接口，不会自行解除阻塞。

自测包含整个 `src/**/*.{ts,vue}`，未排除未测页面；只对行覆盖率设置 80% 门槛，分支/函数另报。fetch 夹具测试与真实浏览器→FastAPI→MySQL 联调分开记录，均不是独立验收或性能测试。证据按阶段保存在根目录 `agents/frontend/`。

f654 的 27 项 CI、行覆盖率 92.79% 及前端 f654／后端 02ec 的 80 次真实 HTTP 是 1.0.0 历史证据，保持原记录。本次 1.1.0 fixture／文档同步不代表 1.1 真实服务联调、容量规则或独立验收已经通过。

## 米咖玻璃视觉阶段

用户指定米色/浅咖、液态玻璃感与圆角；实际使用固定版本 OpenDesign 官方本地技能/模板/设计系统参考，先提交设计原型326f971，再导入生产Vue840b1a8。来源、许可及使用边界在docs/ui/warm-glass；未启动OpenDesign桌面应用或MCP。

导航/顶栏为暖色玻璃，内容与表单保持可读实底，长对话框正文独立滚动。保留无backdrop支持、减少透明度/动效与forced-colors回退。开发服务可用T44_VITE_CACHE_DIR指定独立缓存，多个worktree不要共享node_modules/.vite。

本轮现有27项测试零失败/跳过，全19源文件行310/334=92.81%，最终typecheck/build通过；JS chunk825.22kB提示未隐藏。真实5176→18080/t44_demo_v11只读浏览器验证在1440/390完成40次HTTP（含登录，无业务写），18图逐张看。长表单关闭始终可达、body到底，手机详情标签和底部可达、通知两个0计数分别显示，CDP减少透明度实际匹配。完整结果及失败历史见agents/frontend/warm-glass-validation.json。开发检查不是独立验收或学生手工测试。
