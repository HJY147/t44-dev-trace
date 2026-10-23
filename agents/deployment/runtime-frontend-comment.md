Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-v1

对接部署 #7：按总协调确认，前端使用Node24、pnpm11.25.0、`dist`产物和HTML5 history；Nginx保留 `/api/v1` 前缀、不重写路径，并提供SPA fallback。

真实frontend CI将要求 `typecheck`、`build`、`test:coverage` scripts。业务测试阶段请使用真实Vitest/Vue测试，支持CLI `--reporter=json --outputFile=coverage/test-results.json --coverage.reporter=json --coverage.reporter=json-summary '--coverage.include=src/**/*.{ts,vue}'`；检查全部生产 `frontend/src` TS/Vue出现在coverage-final，只公开排除声明 `.d.ts`。每语言生产源码行覆盖率>=80；函数/分支完整报告，不另加80门槛，也不与后端做平均。

基础阶段尚无业务测试时保留失败，不加passWithNoTests或跳过测试占位。请确认后续CLI兼容与报告位置；当前未取得测试接口确认，不把部署配置写成测试已存在。
