# 2026-10-25 Round8自主续作事实附录

作者、资料整理与本稿操作者：**documentation AI**，实例 `/root/documentation_round8_20261025`。这是可核对的技术过程附录，供学生阅读、判断和自行写作；不是学生本人手写的《AI时代软件工程研究报告》，不记作人工改码、人工识别幻觉或人工校正映射。

产品字节标识为 `935ab5b93bea788672c2b4a088c79cfeed848954`（下称source935）。本稿工作基线为integration `bcf01b1c7e26ac879c40ff479cb0e0978b6eabd7`。公开来源的路径、字节数、SHA-256和Git对象见[来源清单](../../docs/reports/round8-20261025-sources.json)；实际问询及协调转交的中性事实见[收件记录](../../docs/reports/round8-20261025-collection.json)。未跟随来源中的私有路径，没有读取独立测试原始用例、日志、凭据或密文解密内容。

**当前结论仍未达到整体验收。** 新独立F为13 PASS、1 NOT_PROVEN、0 FAIL，整体NOT_PROVEN；source935开发CI四job绿；规模6335/5100超1235。本轮P已有完整认证runner证据：记录600秒核心时钟窗但仅386/400客户端持续、14次传输错误、三目标P95失败，P01 FAIL、完整正式组0、整体NOT_PROVEN；outer supervisor最终状态链仍缺。下文旧结果保留各自source、截止和分母，不以新绿重判旧红。

## 1 需求与设计约束怎样进入修复

[提示词岗截至10:03 UTC的固定附录](../../docs/prompting/CAMPAIGN-20261025-process-appendix.md)保留人的U021/D008选择与1.2父链：上线评估基线和原批准引用同时失效时，先更新评估，再完成原独立评审，由经理决定发布；此规则只细化原批准引用失配槽，不覆盖更早的鉴权、角色、任务及请求评估版本、资源归属等门禁。规格冻结是可实现输入，不是实现或验收通过。

本轮文档岗没有重新读原任务书或私有材料。上述需求与设计依据分别由已发表的[后端报告](../../agents/backend/acceptance-followup-20261025/report.md)、[精确source935审核](../reviews/backend-935ab5b93bea788672c2b4a088c79cfeed848954.md)及固定prompt附录承接；其四权威hash核对和原任务书只读提取是各作者的行为，不冒称本文档岗亲自重做。

原领域发布分支已有state→manager→证据/代码评审→评估/预案/防自审的顺序。后端报告发现批准引用不匹配时，服务层提前选择两个409错误，领域的state/manager守卫尚未执行。新修复只在action7、任务/评估存在且归属与请求版本已经验证、批准引用失配的限定分支，先要求PENDING_RELEASE，再调用既有manager守卫，最后按原D008选择409。三个出口都是拒绝；批准引用匹配及其他动作沿原路径。它不是对所有错误组合实施全局role-first。

## 2 公开缺陷与原始红保持

[v7 F08最小公开差异](../../records/acceptance/817-performance-v7-20261025/F08-minimal-defect.PUBLIC.md)绑定旧source `c8cea7e82805de5283ce67501769fa9a4efc1047`：有效developer无manager角色执行deliver，完整响应409/ASSESSMENT_BASELINE_MISMATCH；契约要求较早403/ACTION_FORBIDDEN。该次原始F08 **FAIL**不重跑、不重判。没有证据表明越权发布成功，失败点后的任务不变与拒绝审计也不能由409推定；原先9项已完成后置条件保留。

[v7性能PUBLIC结果](../../records/acceptance/817-performance-v7-20261025/performance-v7-result.PUBLIC.md)同样保留：D01 PASS（18086请求）、P01 FAIL（1290请求），共19376个完整HTTP200，观察到的同时在途请求未超过1，完整400-client/600-second组0。P01原错误是 `AssertionError: pagination completeness: 8424 expected 8401`：85页audit查询约4.09秒间total从8401变8424，返回/去重8424、无重复ID。它发生在串行预读，不能据此判断吞吐或性能瓶颈；新增audit行来源、快照义务与责任模块仍NOT_PROVEN。

旧F11的输入缺口不推断为产品bug。后端提出自然短TTL human session只是静态可行建议；本轮新F11的专用可弃用撤销session缺口继续作为验证条件未证，不能由AI补写成代码失败或通过。

