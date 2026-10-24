# 6307行规模缺口：静态可行性审计结论

**当前仍为6307行，上限5100，超1207行；没有可信、保持完整行为的1207行缩减方案。** 本轮生产净减0。不能靠“再抽几个class/manager”承诺达标，也不需要用户决定这些内部技术细节。团队应对每个候选的净预算/语义证据负责；本轮不请求改课程范围或计数口径。

数据库AI，基root `f986782311f227082b4445bf7508522aa49c043d`；先行设计提交d8f91d7。公开上一轮分析为后端3b9c907，不接触独立私密材料。本轮仅静态计数、源码阅读和未应用内存草案；没有产品/冻结/DB/服务/用例/CI配置变更，没有测试、负载或性能结果。

## 精确计数与缺口

固定cloc2.10 SHA `bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83`；依旧按非空非注释已提交物理行，Python/TS/Vue/CSS/HTML；只从指定Git对象归档backend/t44、frontend/src、frontend/index.html到项目ignored临时目录，cloc `--quiet --json --by-file --list-file=...`。未把工作树草稿、配置、DDL、测试、部署或副本计入主口径，也不把它们搬动来减数字。`current-count.json`保留66文件原计数/范围/摘要；66项逐文件code值与C6307记录（b66fa36a）完全一致，源码hash按当前root另存static-receipt.json。

6307−5100=1207；需减当前的19.1375%，当前超过上限23.6667%。这是有约束的约五分之一应用删重，不能把大文件总长直接当冗余。

|生产范围|当前有效行|
|---|---:|
|backend/t44合计|5208|
|其中persistence|1691|
|其中services|1613|
|其中scheduling|642|
|其中domain|423|
|其中messaging|357|
|其中contracts Python|55|
|其中根文件api/cli/settings及init|427|
|frontend/src|1084|
|frontend/index.html|15|
|应用合计|6307|

|重点文件（不是可删预算）|有效行|
|---|---:|
| `backend/t44/persistence/seed.py` | 370 |
| `backend/t44/persistence/migrations.py` | 321 |
| `backend/t44/persistence/rows.py` | 299 |
| `backend/t44/services/runtime.py` | 276 |
| `frontend/src/styles.css` | 267 |
| `backend/t44/services/workflow.py` | 247 |
| `backend/t44/api.py` | 244 |
| `backend/t44/scheduling/facade.py` | 205 |
| `backend/t44/domain/state_machine.py` | 193 |
| `backend/t44/services/projects.py` | 182 |
| `backend/t44/domain/models.py` | 177 |
| `backend/t44/services/application.py` | 168 |

持久层1691含迁移/真实结构检查321、seed370、Rows参数化/安全SQL299、outbox167、scan109、schema117及事务/连接/账户/codec等；它们均有当前需求/入口。服务层1613中runtime276维护认证/幂等/成功及拒绝事务边界，workflow247承接七态证据与CAS；纯domain423的类型/命令/守卫不能按相似名称当它们的重复。前端1099已包括米色玻璃主题、表单和真实接口工作台；不删功能/视觉要求的前提下不是1099行任意预算。

## 已做/已尝试：不能再次提前扣减

|事项|真实结果/当前边界|本轮可再记节省|
|---|---|---:|
|删除无人生产调用CoreGateway/TableBinding/可选IdempotencyStore，断言迁到真正Rows/UoW|本岗9aeb阶段已完成并集成；现源没有这两套兼容实现，不能再用旧文件长度抵扣|0|
|受信seed row-builder/默认字段/指针共享，预分组验证|0a676ee已实现并集成；完整小/默认组摘要及后续真实MySQL证据在公开本岗记录。Git净少27物理行是历史diff，不冒充新cloc预算；当前370已是减重后|0|
|后端Call.create/模型/分页/会话发行集中，前端83条未用CSS删除|64b4f89等及bfa1625已实施；后来规定主题/功能补项不等于又有83条可删。已有收益已在6307内|0|
|扫描run完整共享helper|本岗既有等价草案在scans/facade两文件314→315，净增1；14个相同初值key仍有重复，但调用者锁/冲突/返回/事务边界成本不可省，已否决实施|0|
|SQLGlot替整对schema117+migrations321|AST POC保留46/1及13处混用旧CHECK parser不兼容；只可替换旧函数上界171，新AST114，完整assembler/type/接入仍估60–110，联合可能增加3–53；非可删438行|0|
|事务预检合并A|旧-1草案因保留authorize/claim兼容及错误边界而撤回，正确实现270→276(+6)已集成；减少一次事务不是源码必然减少|0|

