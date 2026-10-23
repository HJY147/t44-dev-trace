# 实际派工 ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

来源：总协调 /root 实际消息，原文：

ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1（实际派工，当前仅准备阶段）：原三批正式负载已于10:52:33Z全部停止，前两批独立岗已报告原定延迟阈值触发；正式数值/缺陷报告尚未宣布发布，root也未读取现有黑盒文件。现在选用根 records/prompts/ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1-proposed.md 的目标/隔离/交付约束；补充本条为实际dispatch，原文件保留proposed历史，不把事后重述/不同任务硬凑六版。先同步根最新397bd79（含DB94b、FEb485、文档6b4、你的3ee，精确父产品43f51570）。阶段A只做源码/官方资料分析和诊断工具准备：逐层区分排队/CPU/SQL锁与连接池/验证序列化开销，先列剖析函数与真实输入输出，不推定瓶颈。可创建唯一 tmp/backend/955_perf_profile.py（955专属你，全局下一个954）及短跑方案，但暂不运行：root正等待独立正式报告发布，DB岗也在实库漂移验证，会竞争同机资源。root将新建t44_profile并提供中性账号；不触及dev/acceptance/perf或不可变API，不读未发布黑盒文件/私有脚本，不联系测试岗。先交准备checkpoint（清楚实验尚未运行），或等root补充已发布报告/环境后继续阶段B。不得删鉴权/撤销、锁/CAS、幂等/独立拒绝、outbox或契约校验来提速；代码规模仍5866超5100，不压行/改计数/搬逻辑配置。真正优化等证据定位后再写，保留原始基线/失败、模块报告/handoff/实际prompt和GitHub交流。

阶段差异：根proposed文件保持历史。实际dispatch明确只授权阶段A准备，覆盖proposed“正式报告已发布后才执行”的准备准入；阶段B实际运行仍须根继续派工/给已发布报告和隔离环境。不同任务不当同任务提示词演进，不凑六版。

## 总协调实际续派：正式报告发布后先业务修复

独立v1现已正式发布，允许你仅阅读 reports/independent-tests/v1-blackbox-report.md 和v1-blackbox-results.json（不要读其私有证据路径/脚本）；两文件root已核对publication_status=final_published，报告SHA edde6aa85653cc697c31d51f7c01d909a399cbc04d4cd40c577c4ed5706c99f8，结果SHA e88a2b30c2823c9fa5f6fd3a6eeaf5d960bc266edce8da98064dcfe519049e0d。优先级调整：先修IAT-v1-01..05中冻结规则明确的业务/契约缺陷（profile955准备可暂交但不先大优化）。root核实frozen createReleaseAssessment.description明确“创建...并清空旧上线批准引用”，IAT01真实违反；createTask的CAPACITY_REFERENCE_INVALID明确“任务人力...不匹配其迭代容量记录”。IAT03 task_id0审计503；IAT04 public审计只version不能重建计划（内部schedule_changes已有值不代表外部可见）；IAT05 evidence空应EVIDENCE_REQUIRED、contract-validations顶层附加字段PARAMETER_INVALID而候选payload非法CONTRACT_INVALID。请先按原契约独立复现，补开发回归，保持CAS/事务/幂等/冻结11不动；检查新评估B后旧A审批能否又激活、重放创建是否反复失效等邻接路径，勿扩大未定义业务。容量赋值等若发现真实契约范围歧义先列给root，不擅改冻结文件/发明错误码。新必须回归脚本可复用986/985；955继续专属诊断，全局下个954如需新文件先报备。修复IAT01可先小checkpoint并CI，再做其余；不读未公开独立用例，不联系测试岗。性能三批P95=3035/1908/5506ms，零稳态失败、吞吐均达标；公开报告含负载模型/同机背景限制，阶段B剖析在业务修复checkpoint后继续，最终独立复测另建无历史实例。

## 总协调实际范围确认与运行纠错

范围确认：02先仅冻结createTask明确的iteration.capacity匹配，不新增预算规则。changeTaskAssignment+changeIteration容量移除的生命周期已向用户提出具体业务二选一，待真实回复后再正式v1.1追加，当前不靠猜测改冻结11件。04先完整公开任务/返工五计划字段和版本，iteration.capacity完整公开差异另记录未决设计项，不为凑完整把大值截断或改成不可读摘要。03 bounded attempted引用保证拒绝审计持久化，原invalid数值若需额外记录用现有安全允许field/字符串且契约限制内，不能DDL扩宽。

具体环境纠错：955当前代码/plan默认硬编码18082，该口仍是独立原性能API PID16590，不能绑定或停它。阶段B前把你自己的诊断tool固定改为18083（或显式受限port参数18083），更新plan和metadata实际port。不算生产源码优化；此工具目前未运行，保留原准备稿和后续修订原因。root只准备profile库/账号，没有诊断服务。

剖析证据再补一个真实性点：955 metadata目前只git HEAD，若PYTHONPATH仍指rootprofile快照会出现“记录新SHA但实际import旧源码”。阶段B前记录实际 t44/api/contracts模块__file__和关键源码SHA，确保env显式指正在测的精确源码；argv无DSN。stageB先1/8/32短样本/1worker定位，不能把它与原4worker正式批直接宣称性能收益。业务修复仍优先。