## 3 后端自造4红→4绿、11邻接及限定审核

后端通过自己的开发HTTP API在内存SQLite构造场景，未取得独立私有ID/fixture。结果见[开发报告](../../agents/backend/acceptance-followup-20261025/report.md)：

| 新目标 | 原产品真实结果 | 候选source935 |
| --- | --- | --- |
| 未批准评估，developer发布 | 409 RELEASE_APPROVAL_REQUIRED | 403 ACTION_FORBIDDEN |
| 批准后改期，developer发布 | 409 ASSESSMENT_BASELINE_MISMATCH | 403 ACTION_FORBIDDEN |
| 合法block到状态3，manager发布 | 409 ASSESSMENT_BASELINE_MISMATCH | 409 STATE_CONFLICT |
| 同状态3，developer发布 | 409 ASSESSMENT_BASELINE_MISMATCH | 409 STATE_CONFLICT |

4个新目标在旧源码真实4失败，候选4通过；既有11个邻接全部通过，合计15个唯一SQLite目标，0失败/错误/跳过。不是15个独立验收case，也不是MySQL并发或全局锁证明。

前两新目标在错误码断言前核任务/评审/评估/决定/排期/outbox六业务表不变、恰一条拒绝审计、request ID关联、同键重放原结果且不增审计；最终候选确认reason_code=6。后两目标检查六表不变和单拒审计，没有新增重放验证。11邻接含manager双失效→新评估→独立批准→发布、历史重放、单批准失效、早期版本/归属/缺失及matching-reference顺序；部分边界使用controlled legacy SQL row，不能冒称真实rework全历史。

[审核岗](../reviews/backend-935ab5b93bea788672c2b4a088c79cfeed848954.md)对73个产品跟踪文件逐字核对，仅workflow.py变化；将新分支恢复为旧失败语句后整个Workflow模块AST等base。auth、Runtime、幂等、CAS、事务、审计、outbox、其他动作、契约和DDL未改。审核机械复算4红、4绿、11邻接及24项seal，未新运行测试；结论仅为准确source935窄修没有本scope技术阻断。missing assessment既有分支与通用错误文案的澄清空间仍保留，不顺手重排。

## 4 准确source935远程CI与证据取得

