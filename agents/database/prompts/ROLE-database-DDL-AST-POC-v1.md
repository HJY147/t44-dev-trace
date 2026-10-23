# ROLE-database-DDL-AST-POC-v1：实际派工

总协调原文，操作者为数据库岗AI；只研究/隔离原型，不等于生产迁移或学生亲改。

> ROLE-database-DDL-AST-POC-v1：后续真实优化研究，原代码规模5940超840，审核方案D仅允许先POC，不是凑数迁移。请从根正式freeze189dc4a及当前目录，评估成熟MySQL AST库是否能替换persistence/schema.py与migrations.py中重复DDL/CHECK手写语法处理，保留原C-P4语义检测及原ddl18/226。只先研究/隔离原型，不改生产模块/DDL/API/原freeze，不改backend依赖锁直至证明必要性/兼容/license/净删。候选SQLGlot需查官方主源当前文档/版本/解析宽松限制；不能以parse成功当语义一致、不能从实际反射造预期自比自。对真实权威DDL及原957/956要点做差分：列/类型/nullable/default、index列序uniqueprefix/type、FK目标库列/动作、CHECK字符串/_ascii/_utf8mb4/括号/运算优先级/函数；AST规范化必须区分不等价表达式，不能只是删空白/括号。保留失败，若候选不可行如实结论，不借外部库藏业务行数。原型测试文件分配952（tmp/backend/persistence/952_ddl_ast_poc.py；953已分deploy），不另造未编号测试；root更新ledger。先只做轻量纯解析，不碰任何数据库/不跑seed/重负载（BE正在正式1.1 MySQL，稍后有独占profile窗口）。若需真MySQL再报计划等root调度。估计真实替换后的可读净行数，原321+117不会全删后又保留旧parser，不宣称已节省。自己worktree/记录/prompt/module/handoff/Issue4真实对接/阶段commit，原975 SIM117 BE已获根授权只合并两个with样式，勿并改同一处。独立私有材料禁读，不联系tester。可行时先报告设计和可重复POC证据供总协调/reviewer准入。

957要点仅使用总协调已公布的同名索引/FK/CHECK变异，不读取957原文件或独立私有资料；956为本岗公开回归。

## 总协调本轮收口补充（实际消息）

> 收到36/1保留失败，务必保留且不要改生产旧checker来迁就SQLGlot渲染。这个阶段以可重复POC、真实替换边界/净行数预算及未准入生产结论即可交接，不要求你把所有原型探索凑绿；仅在952补必要区分观察（新AST本身vs混用旧parser），完成当前自然检查边界就阶段commit/释放。后续是否替换由总协调/reviewer另派，生产0节省继续真实。BE当前因1.1内层schema_version出参不遵const导致全CI失败，正最小修代码（契约不变），暂时无quiet窗口。
