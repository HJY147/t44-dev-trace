# ROLE-frontend-INDEPENDENT-UI-FIX-v1 实际派工

派工者：root AI；实现者：frontend AI。用户授权继续。AI识别、AI修改不记为用户亲改。

## 实际派工原文

ROLE-frontend-INDEPENDENT-UI-FIX-v1：固定前端岗继续。根目录 /Users/yang/Desktop/nothing/软件开发大作业，root新HEAD e62f753（含你b485与IAT01～05 BE修复）。只在你自己的干净worktree/index分支codex/做。新的独立UI补充已经正式发布，允许只读 reports/independent-tests/v1-ui-addendum.md 和 .json；SHA分别96257a592fd0fd97ac39866a9512bb1c236d51310cd9ff14d2bc0dee90a9ea6b、1cf910df3c654343c50b035beb1ef78904ac90dc8d0200218ee835ac74e7cc5e。严禁跟随其私有证据路径/读tmp/independent/联系tester。该报告测的是e8原版本，不是你b485复测，迭代空白观察应与既有修复对应，不谎称当时测过修复。
明确缺陷IAT-UI-v1-01：通知页只有共N条和行标记，没有独立未读/未处理总计；API先1/1、只处理后1/0，行变未读·已处理但页无双总计。请核对当前b485仍有则最小修复，使用服务端完整计数，不能用当前分页rows推算，保留project/本人scope、读≠处理，动作/刷新后计数权威更新、快速切项目不串数据。先开发回归复现改前失败再修，现有983/982适当追加有意义的测试，不读独立用例、不可改原独立报告/冻结11件。
深链项独立是“环境阻塞/未声明真实资源URL”，不是已认定权限漏洞，不为凑通过擅自发明资源路由；如当前确实有资源deep link，请只提供真实URL参数和实现证据供root中性转交，否则明确当前能力边界并提出是否需要的技术建议。
当前BE即将对专属profile库短诊断5–8分钟，禁止同时启动全浏览器/全套FE测试重CPU；先源码/小单测/方案，需较重测试或真实浏览器时先通知root等quiet窗口结束。勿动rootVite5174/18081/testerDB。可复用之前dev环境18080等，但root会在BE修复后更新，真实性须记录实际版本。提交本岗日志/模块报告/handoff/实际prompt/真实GitHub对接、阶段commit/push；不得将开发回归写成独立复测。

## 执行对应

静态核对与既有983针对性回归先复现，再只增加服务端双计数显示；诊断窗口不运行浏览器或全套测试。独立报告及其私有证据不修改/不跟随。资源深链现状由本岗router/WorkspaceView的实际实现核对，未新增路由以迎合独立用例。

## 阶段结束实际追加派工

收到。请先阶段commit/push最小修复+原失败/3pass日志+本岗状态，明确全套/覆盖/build/浏览器未跑，然后本轮结束释放slot，避免纯等待占并发。诊断quiet结束后我会用followup_task续同一岗执行必要完整FE验证，不另换上下文。资源深链能力边界写公开本岗报告（当前没有项目/任务资源URL，只区域路由），不编造修复。根会先集成你的明确阶段产物并保留未验证状态。

## 续派验证原文

ROLE-frontend-INDEPENDENT-UI-FIX-v1续派验证：quiet已实际结束，当前BE无诊断服务/负载，文档在LO串行渲染（非性能窗口），可做必要FE验证。你的f654最小修复root已合入，仍只开发3目标case通过，全套未据本地声称。请先查f654准确CI，若完整27用例/typecheck/build/全src覆盖已真正绿且源码未新改，可直接归档原CI证据，不为同SHA重复跑；若CI未覆盖/失败再跑对应必要检查。原3先红后绿日志不改。
真实浏览器双计数需要18080的新准确backend和实际通知fixture。我现在正准备把root拥有的旧dev API18080从b49替换为含IAT01～05的固定快照（t44_dev、DDL不变），不会动tester18081/18082/5174。浏览器写之前等我发ready SHA/metadata；你可先CI/文档轻量工作。沿用本岗958工具/根私密账号，不写新test文件；如需新编号先申请。你自己设计通过公开API创建新通知fixture，root可签发限定dev项目的服务token并用真实messaging进程broker失败fallback落站内通知。请告诉我选用已有专属dev项目ID（之前10）和何时事件就绪，我配合，不直接SQL伪造通知。计数测试须读/处理独立、完整服务端count、刷新/错误/项目切换，不改任务状态来假演示。
新用户D005刚采用容量生命周期规则，root5fb有提案且技术审查中，本轮不要改冻结11/引入1.1逻辑，继续精确f654 UI验证；以后契约演进另派。现仍无任务资源URL的公开边界保留。所有日志/报告/handoff/真实prompt和GitHub阶段交流更新，只有实际browser证据到位才写通过，不称独立复测。

## 实际dev就绪与worker回执原文

Dev ready：18080新API PID34045，固定源02ecdea9ced90cd46cbca898f123d6409f45ba80，backend字节等价3b6dab5（IAT01～05已修，runtime契约仍1.0.0，D005/D006未实现）。t44_dev重复迁移18/226通过，旧root14985已正常停；没有触碰tester服务/库。中性metadata root .agent-worktrees/.runtime/dev-api.json，公开receipt records/validation/dev-api-runtime-v2.json（待root commit）。普通账号仍根 .runtime/api-demo-credentials.json 0600、实际字段沿用旧；project10限定新service token已签到 .runtime/frontend-counts-service.json 0600，仅escalation:write/project10，session_id在metadata，不打印token。可起你自己的5173/headless并用958创建新超期task/升级事件，回报event_id/task_id和大致created_at；root再真实messaging --once触发fallback，不SQL造通知。f654 CI27/92.79已确认归档，无需重复。

真实worker就绪：t44_dev event179 status4终态fallback，已真实生成notifications5→recipient4、6→recipient5，均read_at=null/handled_at=null。task21前后保持state1/version2。用源02ec快照 python -m t44.messaging --once 真实连接本机13307失败后处理，未直接SQL写通知，原始cycle日志与receipt records/validation/frontend-counts-worker.json在root（待commit）。可继续公开API/真实5173 UI双计数验证，不重置旧通知。
