# 本轮真实失败与处理

1. 初次通过绝对 Node 调用 pnpm run build，但子脚本 PATH 不含 Node，vue-tsc wrapper 报 `exec: node: not found`。随后给子进程 PATH 加入已知 Node bin；未修改系统配置。
2. 实际安装最新 TypeScript 7.0.2 后，vue-tsc 3.3.13 在解析 `typescript/lib/tsc` 时抛 `ERR_PACKAGE_PATH_NOT_EXPORTED`。查阅官方 vue-tsc 和 TypeScript 文档，并依据实际兼容失败固定 TypeScript 5.9.3；后续完整类型检查成功。
3. 初次 Vitest 执行未收集到测试，报 Element Plus `base.css` 的 `Unknown file extension ".css"`。按 Vitest 官方文档给 test.server.deps.inline 配置 element-plus 后，5 项测试真实通过；未删改断言来绕过失败。
4. CUA 检查返回 Mac 锁定、无可用浏览器。总协调明确建议后改用运行时 Playwright + 预装 Chrome headless；1440/390 检查和真实截图成功，仍不声称手机真机或业务验收。

上述均由 frontend AI 处理，未发生用户亲自改码。最终成功原始结果见 foundation-validation.log、headless-foundation-result.json；这里记录实际错误与纠正，不将所有配置错误自动归类为已确认 AI 幻觉。

参考：
- https://github.com/vuejs/language-tools/blob/master/packages/tsc/README.md
- https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html
- https://vitest.dev/guide/common-errors