历史公开阶段总量：5866(stage7)→5940(pre1.1)→5973(1.1)→6124(preflight/UI)→6303(plan理由证据组合)→6307(strict evidence)。这是不同已集成快照，不是同一次改动的独占归因；后加需求/质量修补不能当格式清理删回。快照路径和准确SHA见static-receipt.json。本轮没有通过重跑历史测试解释这些数字。

## 当前具体候选：有净预算也远不到1207

|候选/重复点|旧→草案/预计净省|必须保持的边界及风险|结论|
|---|---|---|---|
|contracts.validator/_absolute_refs重复引用改写→官方evolve派生实例|既有55→45，未实施投影10行|根$id/本地引用/未知引用失败、FormatChecker、错误顺序与完整遍历/前100映射、独立实例/并发。3b9仅19合成样本，不是38HTTP完全等价；构造CPU占比也不是规模证据|仍未准入，可信已实现0|
|CHECK-only小范围AST正常化|旧83、新29；还需8–15行可信语法集合/导入/错误边界，既有估39–46|与整对AST替换互斥，不能重叠扣；需拒绝不等价CHECK/字符集/优先级/函数差异、真实MySQL反射证明及新依赖准入|只是旧POC潜力，非实际净删/当前可承诺|
|NotificationFacade.list页装配→现有common.page|新做纯内存草案：旧片段21→18；完整facade95→92、common132→132，合计227→224，投影仅3行|成员授权S锁完整保留；明确order_by=(-id,)覆盖现有page默认双键；rows→逐行序列化→total→unread→unhandled的三COUNT顺序/谓词/错误保持。只新增page可选order_by参数并用已有helper，既有调用默认不变；仍需BE/MQ owner确认及单独语义回归|实质共享小候选，未实施/未验证，当前节省0|

通知候选保留原分页、三个计数和额外结果，不能把两个额外COUNT删掉换行数；即使同样式的小helper有空间，也只是个位行。原初次静态cloc STDIN漏`-`而exit2，已保留static-count-first-error.log，改用工具明确规定的`--stdin-name=candidate.py -`才取预算；这是静态命令错误，不是产品缺陷/测试红。草案只保存在notification-candidate-budget.json的报告例子里，未写生产/新源码文件。无压行/多语句合并，例子各行≤100，仅AST语法核对而非执行/格式门禁通过。

这些预算不能加成达标承诺；即使最乐观预扣10+46+3=59（本轮明确不扣），也仍差1148。没有千行级共享抽象的可信设计、净删草案或等价证据；继续笼统要求“重构1207”不是可审核方案。

## 给用户的可直接说明

“目前按原规则是6307行，比5100上限多1207行。主要集中在持久层1691行和业务服务1613行；前端1099行。旧的重复仓储、种子默认值、创建/会话与未用样式已经清理，当前数字已经包含这些收益。已验证可行的缩减规模没有达到千行，现有未实施候选只涉及个位到几十行，不能保证等价删掉1207行。代码规模仍未达标，我们会如实交代；不通过压缩排版、隐藏文件或删权限/事务/审计来凑数，也不把技术重构细节交给你决定。”

本阶段结论：维持规模未达标；只建议owner在认为3/10行简化值得成本时另提小范围准入，不以补1207为目标盲目重写。原独立验收、正式性能、人工材料出口不由本报告改变。GitHub Issue4实际评论及全文GET另存本目录；本轮全部操作者为AI，不是学生亲改。