文档岗已启动4份技术审阅Word生成/逐页渲染（不代写学生研究正文），会先回报渲染窗口。你业务checkpoint后先发阶段B准确源码/短跑计划，root会协调文档CPU窗口；目前未授权与Word渲染同时跑诊断负载。最新root2e0481f归档了0448fec完整CI335pass0skip行88.47%/分支77.73以及同SHA新容器恢复，不需要为这些源码再重复测试。

## 实际短诊断窗口续派

479已root合入e62f753，最小diff读过，11冻结hash匹配、27个IAT公开日志/Xml scoped token pattern检查0匹配。文档岗收到先不启动LO重渲染，已给你优先保留5–8分钟诊断窗口。待你确认479/3b6的CI业务回归通过，可开始计划中1/8/32短跑（955→18083，t44_profile only），启动/结束即时通知我；保持结果按exact actualimport SHA，原稳态400/600不改、不把1worker对4worker外推。

认可先契约校验单入口测量，有证据再分流转/升级；工具小提交后按actualimport精确SHA执行。若用1:1:1 fixture，断言HTTP200且业务valid=true/violations空，不能只检查传输200把非法候选当成功；凭据/载荷自由文本不进归档。诊断窗口仍为你保留，文档LO暂停，前端只小组单测。开始/结束给UTC即可；原正式基线API400VU/4worker仅留历史，不比较成收益。

当前UTC11:50:26，请自然边界确认实际负载/18083诊断进程是否全部结束；文档LO仍hold，只有收到你结束确认才放开。若还运行给预计剩余即可；不需提前解读未完整数据。

## 第二实际窗口与收尾后的控制器约束

独占本地诊断窗口现在开始（UTC约12:50，预留3分钟，到约12:53）；你可执行所报45/40/10秒矩阵。DB已确认无本地负载并暂停安装/解析/测试；deploy已通知暂停本地测试，当前只实现/资料/远程GHA。根已正常SIGTERM收尾明确完成的旧e8测试服务15690/16590/27817，保留全部旧DB/私有证据不读取不改；MySQL13306和dev18080仍在。根窗口内不做测试/统计/渲染/构建，只轻量日志/GitHub元数据。任何bootstrap失败立即停留证据并释放窗口；成功后CPU/SQL各阶段可观测范围要严谨，不能将db_acquire_and_pre_ping纯说poolwait或pre_runtime纯说线程队列。完成正常退出/无本岗process后立即通知释放。

收到，当前窗口释放；bootstrap成功但0业务样本，连接拒绝是测量生命周期错误，不是产品P95/业务失败。请保存首轮准确时序和失败。下轮必须单个持续运行控制器在一次exec_command里管理服务启动/ready→bootstrap(如已有fixture可复用但先valid sanity)→1/8/32矩阵→正常收尾；控制器不能依赖你下一工具调用才发请求。可在既有955加orchestrate模式或一次内联Python subprocess编排并保存实际argv；不再用45秒短服务跨工具等推理。现有服务上限120s可用，矩阵完成主动正常stop，异常finally清理，底层仍三个独立baseline/timings/profile服务。控制器本身先commit（源码/955干净）后再样本，明确生产字节仍8f，不必因此重复全CI。准备好单命令和预计≤3min后报我，再开quiet窗口；不要立刻负载。原502仅支持假设，记录准确。

## 第三窗口实际授权与失败后范围（原文）

quiet窗口现在开始（UTC约13:18，预留到13:21）可执行245e56b的单命令连续控制器，70–100s/总deadline160s。根已合245，application byte-identical4c（CI394pass/全43lines88.726已归档），14freeze不变。DB已完成释放且无进程，deploy暂停本地guard只远程/写代码，独立新实例纯计划无SUT负载，根不做测试/计数/构建/渲染。务必单个exec执行自动ready→sanity→矩阵→finally收尾，bootstrap/sanity任何失败就停留证据；不要因下一工具调用晚而空跑。结束无本岗进程后立即通知释放，raw fixture/token仍私密0600。

窗口释放，已通知deploy。请只定位结尾RuntimeError/保存完整失败命令及原始metadata，先不重跑负载；若采样所有组内容/时间/计数/源hash真实有效，标“子阶段有效、整体controller失败”并用原件离线分析，不能把RuntimeError改成成功或丢弃已收有效样本。若是最后assert变量或写摘要异常，修工具后仅用已保存metadata验证汇总逻辑（另记录离线重处理），不应为绿色再重复整矩阵。诊断结论先基于可验证有效样本，CPU/SQL边界限定，原正式400/600失败仍历史。

请先反馈可验证的最小观察：baseline/timings 1/8/32各请求数/P95/错误及3个cProfile最显著CPU热点（限定inclusive时间），不必等完整报告/压缩归档commit全部整理完才告诉根；随后再交完整证据。保留controller整体exit1与错变量根因，离线汇总修正不称重新运行成功。需要优化的话先据真实热点给最小方案，不改授权/guard/结果校验/数据库pool等无因果依据部分。这样根可调度下一步，避免日志整理堵住关键开发链。

执行对应：root收到六组最小观察及逐类inclusive补充后，继续离线归档；两行赋值修复/static不运行负载，生产不变。原报告/控制器失败不覆盖，不将工具修复或AI互纠算用户亲改。
