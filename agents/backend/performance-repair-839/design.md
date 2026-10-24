# C性能修复准备：先分层测量、单一最小候选

后端AI；应用C=0dfb55c2191200d947c5423fd9ee74bb0812cc5a，基root6d02cf1。唯一独立输入为已发表839_PUBLIC_MINIMAL_FACTS_v1.md，SHA c35b37f47d822ef82b4f05627627a2b1f42eb7388c4f2a83d6c13493c5350d4a；不读其余独立文件，不跟private引用、不联系tester。

## 事实和未知

任务组实际400在途、10814稳态请求中1个502，流转/查询短窗P95为3645.763385/3315.969690ms；契约校验预热7273中2个502、稳态0。均未完成600秒，未取得联合资源前不能归属CPU/池/数据库/代理，也不能用其它低并发开发样本替换。后端仅基公开报告保留失败事实。

C的实际调用：api.py同步handle在AnyIO线程执行Runtime；capture先读完body，Server-Timing仅覆盖同步handle，故不能直接称完整端到端。GET任务两次实时auth共8 SELECT、任务1，共9；listTasks加page rows/COUNT，共10；均2UoW。validateContractPayload为单UoW/1auth，通常4 SELECT、带task_id时5；不是任务/发布业务门禁。写prepare把首次auth→输入验证→_claim第二auth放同UoW，主UoW第三auth/锁/业务/审计/outbox/幂等完成，当前共2UoW，不照搬旧5dcb的3UoW数。正常新key BLOCK仍22+R SELECT/5DML/2 SAVEPOINT控制，UNBLOCK24+R SELECT，R为实际旧review引用；不是总网络次数。

MySQLSettings默认每engine5保留+10溢出、timeout10/pre_ping/LIFO/reset rollback，4API+MQ+scanner默认6池理论峰90（额外健康/运维另算）；Settings没有池env映射。建连/认证/3条SET、COM_PING、commit/池reset不全在SQLAlchemy cursor hook中。已有本岗bc5诊断在1/8/32下连接重建和acquire墙钟增长，但只自身小样本；旧池ABBA候选未成为云C，不能移植为本次根因或直接应用15+0。

两代理层：C web api.conf connect3/read30/send30秒，额外TLS helper connect5/read30/send30秒；Uvicorn4workers没有已配置业务总超时。代理读写超时是各自语义，不是30秒总请求限时；本次短窗502不等于已触此超时。C应用正常定义错误为结构化4xx/500/503，没有显式502出口。须由root/部署回收同次两层upstream状态、耗时、进程重启/OOM和资源证据才能定位；不先调timeout/worker/pool以掩盖。

## 可证明的小候选：只加载本次域守卫需要的依赖

范围仅Workflow.transitionTask中版本匹配后、review/assessment读取前的3行依赖装载；不改变Runtime.locked_scope任何SQL。当前C已含project_id+task_id依赖谓词（此前一行候选已集成），不能重复记收益。

域state_machine.py只有StartDevelopment、ResolveBlock返回DEVELOPING、AuthorizeRework调用_dependencies；其它命令完全不消费dependency_states。候选对START/REWORK和UNBLOCK blocked_from_state=DEVELOPING照旧读依赖；依赖为空不再发必为空的前驱IN SELECT。其余动作传空tuple，不读取业务层依赖/前驱。START/REWORK即使当前state非法也仍照原前缀读取；不移动version、角色/证据、review/assessment或D008错误槽。

输入仍同受信g/c/目标task；输出同TransitionContext/域决定/Task/Decision。前提为冻结合法数据：依赖复合FK(project,task)/(project,predecessor)、任务state CHECK有效，Call.task核所属项目。不是通过省读修复损坏历史数据，不保证失效数据库故障会在同一条被删除的无必要SELECT上发生。健康数据库业务错误优先不变；若剩余必需读写失败，仍原主UoW退出后独立拒绝审计/503；ACK不明分类、三次实时auth、session→idem→project X→有序member/task锁、CAS、完整幂等重放/审计/outbox原子性都保留。

预期静态差量：BLOCK减少2 SELECT；UNBLOCK返回非develop减少2（Runtime图边读/项目X/任务X仍保留）；必要依赖且空集减少1；必要且非空集0。不把这些称延迟收益/502修复。预计新条件/空集分支净增加约7行，实数以实际候选cloc为准，不能为规模压排版。

有意义回归计划：旧源通过真实SQLite/TestClient发BLOCK、UNBLOCK回pending、START空集及非空满足/不满足；在实际SQLAlchemy before_cursor_execute记录仅SELECT形状/表名、不保留参数，断言无必要业务查询目标（旧源结构红不称业务漏洞）；任务状态/version、独立拒绝audit、幂等重放和原graph-lock edge读仍有效。复用原986及859全前驱交付场景，不改独立/DB测试，不以gateway mock代替真实SQL。SQLite不证明MySQL行锁；候选后需隔离CI或另授权真MySQL回归，未执行前明确pending。

## 待协调测量（本设计不执行负载）

先从同次公开资源联合回执定位502源：两层proxy upstream_status/addr/connect/header/response时间与API request_id/结构化code、worker退出/OOM/FD/CPU/RSS、MySQL连接/活跃事务/锁等待；只保存脱敏形状/类别，不记SQL参数/口令/Token/body。若旧环境未采则标不可恢复，不回填。随后仅自有库、明确安静窗口与精确源，逐阶段小样本：SQL/UoW/physical-connect/pre_ping/checkout计数；dispatch-to-entry含排队而非纯队列；cursor execute与fetch/codec、auth、本地Schema/wire/JSON CPU、commit/reset分别观测。先复现错误码再选择单变量，禁止自动400×600或以提高超时取消失败。

语义依据只用官方来源：[nginx proxy read/send timeout](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout)说明两次读/写之间的超时；[SQLAlchemy2.1 pre_ping](https://docs.sqlalchemy.org/en/21/core/pooling.html#disconnect-handling-pessimistic)说明checkout探活及其不能修复事务中断；[Starlette线程池](https://starlette.dev/threadpool/)说明同步endpoint使用AnyIO、默认40tokens。本轮首个旧starlette.io链接抓取502是资料工具失败，不是SUT请求；改读官方当前域名，无运行参数修改。默认40不是对云端实际线程采样。

## 规模约束

原C仍5211+1099=6310，上限5100、超1210，实际节省0。复用source-budget-current-C设计：validator旧未应用-10和分页复用估-3即使成立也不足；此次性能条件分支可能反增行，单独披露。没有可信等价删除1210方案，不能删domain/实时授权/审计/outbox/seed/migration、改统计根或压行。更大的任务/门面结构重写须完整I/O和错误映射设计，不能把未经证明的毛重复行扣作节省；本轮不实施。
