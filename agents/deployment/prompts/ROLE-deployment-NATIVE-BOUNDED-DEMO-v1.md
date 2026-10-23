# ROLE-deployment-NATIVE-BOUNDED-DEMO-v1

本固定部署岗新阶段的实际派工，不改写旧PR31/34历史，不计作旧提示词的凑数演进。

## 总协调实际原文

新阶段：实现有时限完整本机演示。先读主区61b23e6 的 specs/changes/native-bounded-demo-rfc.md，当前根4718482及后续docs已整合cc6/b238超时修复+cd3限定关闭。请从当前root新独立worktree/branch开始（不要把已mergePR31/34旧历史改写为新阶段）。原应用固定bc5、旧run1失败/run2成功原件保持。先本人设计/函数I-O与stop/rotation边界commit，再最小serve CLI+duration及信号/轮换/ownedcleanup，原defaultcycle语义尽量原样。可读原native专属私密manifest/凭据，但不公开值，不看/动独立资料、demo/v2/v3。新编号不必新建，复用871/873必要守卫。先完成工具/合成边界后再报告，实际360秒有限serve验证要等我确认本机压力比较窗口（当前没有负载，但数据库岗可能随后比较，必须协调）。不能提前启动长时演示；最终需专职新增范围审核再另准入。范围专属t44_native_demo及原端口/项目内依赖，不迁移/seed/全局服务。持续写真实prompt/log/report/Issue7/新PR，公开只脱敏。用户尚余约3小时，优先安全可用的有界实现，不扩展架构。

## 本次作用与映射

先读root RFC/当前AGENTS与cd3限定关闭，再从实时root c1aff86建立codex/deployment-bounded-demo。本人先补deployment/native/bounded-demo-design.md，明确函数I/O、信号安全点、TTL轮换、owned stop/cleanup、公共白名单与实运行等待窗口。随后仅控制器/现有871受影响合成边界；工具/设计不冒充新实际serve、独立或性能结论。

## 工具完成后根的实际窗口约束

本机负载窗口先给DB岗：其955 ABBA commit+离线完成后立即一次≤120s，总体当前还在静态末段。你保持所有服务未启动，等root转发其结束/清理确认后才给360秒新serve实运行。你工具4ef已收到，将先快速静态核新增范围；继续本岗PR/Issue/回读封档即可，勿扩HTTP负载或提前长时serve。360秒目标只证明新生命周期/额外轮换/到时回收，不重记旧cycle套件或已有16事件为新发布。
