Agent-Role: frontend / AI
Prompt-Ref: ROLE-frontend-LOGOUT-CLEANUP-v1
Refs: #25

V2-UI-001已在独立worktree作最小开发修正：先设计844bf71，后产品363ac4d6b7081407bf9086fded2a470ab6b045b8。成功logout/当前401统一清空身份和全部项目上下文，未登录卸载认证DOM及浮层；旧token成功/401和bootstrap/context异步结果不得恢复旧身份。失败logout网络/503保留会话，已发写入仍可能在服务端完成。不改后端、冻结契约、角色/状态/幂等规则。

新增9项开发回归，原75产品7失败/2通过，修后同9全部通过；全前端39/39，完整19文件行327/351=93.16%、分支706/804=87.81%，main/router仍在分母；含类型的构建成功，825.72kB大chunk警告保留。两次运行器路径/PATH错误发生在启动测试前，原始证据独立保留。

独占5176→合成demo18080的真实1440/390浏览器完成logout200、back、reload及重新登录后真实撤销当前session→UI刷新401，DOM认证shell/前项目名/cards/浮层均0。8图逐张查看；60浏览器HTTP54个200/6个预期401，另2个驱动器仅当前session logout200；0业务写/页面异常/横溢出。Chrome和自身5176已停止，独立5175/18084/数据未访问。

证据：docs/ui/session-cleanup.md、agents/frontend/logout-validation.json、logout-before/after.raw.log.gz、logout-browser/first/results.json；全19源hash/14冻结文件hash与原始日志均保留。以上为AI开发回归，原独立FAIL保持历史结论，等待另岗准确提交审核和新的无历史独立复测；不发布reviewer/stage、不APPROVE、不合并main。源码计数政策未改，总规模/正式性能/学生本人材料门禁仍未因此通过。
