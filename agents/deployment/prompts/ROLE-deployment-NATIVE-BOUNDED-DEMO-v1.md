# ROLE-deployment-NATIVE-BOUNDED-DEMO-v1

本固定部署岗新阶段的实际派工，不改写旧PR31/34历史，不计作旧提示词的凑数演进。

## 总协调实际原文

新阶段：实现有时限完整本机演示。先读主区61b23e6 的 specs/changes/native-bounded-demo-rfc.md，当前根4718482及后续docs已整合cc6/b238超时修复+cd3限定关闭。请从当前root新独立worktree/branch开始（不要把已mergePR31/34旧历史改写为新阶段）。原应用固定bc5、旧run1失败/run2成功原件保持。先本人设计/函数I-O与stop/rotation边界commit，再最小serve CLI+duration及信号/轮换/ownedcleanup，原defaultcycle语义尽量原样。可读原native专属私密manifest/凭据，但不公开值，不看/动独立资料、demo/v2/v3。新编号不必新建，复用871/873必要守卫。先完成工具/合成边界后再报告，实际360秒有限serve验证要等我确认本机压力比较窗口（当前没有负载，但数据库岗可能随后比较，必须协调）。不能提前启动长时演示；最终需专职新增范围审核再另准入。范围专属t44_native_demo及原端口/项目内依赖，不迁移/seed/全局服务。持续写真实prompt/log/report/Issue7/新PR，公开只脱敏。用户尚余约3小时，优先安全可用的有界实现，不扩展架构。

## 本次作用与映射

先读root RFC/当前AGENTS与cd3限定关闭，再从实时root c1aff86建立codex/deployment-bounded-demo。本人先补deployment/native/bounded-demo-design.md，明确函数I/O、信号安全点、TTL轮换、owned stop/cleanup、公共白名单与实运行等待窗口。随后仅控制器/现有871受影响合成边界；工具/设计不冒充新实际serve、独立或性能结论。

## 工具完成后根的实际窗口约束

本机负载窗口先给DB岗：其955 ABBA commit+离线完成后立即一次≤120s，总体当前还在静态末段。你保持所有服务未启动，等root转发其结束/清理确认后才给360秒新serve实运行。你工具4ef已收到，将先快速静态核新增范围；继续本岗PR/Issue/回读封档即可，勿扩HTTP负载或提前长时serve。360秒目标只证明新生命周期/额外轮换/到时回收，不重记旧cycle套件或已有16事件为新发布。

## 根转交独占窗口与一次360秒实际准入原文

准入原一次360秒有限serve实运行。DB已明确结束：23:02:14.376665Z–23:02:53.234248Z，38.842s exit0，18083已空、4own server全退出/本库可见连接0，后续只离线不发HTTP/SQL。本机窗口现在给native独占。root静态预检已commit records/validation/native-bounded-serve-coordinator-preflight.json，code exact4ef57b6129c712c1fad88de56775c53b84009b15 SHA942354...且capture AST=cc6。请新fresh run/准确controller prepare，复用已有受限依赖和bc5只读92files/t44_native_demo现有数据/原prior事件链接，不迁移/seed/reset；duration360从启动到到期包括准备实际以controller定义记录。证明ready、首两次真实60秒扫描、至少一次额外TTL300轮换/旧撤销/新tick、APIconsumerUI单次启动及自动到时ownedcleanup。原run1/2不回改，不把旧16事件当本轮新publish。遇小环境问题可查本人raw后窄修留痕，勿循环全跑刷绿；故障/清理失败立即上报事实。仅这次360，尚未准入长时4hserve；实际阶段封档后由专审新增范围才决定。运行中发start/ready/结束事实，日志私密0600、公件扫已知秘密，写Issue7/PR37阶段commit回读。

## 原360失败后根的实际限定修正派工

收到真实360退出1/自包含runner确定性原因；原失败必须保留。授权先原件封档→设计→窄修verify_stopped只选真实roles generations/APIchildren、external driver wait确认runner；同一自包含反例先红后绿、无OS动作即可。不要自主重跑360或长serve。最终交工具准确SHA+原360公共白名单结果/修复结果/源hash并FINAL，我再让独立专审agent复核，必要后授权一次新的360。所有受保护旧服务保持，当前本机窗口已释放。

本人执行映射：先f1598b9封存原失败与独立postabsence，再补bounded-demo-design停机检查勘误；只现有871三类必要合成案例及verify_stopped角色generation选择，外部driver真实退出独立列证。没有第二实运行/HTTP/SQL，不把新源合成通过当360通过，完成GitHub准确回读后交根复核并结束。

## 根对保护snapshot覆盖范围的实际纠正

读到f159公共serve-run1摘要，原事实保留准确。发现protected_listener_exact_matches白名单是5173/18080/5175/18084/5176/18089/13306；当前独立v3实际保护端口应5177/18086（14262/14268），旧reason18089已退役，5176可能旧空。请不要把这7项匹配写成v3也已逐项核对。离线在设计/说明明确旧snapshot覆盖范围；下一次如获准360 preflight必须新增5177/18086的准确UID/start/argv hash基线保护。不要因此重跑/读取独立应用数据。root可另只读lsof核当前5177/18086仍在，但这不是过去全时未变证明。

## 根专审整合后的唯一新360实际复验准入原文

精确62ac专审a7bad288完成（原SERVE-CLEANUP-SCOPE-01仅限定关闭，同冻结反例一红一绿、无另确认新增P1/P2），root已正确merge16b+a7，HEAD1e9a081703f42dba5fba793c1706a7486933bbdc、appstillbc5。现在授权唯一【新360秒实际复验】绑定62ac/084618工具，不授权4h yet。你own worktree controller/source固定，按原prepare新fresh run/manifest/cookie/vhost，原failedrun不改/不复用；新增外部read-only基线必须含5177/18086+旧7共9端口的listener PID/UID/start/command hash，fresh prepare前→serve前→结束后逐项相同；这是补充观察而非回写旧七端口。不要为加端口修改已审controller/runtime代码，可在本次外部operational driver精确观察，原baseline与额外9项分别标注。当前本机无负载比较，root给予此360唯一runtime窗口；其他agent只offline或hosted，禁止触及独立数据。检查真实ready/两60s新持久ticks/TTL300额外轮换≥1/角色spawncounts、deadline触发、真实exit与cleanup/allownPIDs/workers/brokergone/新portsclosed/9protectedexactmatch；旧16/26勿称新publish、新outbox0如实。每个阶段消息报实际事实，原360 exit1永保留。若新运行失败先seal并只读定位/窄修需报告，不盲重跑。实际结束封档公共白名单+秘密scan+真实私密位置/源SHA/Issue7交接后FINAL。若完全通过，另等root授权最多4h有界用户演示，不自行提前。

本人执行：不改已审工具084618/runtimea251；独立外部operational driver在freshprepare前/serve前/实际结束后对九端口监听PID/UID/start/commandSHA逐项比对，只读监听元数据，不接触独立应用资料。仅一次fresh360，阶段消息如实；私密driver/日志0600，公共只白名单/源hash/实际返回码与基线匹配范围，原failedrun不改。
