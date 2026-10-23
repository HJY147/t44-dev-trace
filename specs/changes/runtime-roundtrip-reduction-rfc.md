# 内部RFC：减少重复事务边界，保留实时检查

状态：设计草案/未应用，等待总协调选择一项并限定审核；不是规格冻结、实现或性能通过。依据生产5dcb73cc10c38deb14fae68d33318b04d538fecf；工作树集成e850af5，后端同该生产对象。ABBA解释见agents/backend/contract-abba-interpretation.md，执行者root，本岗只离线复核。原正式400并发10分钟/P95≤270ms与3500–5100有效源码要求不变。

## 选择与范围

建议先准入候选A **authorize+claim共用首个UoW，但保留两次实时鉴权**，单独改runtime.py。它覆盖18个幂等写操作，包含transitionTask、改期和createEscalation；能静态减少一个checkout/事务提交，不能声称减少一次鉴权或SELECT、也不能保证P95下降。已审5dcb的契约校验路径维持现状。不要一次合入A/B/C：每项独立证明、精确源CI和必要窗口后再选下一项。若A的错误/提交不明语义审核不通过，先停，不靠更少检查替代。

候选B是Workflow按领域实际需要加载依赖、空集合不发前驱SQL；候选C是用jsonschema公开evolve保留完整根解析上下文，移除重复递归ref改写。三个独立未应用patch和实际格式化后的行数预算见agents/backend/runtime-plan-{preflight,dependencies,validator}-not-applied.patch、runtime-plan-loc-budget.json。本阶段只有字符串/AST/项目Ruff/固定cloc静态检查，没有执行候选代码、HTTP、SQL、pytest或负载。

17个GET、login/logout和validateContractPayload不在A的事务合并范围：GET/logout仍先独立authorize结束再validate再原主UoW；login仍先validate再原登录事务；5dcb唯一只读分支原样在prepare之前返回。普通GET单UoW暂不设计补丁，因为会少一次观察在途成员撤销的机会，需要逐操作定义；尤其通知列表现有成员撤销序列化证据不能由通用分支覆盖。无鉴权join或跨事务身份缓存。

## A：实际调用链、输入输出与预算

输入仍是当前Call、原validate回调和同一factory；输出仍是HTTP status/data/replayed/original_request_id。请求body已由api.py:203–213在打开UoW之前完整读取，最多1MiB；事务中只做同步数据库/本地JSON与Schema校验，不等客户端上传、外部HTTP或消息网络。

现状：

```text
U1: authenticate普通读 → commit/close
validate原回调（含规范化）
U2: claim计算摘要 → authenticate(session S) → idem X → claim/replay → commit/close
[若已完成，同原request_id来源重放；不进U3]
U3: authenticate(session S) → idem X/owner → 必需project X → members S → tasks X
    → 原业务/校验 → 成功audit + outbox + COMPLETE快照 → commit/close
```

候选：

```text
U12: authenticate普通读 → validate原回调 → claim计算摘要
     → authenticate(session S) → idem X → claim/replay → commit/close
[已完成结果只有完全退出with后才送回；原response_request_id重建meta]
U3: 逐字原主流程，不复用U12读取的身份/任务/成员资格来跳检查
```

这里仍是每个成功新写3次authenticate：U12普通读一次、session S保护的claim一次、U3再一次。不是只检查一次后缓存。SQLAlchemy RowsGateway每次Session.execute返回dict，没有ORM identity-map缓存行结果；engine.py:98固定READ COMMITTED，数据库岗门面不变。READ COMMITTED同事务的普通SELECT也是各自语句快照，因此U12后半重新读取能观察前半之后已提交的成员变更，不能拿REPEATABLE READ结果代证。[MySQL8.4官方隔离说明](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)

