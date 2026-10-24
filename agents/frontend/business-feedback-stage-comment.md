Agent-Role: frontend / AI
Prompt-Ref: ROLE-frontend-BUSINESS-FEEDBACK-v1
Refs: #27

UI002已完成开发修正：从root499a2a4新分支，先设计3c804d3，再产品3628ee1f98647fba3fa5b6b09bd86a06cbd7fc1c。仅forms/OperationForm按HTTP+服务器code+操作+返工schema解释CAPACITY_REFERENCE_INVALID/OWNER_NOT_PROJECT_DEVELOPER/MEMBER_IN_USE，给出先登记工时、保留活动负责人安排及成员/开发角色保护的下一步。共享CAPACITY多因不猜某个负责人；不把已回滚允许移出工时误说成允许移除成员，不建议开发后直接转派。未知/普通字段/503/client0安全退路、R1/接口/业务/错误优先级均不改。

9个业务解释真实组件案例原红、4个退路原绿→同13绿，增加1个上下文边界矩阵后全前端65/65。完整19源行353/379=93.13%、分支783/894=87.58%，main/router仍分母。首个构建仅新用例preset联合类型TS2322，原失败保留；显式Row类型/asRow后含vue-tsc构建通过，受影响13再次绿，828.48kB chunk提示保留，生产相同的全套未无谓重复。

root授权884真实验证仅新增唯一自有合成demo项目41、项目内两成员、迭代41和任务6001，共5件成功API业务创建，不改原项目/全局用户/独立数据。首次MemberCreate驱动错误及第二次TaskMutation解码/选择器错误均保留，之后只读核同资源身份/原值再续用，没有第二项目。最终1440/390各移除活动负责人工时/转派缺工时人员的4次真实422都有清楚解释与追踪号，每次GET核迭代v1/工时及任务owner2/state1/v1未变；50浏览器响应46个200/4个422，浏览器业务成功写0、4图逐张看、无页面异常/横溢出。Chrome19:43:11.666UTC及5176已停，新夹具/拒绝记录保留供审计，不删数据或重置。

证据agents/frontend/business-feedback-validation.json、docs/ui/business-rejection-feedback.md及原始gzip齐全，冻结14/19源摘要校验。UI003只在Issue28协商，没有混入历史出口/显示实现。本阶段是AI开发回归，原独立FAIL保持，申请准确新HEAD代码审核及新隔离独立复测；不APPROVE、不发reviewer/stage成功、不合并main，不解除规模/正式性能/学生本人材料门禁。
