Agent-Role: reviewer / AI
Prompt-Ref: ROLE-reviewer-SESSION-CLEANUP-v1
Review target: 3c160c57c56af47eea2c524d93340a679eeb441b (product 363ac4d6b7081407bf9086fded2a470ab6b045b8)

本专项不通过：确认一处 P2 SESSION-R1，需前端修复后按新SHA复审。

[P2] 卸载旧表单的迟到403/409仍可擦除新登录上下文。api.ts:32–35仅在成功响应后checkSession；OperationForm.vue:43–47收到旧403/409仍调用props.refresh；旧WorkspaceView.refreshConflict():59–60再进入refresh(true)，:32在:33的卸载sequence守卫前已调用context()。context():35–36会立即清空当前新身份的project/members/template等，再使用新token读取当前项目。

895纯夹具通过正常App操作复现：身份A提交创建项目POST待定→正常logout200使表单卸载→正常LoginView登录身份B且项目2上下文已加载→A旧POST迟到403→已卸载回调发出/projects/2、/members、/iterations三条孤儿GET；这些额外读取503后，B身份/token仍正确但workspace.project={}。895:64先确认新上下文存在，:67的保留断言实际失败。影响是前端跨会话刷新与上下文擦除；没有证明服务端越权、旧数据注入或新token撤销。

本岗仅执行总协调分配895文件3项无网络探针：1失败/2通过（exit1），原红保留；同项目并发context和旧logout200不清新session两项通过。未替换生产保护，未改产品/冻结14文件/门禁，未重跑已绿全套、构建、浏览器或负载。19源/14冻结摘要、开发原gzip与完整19文件分母已核验；开发39/39、327/351行93.16%、706/804分支87.81%不覆盖此次旧错误回调缺口。60HTTP/8图是开发证据，0业务写，非本岗独立复测。

八段十项报告：https://github.com/HJY147/t44-dev-trace/blob/7a544794de3c9dcfca09b0590c89000ab8bb624a/reports/reviews/26-3c160c57c56af47eea2c524d93340a679eeb441b.md
原失败/源hash：https://github.com/HJY147/t44-dev-trace/blob/7a544794de3c9dcfca09b0590c89000ab8bb624a/agents/reviewer/evidence/session-3c160c5/probe-run.json；探针：https://github.com/HJY147/t44-dev-trace/blob/7a544794de3c9dcfca09b0590c89000ab8bb624a/tmp/frontend/895_session_lifecycle_probe.test.ts。

原V2-UI-001独立FAIL保持历史结论，新的无历史独立复测仍未完成；正式性能及源码6051超过5100（总协调给定，本岗未重算）门禁未解除。同账号仅COMMENT，无APPROVE/成功状态/合并。由总协调转责任岗，本岗不修生产。
