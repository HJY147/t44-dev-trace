Agent-Role: reviewer / AI
Prompt-Ref: ROLE-reviewer-SESSION-R1-FOLLOWUP-v1
Exact reviewed head: babc60f275ec780bcd3044be455acfddc4a49e60
Product source: 9560e7bd23b68eddbdb733a5ee671999f46a44cd

SESSION-R1在9560范围限定关闭；整产品准入仍不通过。原3c不通过报告、原895红输出及独立FAIL保持历史，不回写为通过。

API现在在fetch失败、响应头和JSON解码后检查原token（api.ts:28–35）；OperationForm在各await恢复/错误回调前检查active+token（:23–55），WorkspaceView在refresh入口先检查active并保护saved/refreshConflict（:27–30、56–67）。旧403/409不再进入新会话恢复链，且同token卸载也被拦截。LoginView旧catch仅在自身存活/token仍属于该请求时清理，TaskDrawer卸载后递增sequence并在任务GET后检查，避免继续二次读取。当前401仍经过统一clearSession；当前网络/503和幂等重试、409/422、历史重放与权威读取没有被禁用；没有取消服务端在途提交的实现或声明。

原895 SHA256 f42aef302d520ef91ffb9afe3938adba5d2220476f5059e43bb4bd36f00aa2e4与公开7a54479字节完全相同。本岗只在babc目标定向重放一次：3/3，exit0；原失败项orphanReads=[]，新user/token/project2均保持。测试标题保留旧3c文字以保证字节，实际源码绑定见重放JSON。没有新实质阻断，未重跑51全套/构建/browser/真实服务/负载。

19源/14冻结/10开发原gzip+可读hash与完整19分母已核。原39项加895三项及邻接9项成为51；旧401只改为更严格SESSION_CHANGED且最终身份断言保留。开发最初同token卸载3红是漏await驱动错，提前全套48绿3驱动错均原样保留；补await且期待不变后隔离旧3c取得真实3红（另41未选），最终邻接9绿、全套51/51，行347/373=93.02%、分支755/868=86.98%。这些为开发证据，不是本岗重复或独立验收。896的8图/60HTTP+2driver logout仅证明正常登录/退出/真实401，未证明真实网络迟到403；本岗仅核JSON，不宣称看过8图。

新八段十项报告：https://github.com/HJY147/t44-dev-trace/blob/19b9d1dd04005cfd1def2bee163a311b1197ed79/reports/reviews/26-babc60f275ec780bcd3044be455acfddc4a49e60.md
一次重放与源码绑定：https://github.com/HJY147/t44-dev-trace/blob/19b9d1dd04005cfd1def2bee163a311b1197ed79/agents/reviewer/evidence/session-r1-babc60f/895-replay.json；原始hash/开发红绿核查：https://github.com/HJY147/t44-dev-trace/blob/19b9d1dd04005cfd1def2bee163a311b1197ed79/agents/reviewer/evidence/session-r1-babc60f/evidence-integrity.json。

正式P95失败、完整独立验收及公开UI002/UI003另期修复未关闭；前轮源码6051超过5100仍未解除，本岗未按冻结政策重算9560，不把旧数冒充新计数。仅COMMENT，无自我APPROVE、reviewer/stage success或main合并。源或base更新后按新SHA复审。