18个操作为createProject、add/change/removeProjectMember、create/changeIteration、createTask、changeTaskPlan、changeTaskAssignment、add/removeTaskDependency、transitionTask、createTaskReview、createReleaseAssessment、reviewReleaseAssessment、createEscalation、markNotificationRead、handleNotification。只改变事务所有权：claim(g,call)变成内部调用者提供当前Gateway，不新建事务；prepare返回需经过with正常退出。运行时生产没有其它claim/authorize调用者；新增测试若直接调旧内部签名须转到真实execute断言，不能伪装业务API兼容要求。

### A的静态持久账本

完整before来源agents/backend/write-path-static-ledger.md。R=可选已有review读取0/1；M=升级收件经理主体读取数；N=本次需新建scan_run的0/1。此表只算正常指定分支，不猜正式400任务的项目分布/R/M/N。

| 单个请求 | SELECT（前后相同） | DML（相同） | SAVEPOINT/RELEASE（相同） | UoW/acquire/成功commit before→A |
|---|---:|---:|---:|---|
| BLOCK新key | 22+R | 5 | 2 | 3→2 |
| UNBLOCK新key | 24+R | 5 | 2 | 3→2 |
| changeTaskPlan新key | 20 | 6 | 2 | 3→2 |
| createEscalation新key/新事件 | 24+M | 6+N | 4+2N | 3→2 |
| createEscalation不同key/事件已有 | 21 | 3 | 2 | 3→2 |
| 已完成同key人类/服务重放 | 9/7 | 0 | 0 | 2→1 |
| GET task（不改） | 9 | 0 | 0 | 2→2 |
| contract校验category1/2/3（不改） | 4/5/5 | 0 | 0 | 1→1 |

因此GET→BLOCK/UNBLOCK的一轮UoW由5变4，GET→改期→新升级的一轮由8变6，cursor数不变。不是每个acquire恒有一次网络ping：复用/新建/重连和checkout等待不同，COM_PING/项目connect SET/COMMIT不在原955 SQLAlchemy cursor计数里。A移除一次只读COMMIT调用及一次checkout机会，绝不将其量化为固定毫秒或固定总包数，不改pre_ping/池参数。[SQLAlchemy官方pre_ping说明](https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic)

早期VERSION_CONFLICT例仍BLOCK22SELECT/3DML/2控制、UNBLOCK24/3/2；原4UoW（3commit+1主rollback）变3UoW（2commit+1主rollback）。其他拒绝按实际前缀而非套常数：参数拒绝原授权read commit+audit commit，A是首Tx rollback+audit commit，UoW数仍2；auth拒绝仍先退出失败Tx再独立audit；claim冲突原authorize commit+claim rollback+audit commit，A合并前二为一次rollback，仍不拥有别人idem或覆写其结果。

### A的明确语义变化和保护