[CI manifest](../../records/ci/40183757236/manifest.json)绑定run [40183757236](https://github.com/HJY147/t44-dev-trace/actions/runs/40183757236)、head source935，static、coverage、contracts、frontend四job均completed/success。[JUnit复算](../../records/ci/40183757236/junit-recount.json)显示完整coverage/junit为566后端testcase，0fail/0error/0skip；contracts183、fault19、integration93是重叠子集，不能加到566。四个官方artifact的元数据与已下载ZIP大小/SHA核对记录在manifest和各fresh.metadata；本文档岗只读公开manifest/元数据/复算，未重新下载解包或执行套件。

初次签名下载跳转在使用前过期，返回403；后来立即使用新跳转下载并核验。这是证据取得错误，不是产品失败。CI是开发检查，不替代无开发历史实例的独立F、故障、正式性能或人的验收。root另转交后端行覆盖2645/2964（约89.24%），本文档岗没有另开coverage XML复算。后发integration head bcf的[product40186313664公开API回读](https://github.com/HJY147/t44-dev-trace/blob/e45a2b980c6ba8c61761f897414d54a10000409d/records/ci/40186313664/job-status-readback.json)四job均success，[Docker40186313655公开API回读](https://github.com/HJY147/t44-dev-trace/blob/e45a2b980c6ba8c61761f897414d54a10000409d/records/ci/40186313655/job-status-readback.json)docker-application job success；两件readback本文档岗已对主树公开副本与准确提交字节核同。其scope仅API job状态，未归档ZIP，不将source935的ZIP复算移植为bcf artifact验证。产品字节相等据root实际gitdiff转交，不是本文档岗新读实现核对；上述均为开发检查，不合并成一轮独立验收。

## 5 新工具、隔离环境与新独立F

[v8工具/F/P准入审核](../reviews/v8-tool-FP-admission-d11369fae060b1d282f28e5e959abc7853a2d50bb7439178080e28241d084b56.md)绑定freeze `d11369fae060b1d282f28e5e959abc7853a2d50bb7439178080e28241d084b56`。原控制字节prefix/AST保持，新增通用分页观察及原raw资源解析：真实0保留，null/缺口不补值。旧18分页检查7绿11红，新18分页+16资源检查34绿为公开有限工具证据；没有新增完整加密journal端到端证明。快照不可证明时，相关后置与完整正式验收仍NOT_PROVEN，不能因核心窗口指标好看增加完整formal group计数。

旧F授权文件因仍指v7根、旧session说明/截止与旧scheduler PID而被实质拒绝；原admitted=false文件保留。纠正F和精确P各一次phase限定准入，没有延长旧授权，也不预许case通过。两份新环境source935、全新namespace/runid/CA/vhost、只用授权F/P schema，原生TLS；部署原初native-build及后续scope receipt分开，不回写初始pending事实。[部署设计](../../agents/deployment/native-performance-20261025/round8/design.md)和[部署结果](../../agents/deployment/native-performance-20261025/round8/result.md)只负责环境身份、守护、停止和资源采样，不是测试结论。

[新独立F公开结果](../../records/acceptance/814-functional-v8-20261025/functional-result.round8.PUBLIC.json)绑定source935、上述freeze、F native-build SHA `80d8ea9791e9d8e8a6ff9f48240f125bd4af5661347a1385cbb29df0d3b5b594`。独立新实例一次执行、自动重跑0：2026-10-25 10:34:27.210825–10:37:05.469434 UTC，共158.258609秒，14项全部结束，**13 PASS、F11 NOT_PROVEN、0 FAIL；整体NOT_PROVEN**。

实际1083次SUT请求、1083份完整HTTP body与持久完成记录，transport error及completion rejection均0；94个完成后置条件计数、8823个断言。负面HTTP状态包括预期拒绝，不能把403/409等逐个当失败。551个声明错误分支只观察30，521未证，不能将断言数或后置计数当完整case总数。原加密证据完整认证的公开声明保留，本文档岗未解密核验。

F11缺专用可弃用revocation session，自然过期token响应已保留，没有重跑或fixture修补。新F08 PASS仅是本次准确源的新结果，旧source的F08 FAIL保留。物理DDL、架构/规模、覆盖率/CI及人的批准不在本次HTTP证据范围；故障case和本授权内正式性能组均0。进程exit0不等验收通过。

F结束后部署按root停止条件正常停owned环境；最初两次端口检查24398仍false，不能从进程absent推出当时全端口free。10:40:56.264 UTC另查14端口全free，旧false未删；P、共享MySQL和P sampler未被当作F清理目标。

## 6 本轮P认证终章：核心指标失败，外层状态链另有缺口

[本轮P最终PUBLIC报告](https://github.com/HJY147/t44-dev-trace/blob/e45a2b980c6ba8c61761f897414d54a10000409d/records/acceptance/814-performance-v8-20261025/performance-result.round8.PUBLIC.json)是总协调明确许可的单个公开文件，本文档岗直接核对12100字节、SHA-256 `561f333e8283e4ea8a085a7362990052a49870797b3bb55bf1202bc932fce9a9`，主树公开归档副本与新提交Git对象逐字一致；本稿不再转读tmp。报告绑定source935、同v8 freeze及P native-build SHA `bc2b141fb19958d07c684a074c9e640796daa9d4c4553e4ada20a39358f66019`，单次执行、自动重跑0，sealed 11:03:53.907374 UTC。

此前root于10:58:26转交三原PID已不存在、PUBLIC finalstatus缺失，只能作为进程观测。最终认证材料证明runner journal完整finalized、最终summary与journal一致且有finished标记，不能继续把“runner异常退出、未测600秒”当成已证结论；缺的是**outer supervisor最终receipt/status链**。进程exit code不可得，hard-deadline、最终RSS verdict及终止原因均NOT_PROVEN。这两个层次明确分开，本文档岗未读取私有journal或解密密钥。

D01 inventory PASS，40项目/6000任务/9000依赖/15000评审及决定经18086次API请求取得。正式30秒预热cohort启动400/持续400、failure0；HTTP按phase标记的11641次warmup请求包含此前预读，不能把整个标签时段当cohort窗口。稳态核心时钟窗固定为10:46:39.220422–10:56:39.220422 UTC，600秒；cohort启动400，386持续至截止，14提前结束，最大同时网络请求400。结束后的1.383743417秒drain不延长核心计量窗。

稳态134060次request starts，其中134046完整HTTP、14不完整响应；14次ConnectionResetError集中于10:51:31.748048–31.780287，未记录request deadline exceeded。冻结公式在核心窗计完成133674（包含failed samples），吞吐13367.4次/分钟，数值≥1000仅该单指标通过，不能抵销错误/客户端持续/P95失败。升级测的是已有严重超期event去重，不宣称新event生成延迟。

| 指标/目标 | 原冻结结果 | 判断 |
| --- | --- | --- |
| 全400客户端持续600秒 | 400启动、386持续、14提前结束 | FAIL |
| 零错误 | 14 ConnectionResetError | FAIL；根因NOT_PROVEN |
| transitionTask P95 | 3499.286084ms | FAIL，阈值270ms |
| validateContractPayload P95 | 3212.385667ms | FAIL，阈值270ms |
| createEscalation P95 | 3467.956292ms | FAIL，阈值270ms；去重负载 |
| getTask P95 | 3253.577ms | 仅原指标，非另增正式目标 |
| 冻结吞吐 | 13367.4次/分钟 | PASS_NUMERIC_CRITERION_ONLY |

全phase请求163787=163773份完整HTTP+14份不完整，durable result均163787。首个记录失败条件为全400客户端持续600秒，后续terminal postconditions未继续执行，完成后置计数0、完整formal performance groups0。原记录P01 **FAIL**，状态PERFORMANCE_CRITERIA_FAILED_WITH_PROOF_GAPS、overall **NOT_PROVEN**。page-only接口的完整跨页audit快照限制没有绕过。

资源原raw镜像6550785字节、SHA `e96d21fd1be734867c3dd6687dad5b9fca91f81474b52dd3d35dfdbeed84bd97`保持，12858完整行含1702个null与11156个numeric pair，未过滤为numeric-only、未补0/插值/修值。六类资源最后numeric均10:55:21.734974 UTC，距稳态窗末约77.49秒，要求的最终边缘覆盖未达到，sampled coverage NOT_PROVEN；不能用内部最大gap约1.09秒替代尾段覆盖，也不宣称连续未采样值已证。

同宿主Darwin arm64上generator/API/MySQL共机、共享MySQL全进程归属及采样边界均保留；不推云等效或按schema归因。传输异常、镜像尾缺与outer最终状态缺失的因果关系未证，更不自动归为SUT根因。新认证数据补充本轮结果，不重判旧v7 P01 FAIL、不放宽400/600/270/1000/zero要求。

收尾仅据root转交：11:04:53 UTC已停P sampler，11:04:55 controller正常stop所有apps/broker、forced=false。完整owned进程/guardian/端口与原件后验由部署岗收尾；本文档不提前称所有停机已验证、不把行政收尾当性能通过。

## 7 原始失败与更正台账

| 责任与公开出处 | 实际失败或缺口 | 后续边界 |
| --- | --- | --- |
| 固定10:03 [prompt附录](../../docs/prompting/CAMPAIGN-20261025-process-appendix.md) | v5十二写请求先见201但正文Bad file descriptor，完整正文0；原0PASS/12FAIL/2NP | transport socket lifetime后续修正不删除原红，不推写回滚 |
| 同上 | v6 F唯一POST完整201后scope交接未证、14NP；root下界/批准目录前缀两准备错误 | provider准备错误不冒SUT业务bug；后续新grant不回写旧结果 |
| 同上 | v6 P union schema导致unhashable list工具错，D01PASS/P01FAIL | 未进入正式负载；89 generic新绿不改旧P红 |
| [v7 P PUBLIC](../../records/acceptance/817-performance-v7-20261025/performance-v7-result.PUBLIC.md) | audit分页8424 expected8401，P01FAIL | 0完整正式组，不归因快照义务、writer或性能瓶颈 |
| [后端报告](../../agents/backend/acceptance-followup-20261025/report.md) | 主venv缺pytest；首轮Ruff配置/format错误；旧4红；脱敏标记使XML解析失败；全局cached whitespace返回2 | 原件/脱敏派生/无损gzip及各hash分别留痕，不把包装成功当重跑通过；不接触私有原token |
| [source935审核](../reviews/backend-935ab5b93bea788672c2b4a088c79cfeed848954.md) | 一次误读services/call.py exit1 | 改读common.py；是审核路径错误，不是产品失败 |
| [v8准入审核](../reviews/v8-tool-FP-admission-d11369fae060b1d282f28e5e959abc7853a2d50bb7439178080e28241d084b56.md) | helper初次substring sourcecheck误匹配baseline_audits；root初始JSON/binding准备错误；旧F被拒；行政PID复查ProcessLookupError | 改AST/另纠正授权/按真实动态PID披露，不改原文件为绿，不当独立case结论 |
| [部署execution-notes](../../agents/deployment/native-performance-20261025/round8/execution-notes.json) | 首轮3处S102 lint exit1后仍提交；sampler O_EXCL拒已复制canonical，无PID；receipt action缺失KeyError | 155be02限定noqa；保留同bytes/input后让launcher预留；get过滤。后续guard4绿不抹首轮流程失误 |
| [部署结果](../../agents/deployment/native-performance-20261025/round8/result.md) | F停后两次24398 bind false | 后续独立只读全free另记；不推测短时占用原因 |
| [CI manifest](../../records/ci/40183757236/manifest.json) | 初签名redirect过期403 | 新redirect即时下载，官方大小/SHA核验；工具取得错误 |
| [规模方案](../reviews/source-budget-deep-plan-20261025.md) | 最初worktree误建Documents后move；rg不存在requirements目录exit2；静态子任务被中断且未收结论；scan factory原型净0淘汰 | 未冒称独立复核或生产收益，生产变更仍0 |

本稿整理曾两次遇工具输出截断，改按精确字段/路径读取；没有因此推定未显示字段。本稿检查只验证文档链接/JSON/hash/Git差异，不增加产品测试通过数。本轮P的14次传输错误、资源镜像尾缺与outer最终状态链缺口按第6节单列，原因仍未证，不删除本台账。

## 8 规模、费用与人的工作仍在哪里

[主计数JSON](../../records/metrics/20261025-post-role-fix-source-count.json)绑定计数commit `d9e971a631a970d59bdc96923f184c820f6de484`，固定cloc2.10、66应用文件，非空非注释物理代码6335，范围3500–5100、within_range=false；总协调转交该命令实测exit1。**超1235，N07规模不通过。** 本文档岗未重跑计数，也不以新文档行数代替产品主口径。

[深方案报告](../reviews/source-budget-deep-plan-20261025.md)给三条保行为路线：投影/分页估算净省5–20，域DTO适配净增25至净省20，持久记录策略净增15至净省10。小原型投影205→200净5、scan factory314→314净0，均只在临时原型，生产变更0、实际节省0。即使三条最乐观50全成立仍超1185；没有已证足够1235的方案，不将前轮净33重复预支。共享DTO/枚举是否可接受是人的真实架构选择，允许也不承诺达标；固定计量、完整功能、校验和锁序不静默放宽。

本轮新云付费资源0，使用已授权免费本机隔离环境；没有新付费购买。此事实不证明旧阿里云最终账单为0，旧账单未核验边界保持。停止本轮进程、回收归档和账单是不同证据，不互相替代。

学生本人仍须实际完成并手写最终研究报告，独立组织观点与课程建议；人工至少12处改码、3条幻觉识别纠正、5处规格/代码校正映射须用本人before/after、判断和验证证据支持。AI提出分工、发现工具错、修补产品和写本稿均标AI，不计成人工额度。旧Word、封面、既有QA及历史报告截止未重导/回写；当前最终技术Word和提交封包仍需准确新版本另行处理。

## 9 交付与可审范围

本稿新增入口加入[submission-map](submission-map.md)，原正文保留。作者设计、实际prompt、来源hash、问询、轻量验证及本岗交接一并归档。实现d194019已实际commit/push；[Issue9本次评论](https://github.com/HJY147/t44-dev-trace/issues/9#issuecomment-6396883029)已按精确ID GET，正文与本地保存稿逐字相同，回执见本岗agents目录。文档岗本轮应用/测试/SQL/HTTP探测/CI/压测/云/Word执行均0，不给主干APPROVE或全局发布PASS。

本轮P公开认证材料已纳入，核心三目标P95、零错与全400持续条件失败，后置0/完整组0、整体NOT_PROVEN；outer最终状态链和资源尾段仍缺。其他开放出口为F11及未观察错误矩阵、故障范围、规模、人的验收/研究材料、历史最终账单和新准确版本封包，不能由任何单项开发绿抵销。
