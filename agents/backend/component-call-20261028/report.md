# 后端组件Call实现：净减19行，通知owner接线未完成

实际作者/执行者：后端AI；prompt ROLE-backend-COMPONENT-CALL-20261028-v1。独立分支codex/backend-component-call-20261028，基线5d5e0a15e3b15e2f509c4ae71a927bbc35579be7。先行边界/782测试提交63748058db765e094f0b5012f6f3398edae868f2；实际产品提交**2d947d237328521e46b9766859ca166a4c54f789**已push并远端读回一致。根云/CI候选仍5d，此分支不可作为已联合通过版本部署。

## 实际代码与输入输出

仅两个产品文件变动：services/application.py与common.py。

Business.dispatch保留原collections分支和普通getattr分派，在两者之间按受信静态六项表调用组件。原listMyNotifications/markNotificationRead/handleNotification分别映射notifications.list/mark_read/handle，getEscalationRules/listEscalations/createEscalation分别映射escalations.rules/list/create。所有组件统一输入**同一个(g,Call)**，不复制/转换actor、project、path、body、query、clock，不构造新UoW/事务或绕过认证。组件None仍在访问业务字段前抛503 DEPENDENCY_UNAVAILABLE。返回组件的原对象。

七个旧薄方法(含_escalation)删除，无旧签名兼容壳。内部组件接口迁移由root明确准入；NotificationFacade产品仍旧平铺签名，消息owner已基于本产品SHA另开树负责迁移。本岗未改其文件或开发测试。升级组件原本就是(g,c)，当前六项共用静态分派。

Call.cas新增keyword-only `record_diff=True`。默认保持所有原consumer行为；只在受信调用传False时不执行原版本before/after赋值，保留原列表内容及对象身份，**不是清空diff、关闭审计或跳过事务**。返回、expected显式覆盖、最大版本、版本冲突、updated_at规则、SQL条件UPDATE及其执行时点完全保留。Runtime.audit/outbox/COMPLETE及所有锁/UoW源码不变，开关不从HTTP输入映射。

后续消息owner约定：NotificationFacade.list/mark_read/handle接(g,c)；通知_update先原项目资格/行归属/recipient核对，再**显式c.check_version(row)，然后才求值values(row)**，再c.cas(...record_diff=False)。不得因为Call.cas内部还有检查而把值求值提前；handle不隐式mark_read。notifications无updated_at列，原默认空audit diff必须保持。此约定已直接交消息owner，并给同一解释器/782命令。

## 准确LOC

仅使用既有source_count.py、固定SHA的cloc2.10及原分类；无统计脚本/范围/功能迁出。

- 基线产品5d实际与先行测试源63748058应用相同：**5935**，不是旧a12的5933。
- 产品2d947d23：**5916**，仍超5100达816，require-range仍退出1。
- application.py固定cloc167→147，净减20；common.py140→141，净增1；**实际净减19**。
- git物理diff19add/44del包含空白，与固定cloc净19区分。完整A设计37还包含消息owner预计18，不能把后半未实施提前计入。

计量原件source-count-before.json/source-count-after.json分别绑定63748058与2d947d23，verification.json记录实数和tool hash。当前未解决总体规模/性能/独立验收。

## 真实验证与原失败

新782开发边界先在63748058未改产品真实**8失败、6通过**；后端改后**14通过**，验证六组件准确委托同一对象、缺owner优先、默认diff及False保旧列表、False仍拒旧/最大版本和SQL CAS0、显式expected覆盖及updated_at。假gateway只验证参数化调用/局部语义，不冒称MySQL或完整审计/并发运行。

随后在准确产品2d947d23运行原986 HTTP、987故障、816、856、859五模块及782，共**157项：156通过、1失败、0错误、0跳过，36.50秒**。其中782已包含，不把两次执行重复累加。唯一失败为 `test_default_notification_component_returns_empty_page`：期望200，实际500；旧NotificationFacade.list接收平铺关键字参数，与新(g,c)不匹配。原测试/断言完整保留，没有加壳或把失败说成绿。其余142个既有SQLite目标及14新边界通过。消息owner迁移后须重新验证这个缺口及自身原通知全部断言；此阶段不是端到端通过。

Ruff check首次通过；format首次只因application.py末尾额外空行失败，原format.log保留，窄格式化后3文件format通过。原失败不重写。AST边界证明：common整模块仅去除新kwarg、展开diff的if后与5d AST一致；application整模块除静态表/新增分派与删除7适配器外一致。其它所有产品、Runtime、FrozenAPI/DDL逐字不变；ast-boundary-initial.json保格式化前哈希，ast-boundary.json绑定最终产品哈希。

失败HTTP traceback含1个一次性内存SQLite夹具token。精确原log/XML已保存在 `/tmp/t44-backend-component-call-20261028-raw` (目录0700，原件0600)；提交显式脱敏派生，各1处替换，原/派生双SHA和位置在failure-originals.json。错误、断言、请求ID和失败计数保留，派生XML重新解析通过。其它新782原失败不含凭据且原样保存。

没有MySQL/RabbitMQ、完整开发CI/覆盖率、前端、云、正式性能或独立验收执行；未读783/792私件、不修改学生正文、他岗文件/原测试或门槛。没有为新接口启动自动CI；阶段push带[skip ci]。

## 交接与命令

消息owner `/root/messaging_component_refactor_20261028`已收到准确产品SHA、契约和旧签名缺口，确认只改其NotificationFacade及自身调用，后端两个文件不由其改。root后续负责联合审核/完整回归、固定计量及原严格性能/独立流程。本岗完成后释放槽，不自行扩大范围。

从各自worktree运行：

```sh
PYTHONPATH=backend /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/backend/.venv/bin/python -m pytest -c backend/pyproject.toml tmp/782_component_call_refactor_20261028/782_backend_component.py -q
```

包含旧回归的精确argv与源码SHA在sqlite-developer.command.json；红/绿及静态argv在对应command JSON。主要证据：red.log/xml、green.log/xml、sqlite-developer.log/xml、ast-boundary.json、source-count-before/after.json、verification.json。操作者均为AI，不计学生亲写/人工验收。