1. 本地输入校验期间持有一个普通读事务/连接；原先连接已归池。此前无session S/idem/project/member/task写锁，第二次鉴权的S锁仍在校验之后取得，没有扩大session S持锁窗口。代价是连接更久跨本地CPU，可能抵消省checkout的收益，须测，不能承诺吞吐提升。
2. 成功健康路径保留auth→输入→二次auth→idem→主事务→角色/资源/版本/业务守卫顺序。输入非法不认领key；未鉴权/已撤销/到期/非成员/服务scope先于非法JSON；同key原成功结果仍先于旧expected_version业务检查、不同内容拒绝；整数1/1.0仍先原规范化再算摘要。不会新增批量预检或改变CAS最大版本/容量/证据优先级。
3. 第一普通auth后暂停校验时，session撤销仍可提交；恢复后的原claim session S当前读必须看到撤销/到期，拒绝且无新idem。有效输入前半/后半各用fresh now的原authenticate，非Call.clock；若validate本身先失败则原输入错误优先，不另加新到期复核。成员撤销在claim member SELECT之前提交也须被RC新读看到；若在claim读之后但主事务前提交，原U3重新鉴权/成员S仍须拒绝。不能声称四表原子授权快照。
4. claim已拿session S时CLI相同session X撤销仍等待短事务释放；主写仍session S→idem X→必要project X→user_id有序members→id有序tasks。prepare不拿project/member/task锁；无S→project新增锁链。成员编辑原project X→member X规则、容量/依赖编辑项目X、所有有序task锁不变，不能改为SHARE或去锁。lease比较/owner_token换代/fence照原流程，不新增“仅超lease即拒绝”口径。
5. 首普通只读事务的独立COMMIT故障点被移除，不能称所有注入故障逐条等同；validation失败现在回滚这个无业务写事务，原先它已提交。未知提交发生在U12认领写之后时call.idem已保存owner，仍503 TRANSACTION_UNCERTAIN并同key恢复；没有call.idem时仍原DEPENDENCY_UNAVAILABLE。不得把ACK丢失当rollback成功或另做rejection重复写审计。主U3 commit-ACK丢失逻辑逐字不变；同key恢复/结果重放必须以实库持久值证明，不能只mock抛异常。
6. Rejected/PersistenceError/通用异常只有完全退出U12或U3（rollback/close）后，外层原except才调rejection新UoW、新Session。独立连接可复用池中物理连接，不能说必新TCP。主成功task/子记录/audit/outbox/COMPLETE仍一个U3；拒绝不留业务变更，4xx只有owner有效时完成错误快照；5xx保持PROCESSING，audit失败503/null。不能删除拒绝audit项目/task FK安全查询或存入非法引用，不能声称单库全宕仍必落DB审计。
7. 通知owner、升级owner、Schema请求/响应、response_request_id、只读版本和静态错误码均原样。新增操作若非GET且需要特殊认领规则，必须显式审查prepare分类；不是根据可控客户端method决定授权。

### A准入后必须先红→绿的开发回归（本轮未写/未跑）

复用986_http.py/985_mysql_http.py及现有fixture，不开894新脚本，不接触独立测试。新增性能结构目标在旧代码应真实失败，旧业务断言仍通过；不能把这些新结构红称旧业务漏洞。

- 真MySQL记录成功BLOCK、UNBLOCK、改期、服务升级及完成重放各自UoW/checkout/commit和cursor账，证明只少事务边界、3次鉴权仍真实查库；空依赖仍按旧SQL（A不含B）。记录控制语句/commit/ping边界，参数不落日志。
- session两时序：撤销提交再开始新请求→401；首普通auth后屏障暂停validate，另一事务撤销同session并已commit，再恢复valid输入→claim401且idem无新行。另在claim S读后屏障确认撤销writer等待，释放claim后可提交，U3必须重新拒绝。以事件/提交回执证明先后，不以sleep冒充锁证据。
- 成员两时序：无受保护任务的有效manager/reviewer为被撤销主体，另一manager执行合法撤销；前半auth→撤销commit→后半claim应403；claim读后→撤销commit→U3应403。任务owner/最后经理保护原断言保留，不用非法直接UPDATE伪装API撤销；READ COMMITTED实测而非SQLite代证。
- 时间/输入顺序：初始无效auth+非法JSON仍原401/403；auth后推进到过期，valid输入在claim复核拒绝；invalid输入先原422，无idem；服务scope及1/1.0同key、旧version重放/内容冲突/处理中Retry-After保持。
- 重复claim/owner接管并发、CAS一赢一拒、同项目capacity/依赖有序锁全部既有断言保持；同键并发不能从无PROCESSING空窗重复主执行业务。
- 独立审计：validate失败或主业务拒绝后，证明主Session关闭后才建auditSession且真实DB持久化；按早失败/主失败检查业务/outbox无额外行，审计失败仍503。SQL故障按注入标注，不冒称整库真实宕机。
- commit-ACK：wrapper先让真实U12/U3 commit成功再模拟确认丢失，明确故障注入；首次503、同key重试读取真实PROCESSING/完成记录恢复，业务/audit/outbox恰一次，最终original_request_id来自实际COMPLETE。另覆盖真实commit前失败无业务落库，不能以清理rollback推断服务器没有提交。

达到上述后才跑精确新源CI一次、全43文件覆盖分母不改；收益需要另外协调小窗口的同源对照。412旧绿和本次ABBA不能当A的新验证。

