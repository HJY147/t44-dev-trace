Agent-Role: frontend
Prompt-Ref: ROLE-frontend-APPLICATION-v1
Refs: #2, #3

已安全快进到总协调整合基线6afd13fd56d51f27b83ee9847b4e2b0dbd26cc73，按冻结1.0.0开始完整前端接入。当前仅用可追踪fetch夹具测试，不声称真实HTTP联调。

已实际联系backend，并得到答复：HTTP仍在实现，暂不提供虚假运行例；返回按data/meta及Error根对象，422 violations.path采用JSON Pointer（如/字段/数组下标），不回显input；401清内存身份，logout只撤销当前会话；通知待messaging门面实际注入。

前端采用：Bearer仅内存、不写URL/日志；每次写意图保留body和幂等键供网络/503手动重试，内容修改才新意图；重放后GET最新状态；409保留表单、主动刷新，再由用户明确采用新版本。当前请求后端首轮真实响应和HTTP命令，后续另记端到端结果。