## B：按需依赖读取，单独候选

纯域state_machine.py:100–123/193–203只在START、UNBLOCK回DEVELOPING、REWORK使用dependency_states；REJECT_REVIEW回开发没有此守卫。workflow.py:70–75目前无条件查边与前驱（空IN仍发SQL）。候选保留task读取/第一expected_version检查位置，条件加载上述三类；仅有前驱id才查前驱；其它命令传空依赖上下文，不改typed command/decide。

BLOCK或其它无需依赖动作主流程少2SELECT；UNBLOCK到非开发也少2；需要依赖但空集合的START/UNBLOCK回开发/REWORK少1；非空需守卫保持2。锁阶段的project X、边读、有序前驱task X一条也不删；因此不是删除所有边查询。可选review/assessment读取和错误顺序不变；版本错误仍先于这段，域角色/状态/证据等顺序保留。新差异是无需依赖时不再可能因这些多余SELECT故障先返回503，不能把消除无必要失败点说成所有故障输出相同；主业务失败、审计独立及提交不明均原流程。

若只B：BLOCK22+R→20+R SELECT，UNBLOCK回开发空集合24+R→23+R，非空不变；UoW/DML/控制/commit均不变。版本不匹配在此段前失败，错误账本不变。它不改善createEscalation/候选校验的SQL，不能包称三接口皆优化。净+6有效行，优先级低于A；不为规模指标把条件挤一行。

必要回归：9动作的合法输出/错误优先与旧源对照；START/UNBLOCK回开发/REWORK的空/已交付/未交付依赖和上游后续回滚守卫；UNBLOCK其余环节及REJECT_REVIEW不突然加守卫；目标version/state/权限错误与依赖并存保持原码；真MySQL cursor数和project锁/前驱task锁仍存在，回滚/拒绝audit/outbox/重放保持。只有新增无多余SQL的结构目标应先红，其余业务断言不改。

## C：根解析上下文派生验证器，单独候选

当前contracts/__init__.py每次validator(schema)递归复制schema、改写全部本地$ref、建新FormatChecker和validator。候选创建一个带$id=urn:t44:api的内部完整根validator，公开evolve(schema=schema)每次派生独立实例，保留根registry/ref上下文；删_absolute_refs递归。运行OpenAPI本身/冻结hash不变，根副本$id只用于内部解析，不写回SPEC，不缓存payload/验证结果/身份。

官方公开协议说明evolve创建新validator且保留未覆盖属性和引用解析行为，参考[jsonschema Validator协议](https://python-jsonschema.readthedocs.io/en/stable/validate/#jsonschema.protocols.Validator.evolve)；[referencing Registry](https://referencing.readthedocs.io/en/stable/api/#referencing.Registry)为不可变返回新对象。锁定jsonschema4.26.0/referencing0.37.0；本机只读库源与[官方实现源码](https://python-jsonschema.readthedocs.io/en/stable/_modules/jsonschema/validators/)吻合：evolve传递resolver，iter_errors局部遍历，lookup返回派生resolver；未调用旧RefResolver或私有resolver参数。

这不是预编译或共享验证结果，也不是官方对任意共享validator的线程安全保证。设计约束：根只调用evolve，从不在根上运行iter_errors或改schema；每请求/每次独立validator与generator；FormatChecker现有检查只读、禁止startup后注册/修改checkers，registry不加网络retriever；用户不能提供schema，只是冻结/程序生成的候选payload。当前冻结Schema没有自定义$id/$anchor/$dynamicRef；不能对未来新增解析语义未经审查沿用结论。root+$id、registry同URI及嵌套oneOf引用解析是否与旧rewritten模式逐条同义，必须先回归，而非仅由源码/AST推断通过。

SQL/Tx为0变化；可能减少每次schema递归复制/FormatChecker分配，尚无此部分CPU占比或新延迟数据，不能声称收益。净减10有效行，但影响全38操作、candidate外壳/证据错误分类/成功precommit及HTTP错误响应，证明范围比A大，不因951缺口优先它。

必要等价与并发计划：从38操作的真实HTTP正负请求/响应和现有UTC1000/9999、integer/bool/额外字段等边界验证严格性；参数/主体/返回data/完整envelope引用、所有oneOf/action/category/证据缺失与为空分类、内部schema_version1.0/Meta1.1均保持；独立派生instance id与交错混合schema/valid/invalid的多线程请求不能交叉污染path/rule/错误类别，无共享generator/旧payload保留。对程序生成outer壳与原SPEC一致、未知本地ref不得远程读取。旧递归实现与候选对同一有效/非法JSON样本逐项(path,rule,message)对比，不只断言both truthiness；再用真实HTTP/故障事务证明无commit后响应500。此时才能讨论局部微测/短负载，不能仅离线Schema小例当HTTP通过。

## 实际净LOC预算与门槛

未应用patch按项目既有100列格式化后AST/Ruff检查；固定cloc2.10 hash和原口径分别数原文件/候选文件，不修改统计脚本/分母。结果是草案文本真实差异，生产当前改动0：

| 独立候选 | 原物理行→草案 | 有效代码行→草案 | 有效净变化 |
|---|---:|---:|---:|
| A runtime | 289→288 | 270→269 | -1 |
| B workflow | 256→262 | 247→253 | +6 |
| C contracts init | 71→61 | 55→45 | -10 |

三者合计-5只是账本加和，不是批准一起应用；第一推荐A仅-1。原6051即使三者全部未来等价通过也仅条件性6046，仍超5100，当前绝不能称规模改善已实现或达标。没有压行、挪业务到配置/工具或删除必需逻辑；C删的是递归ref转换，A删的是重复事务所有权，B为明确守卫条件增加代码。以后源码增长/审核反馈以精确新SHA重数。

根选择一项→限定设计审查→明确准入→先保留新增目标真实红→最小生产改动→定向真MySQL/HTTP/静态→精确CI→另协调quiet短测。任何阶段如遇锁/错误/响应差异，保留失败并停止扩大；14冻结文件/旧原始日志及正式失败不改写。普通read合并、一次auth扩大S窗口、鉴权join、project SHARE、审计FK查验省略、task行跨事务缓存均不在本轮准入请求。

## A调用者勘误与窄修正（2026-10-23，尚未应用修正）

前文“生产没有其它claim/authorize调用者”的静态结论错误，不能沿用。backend本次扩检发现真实scheduler/scanner.py:61调用authorize(probe)，probe.operation=createEscalation；tmp/backend/persistence/988_mysql.py:258等直接调用authorize/claim。root设计审查也遗漏，属于AI对AI设计/代码的真实纠错，不是学生发现。精确原A虽25项新定向通过，但原988认领接管和974重复扫描2项真实AttributeError失败，原日志preflight-caller-before.log/xml保留，不称完整整合通过。

root已在816ba60记录并准入窄修正：恢复原authorize(call)四行作为真实调度接口；保留claim(call)三行薄包装自建UoW委托_claim(g,call)；prepare直接在合并UoW调用_claim，不调用旧claim包装、不开额外事务。不改scheduler生产或DB原988断言/字节，不把claim变成会做输入校验/分流的prepare。原算法、错误优先、三鉴权/原SELECT及3→2UoW均保持，B/C仍不应用。

修正提案未应用patch为agents/backend/runtime-plan-preflight-corrected-not-applied.patch；静态AST/格式/Ruff与固定cloc结果preflight-caller-correction-design.json。相对原5dcb，runtime物理289→297（+8），有效270→276（+6），取代此前原A草案-1节省结论。现在不能宣称A减少源码；6051基准即便其它字节不变也会增至6057，此只是预算，不是整项目已实测新总数。原-1预算/patch按历史保留，不能拿它做当前规模结论。

本勘误先单独提交，再应用窄修正并重放原988/974及必要新目标；25绿/2caller红和前置14结构红全部保留。新源完整CI、限定独立审核/性能窗口都仍待后续，不自动负载。
