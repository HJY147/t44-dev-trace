# R29 文档资料收集、核验与交接记录

操作者：文档岗AI；Prompt-Ref：`ROLE-documentation-R29-CHECKPOINT-20261029-v1`；资料截止：`6f91960bca1d59b9ac424c082de403241b5f9115`。独立worktree/分支 `codex/documentation-r29` 从协调分支该准确提交派生，未使用根索引。

## 实际收集方式与边界

- 先读项目AGENTS、本岗TASK、team/report-template/implementation-layout/github-workflow；本次明确派工覆盖TASK的初始化历史任务，没有重复唤醒旧队列。
- `collaboration.list_agents`实际只见root、文档、独立性能和提示词四实例；前端/数据库/后端/部署没有活跃实例。本岗按明确授权直接核已发布报告和Git，**本轮未向四开发岗发送询问、未收到其本轮回答**，不伪造采访。
- 与root实际往来为资料范围、核验进展和actor边界；向prompt_engineering_r29实际通知本岗Prompt-Ref和产物映射，收到资料归档进度通知。它们是AI对接，不是学生访谈。
- 测试资料只读协调仓库中具名 `QA772-PUBLIC` 两JSON及公开unit属性；不联系测试岗、不读取测试用例/工作日志/PRIVATE，不沿公开记录中的私密引用继续读取。未读账号/keys/财务私件，未发布教师原文件。
- 新产物只有Markdown工程材料，既有handoff JSON按岗位规则更新；没有Pages/Word/PDF、产品代码、云、HTTP、SQL、测试器或CI运行/重跑/取消操作。学生研究正文和个人感想不代写。

## 具名来源：字节与Git绑定

以下20件全部从本次worktree读取，并与截止提交对应Git blob逐字核同。表中SHA只指该公开文件，不是被测产品SHA。不能把高层报告中的私密原件引用当成本岗已看过该私件。

| 公开来源 | bytes | SHA-256 |
| --- | ---: | --- |
| [reports/final/performance-r29-20261029.md](../../reports/final/performance-r29-20261029.md) | 5510 | `4daebb1187b116e3923a6bb2acd26649f16ea3de892eee066b8da3b6ef782127` |
| [records/ci/r29-7b15f893-40821621806/run.PUBLIC.json](../../records/ci/r29-7b15f893-40821621806/run.PUBLIC.json) | 828 | `0b28f34e34571a67df8958fc8a28d7342bba7aed60190afd9487227d4f79e311` |
| [records/ci/r29-7b15f893-40821621806/summary.PUBLIC.json](../../records/ci/r29-7b15f893-40821621806/summary.PUBLIC.json) | 3566 | `b59df0c288361597e5f53b7639029e77d9c8dff3eb0300054a668a0c79ed4f8f` |
| [records/ci/r29-7b15f893-40821621806/artifact-manifest.PUBLIC.json](../../records/ci/r29-7b15f893-40821621806/artifact-manifest.PUBLIC.json) | 20151 | `239badfe5c6ac7afaa18c2a939fd555c1037d2fea6bef6db23422c835188f3b3` |
| [records/cloud/f7-r29-window-20261029/short-summary.PUBLIC.json](../../records/cloud/f7-r29-window-20261029/short-summary.PUBLIC.json) | 3673 | `c75b11d56f94af904f3ab60d04fc4d0fba5e645e2fa5d67b8c85d6d44768e7c1` |
| [records/cloud/f7-r29-window-20261029/matrix.stdout.PUBLIC.jsonl](../../records/cloud/f7-r29-window-20261029/matrix.stdout.PUBLIC.jsonl) | 5961 | `00480beb0e9d82503b070818fdd6f8a9ad815e8b094d21a0e2f8d2d56c27252b` |
| [records/cloud/f7-r29-window-20261029/QA772-PUBLIC/qa772-final-scope.json](../../records/cloud/f7-r29-window-20261029/QA772-PUBLIC/qa772-final-scope.json) | 521 | `36d97a59548d0e5aab4c8d8a5a154dec9f03dcd5a558c4f2b5e16f595db37b03` |
| [records/cloud/f7-r29-window-20261029/QA772-PUBLIC/qa772-readonly-status.json](../../records/cloud/f7-r29-window-20261029/QA772-PUBLIC/qa772-readonly-status.json) | 512 | `0a265a4cb5240d031370d5225f423912b61fa8032c65b2f8aa991a56d9f933ce` |
| [records/cloud/f7-r29-window-20261029/ROOT-QA772-authorization.PUBLIC.json](../../records/cloud/f7-r29-window-20261029/ROOT-QA772-authorization.PUBLIC.json) | 500 | `a1bcef4984b6d29e59038ff54864001dc60b7dd73dcb08e24c6b5adf01a50791` |
| [records/cloud/f7-r29-window-20261029/start-time.PUBLIC.json](../../records/cloud/f7-r29-window-20261029/start-time.PUBLIC.json) | 219 | `7647560ed4e745e96e9a56efc5320bd2db1f0fd243eb656358e844fba5c7ad6f` |
| [records/cloud/f7-r29-window-20261029/stop-and-continuation.PUBLIC.json](../../records/cloud/f7-r29-window-20261029/stop-and-continuation.PUBLIC.json) | 1080 | `338bbdd273d11b04c79f4633542c805a9db170efcdb96e24699660b835942ebf` |
| [records/cloud/f7-r29-window-20261029/APP-resource-sealed.original.PUBLIC.json](../../records/cloud/f7-r29-window-20261029/APP-resource-sealed.original.PUBLIC.json) | 1394 | `6cb008b0289558c1ad5589e71434f1a79e0ea859f889ec934efe786e2032faaa` |
| [records/cloud/f7-r29-window-20261029/LOAD-resource-closure.original.PUBLIC.jsonl](../../records/cloud/f7-r29-window-20261029/LOAD-resource-closure.original.PUBLIC.jsonl) | 17901 | `aa1f3a706a094ba3dc6f8ca44eca5377e7dbeed9d6282e8f4f426820b5478db9` |
| [records/cloud/f7-r29-window-20261029/APP-services-closed.original.PUBLIC.json](../../records/cloud/f7-r29-window-20261029/APP-services-closed.original.PUBLIC.json) | 12155 | `652de406fde14872ff7968729ce959650e4d971f0fae0c57fd7962f5e716ec55` |
| [agents/database/scale-r29/report.md](../../agents/database/scale-r29/report.md) | 4591 | `d7575de4af559af0a7968c9ef11c255c93f9fdd82b05c562a66e1807cdb51aac` |
| [agents/database/scale-r29/verification.json](../../agents/database/scale-r29/verification.json) | 3818 | `29a08b3898121e071e392b08652f3ac6ee1a84ba24f7ceb1573fbc5db422a469` |
| [agents/backend/neutral-fixture-20261029/report.md](../../agents/backend/neutral-fixture-20261029/report.md) | 3104 | `8ea2fb37fe627dc051b585e56cca603a5d22ef9e910a5bda1fe0283477619201` |
| [agents/deployment/opaque-relay-20261029/CLOSURE-CLI.md](../../agents/deployment/opaque-relay-20261029/CLOSURE-CLI.md) | 2845 | `eb3e85384a21e7b52e1a69883530cbf7e7a82f1a901b684a721e54e15a81e4d0` |
| [records/spec-freezes/v1.2.json](../../records/spec-freezes/v1.2.json) | 5960 | `00e52d9c774a43679071deea5bb14c6e1f654b3529f811faa5b409aa94bd805e` |
| [docs/reports/requirements-source-audit-20261028.md](../../docs/reports/requirements-source-audit-20261028.md) | 12389 | `49adb9439e790f758f61b9d7d6a0f5d765bbcaad90f051aebe94ebdc36340c2e` |

CI的`artifact-manifest.PUBLIC.json`另列97个解包文件。本岗逐件核存在、尺寸、SHA，97/97匹配，并与截止提交97个Git blob分别匹配。**本轮没有重新下载Actions原ZIP，不把解包成员称为本岗新归档原ZIP，也不重复验证云盘上的19.7MB原流。** 云流完整性引用公开收尾回执中APP与LOAD相等的尺寸/SHA。

## 四岗分支与公开结论核对

实际运行 `git ls-remote origin` 精确分支查询，读回以下三个远端head；部署内容已在截止父链中。链接绑定完整SHA，不用会移动的分支名称替代证据。未集成候选保留在其分支，未复制到本岗产品目录。

| 岗位 | 已发布准确head/产品 | 本次读取与限制 |
| --- | --- | --- |
| 前端 | 远端`6aed8b2464aad903f43abac94ac3850e55f7bee0`；产品`56e62caacbe0380d5d82212b0c051a57da23dfd5` | 直接`git show`其`agents/frontend/scale-r29/REPORT.md`；净增4、旧89与新3、初次新测试失败、日志原件保留；不是其本轮给文档的回答 |
| 数据库 | 远端`4223c9ca529420423d14ff82287e8819af2dea0a`；产品`274e2e6bfa6dfb2d90926773002a1a62808ec060` | 读取已集成报告、verification与handoff当前小节；本地168/41相互重叠不相加、初次17skip保留；后发准确sourceCI另列 |
| 后端 | 远端`753f1bff71114dab6fb580936f1ed51f08e7c857`；缓存产品`7d101e02590566bcde5385563c45d9c8866cc53f` | 直接`git show`其缓存/规模报告；净增26、微基准限制、误触发后取消CI；另读中性准备已集成报告，云执行者为root |
| 部署 | 已集成`9e605204d618f8116efdf4cb72f584c27ed76026` | `git show --stat`与公开收尾CLI、模块报告尾节；本地工具交付与root云实际回执分开，不联系独立测试者 |

## 已执行核验与结果

| 核验 | 真实结果 | 不支持的外推 |
| --- | --- | --- |
| 97件CI清单逐件bytes/SHA/Git blob | 97/97匹配，97件均已跟踪 | 未做新下载/新产品测试 |
| 四份原JUnit解析与testcase计数 | fault19、integration102、contract183、全套796；各0failure/error/skip，声明和实际testcase一致 | 子套不累加为1100；不代表独立用例 |
| 覆盖率原JSON分子分母 | 行2500/2771=90.2201371%；分支713/848=84.0801887%；组合88.7814313% | 组合值不是行覆盖率 |
| 前端原结果JSON | 89总/89通过/0失败，success=true；类型与build日志存在 | 不代表新浏览器或云性能验证 |
| v1.2清单15件SHA | 15/15与当前文件匹配 | 规格冻结不代表产品通过 |
| 截止源码与CI源码目录对比 | `git diff --quiet 7b15f893 6f91960b -- backend/t44 frontend/src` exit0 | 不把新source的CI移给旧f7性能 |
| QA772公开结论 | NP_NO_RUNTIME_RESULT；result_present=false；cipher_bytes=76；unit241 | collector0调用不等整个测试器0调用；不能判业务失败/600秒完成 |
| 云封存及保盘停止 | 公开APP/LOAD回执19,661,075B/SHA相同，VMStopped/StopCharging/autoRelease空值对应UI“-” | 未读私密控制台截图、未重验云原流、未查账单，不称零费用 |

## 本岗实际遇到的问题

- 初次读取历史日志/handoff输出过宽被截断，改用精确小节/短字段，不猜缺失内容。
- 读取不存在的`specs/architecture.md`退出1，之后改读真实`specs/backend-design.md`及根`architecture.md`；查询猜测部署分支名返回invalid object，改用已知准确提交9e605204。均属文档定位错误，不是产品失败。
- `rg --files`默认忽略coverage等目录造成清单显示不全；直接按97件manifest验证存在、读取字节并核Git跟踪，确认并非归档缺失。没有为此修改忽略规则。
- 本页记录的是资料核验，业务/集成/独立/性能测试执行数均为0；不把这些定位错误或后续Git成功计为学生调试或产品通过。

## 交接与冻结

本岗交付[R29 checkpoint](../../reports/final/engineering-checkpoint-r29-20261029.md)、[学生自写素材索引](r29-student-fact-index.md)、本记录及日志/模块报告/handoff/实际prompt。root补充的QA v2当前为纯本地测试器修复pending，本稿不等待、不读取其内部材料，不产生新云或SUT结论。

以下“最终本岗文件核验”由实际执行后追加；未执行项不提前标通过。

## 后发提示词资料通知

提示词岗实际通知其已提交/push：实质175173f308b4d134d481e7141f742b8ddecd9b05，行政HEAD f9d031106ca1a585a218230ede526621cd3d82e7。文档岗随后直接读取该Git对象的`docs/prompting/R29-process-evidence.md`前部事实与边界，并精确`git ls-remote`核远端codex/prompt-engineering-r29=f9d03110。此项是截止后的具名补充，不混进上面20件基线来源或冒称本岗独立复验其81项。其材料同样明确优化稿proposed、用户恢复浏览器与AI签grant归属、研究本人自写。

## 最终本岗文件核验（提交前）

- 新四份Markdown及模块报告新增段共67个本地链接均存在；11个handoff必需字段齐，7个交付路径存在，JSON可解析。
- 准确版本不同、5887/超787、NP/76B和QA v2“结果待完成”边界有据；新增Markdown私钥/常见token形状扫描无匹配，仅为限定文本检查，不声称完整安全认证。
- 初版文档校验错误要求英文`pending`而正文写“结果待完成”，触发辅助assert；改查真实中文后边界检查通过，正文事实未因此改写。随后辅助脚本误把`git diff --no-index --check /dev/null 新文件`的正常“存在差异”exit1当失败，实际stdout/stderr均空；改用真实暂存diff检查。两次属于文档校验器假设错误，保留在此，不算产品失败。
- 范围检查恰为本岗7文件：4份新Markdown、3份既有岗位记录；没有产品/测试/云路径变化。最终暂存检查执行结果随后补记。

- 实际显式暂存7文件后，`git diff --cached --check`无输出；随后以单独命令核真实exit0。handoff被更新的历史顶层值逐项与6f91960b核同，原prompt_refs完整保留为前缀；无历史资料丢失。

## 实际发布回执

实质提交 `9c183a537b9f44bcf39af7c0ca2dc08b627e278b` 已实际push到 `codex/documentation-r29`；`git ls-remote origin refs/heads/codex/documentation-r29`精确读回同SHA，worktree clean。该提交使用`[skip ci]`避免纯文档归档触发产品CI，未修改工作流或降低门禁。未新建PR/Issue评论/审核success。此后仅本岗日志和handoff发布行政补记，最终行政HEAD由交接回复提供，不新增产品或验收结论。

## R29B 后发收集（2530ee2e起点，后发4b4e792b CI）

先核原文档worktree clean且原HEAD为3dfa20f9，再按root指令fast-forward到准确0b、随后2530ee2e。没有覆盖或修改别岗文件。仅追加本岗三份文档及本岗记录，不重跑旧97件资料核验、不读独立PRIVATE或联系测试者。

后端/数据库的公开WORKLOG、模块报告、handoff、实际prompt已定向读取；后端模块报告保留较早“进行中”文字，当前152以其最终report/原XML为准，不伪造岗位本轮回复。两份原JUnit分别152与133，声明/testcase均同且各0failure/error/skip；DB43未选另列。已读d470公开限定审核（技术901a），72不计为产品或owner模块用例总量。

以下8件与准确2530ee2e Git blob逐字核同；集成0b的reviews.py/migrations.py分别与准确41a111f2/8f290307产品blob相同。计数JSON的commit字段准确0b，application.summary为5880/65，逐文件code和为5880、within_range=false。未新跑cloc或产品。

| R29B公开来源 | bytes | SHA-256 |
| --- | ---: | --- |
| [agents/backend/dry-r29b/report.md](../../agents/backend/dry-r29b/report.md) | 2482 | `67058230b7349243d762b5ec1d9a81bef99ea966a7f2fbd681701a21bb7bf372` |
| [agents/backend/dry-r29b/module-tests.xml](../../agents/backend/dry-r29b/module-tests.xml) | 1067221 | `bfee22c4902ce71a3708badf5f6935da262e8c6a9a055a74ae84dd9f0e576bf5` |
| [records/handoffs/backend.json](../../records/handoffs/backend.json) | 165504 | `5508ebbc94cf77bf07144b8ada19c10d3ab9e14f1e6fd0d01f85099ad1e79bd1` |
| [agents/database/dry-r29b/report.md](../../agents/database/dry-r29b/report.md) | 4203 | `11e3171f433ee4b193eff78d51b546c9fb0f7c81514b52433e58bdaa740adad9` |
| [agents/database/dry-r29b/full-local.xml](../../agents/database/dry-r29b/full-local.xml) | 17739 | `73de40b047a54a1b1be97586955d27fcecbbde4ae70079ec320e664cfbed3586` |
| [records/handoffs/database.json](../../records/handoffs/database.json) | 100128 | `3a25b0dc5abd0ba52b4c2466e0c727cc6a110d09274de2d0db9b0ae7a4b3ea9c` |
| [reports/reviews/dry-r29b-20261029.md](../../reports/reviews/dry-r29b-20261029.md) | 9230 | `7f0af7ed2d225db29accf9e7f90d9e24e866de6364952430ae32b54f84819f08` |
| [tmp/768_integration_r29/source-count-r29b.json](../../tmp/768_integration_r29/source-count-r29b.json) | 31730 | `85740515254a489077946d4837e1cbd8a9ddd2fa47a97720daae1b09172e4544` |

准备阶段曾将CI与QA均标pending，未先写passed；之后只据新公开原件更新CI。QA v2.3后续已收到正式PUBLIC且整体NP；准备阶段和CI到达时仍据root转交占位，当前精确终态见本节末；修正后的有限回归/新完整运行仍待后发；不拼接运行段成功。拟免费4CPU Actions子集不升级为8CPU正式环境。旧云NP、旧f7性能、两VM保盘停止保持原范围。

初次读取新count时本岗把groups字典当列表，辅助解析报AttributeError；改按application.summary读取并核65成员和，原数据无改动。该资料解析错误不是产品失败。后读新归档曾沿用旧`artifact-manifest.PUBLIC.json`文件名，实际不存在；按该目录实际`members.PUBLIC.json`修正，只读定位错误保留。后续仅做增量链接/7文件范围校核，不复测旧资料或产品。

### 新CI公开终态与原件限定核验

root转交已提交4b4e792b后，本岗在保留7个自身未提交路径的情况下ff-only到该准确提交；没有覆盖他岗文件。source仍为0b，app目录与先前集成保持不变。以下5份新公开元数据与4b4e792b Git blob逐字匹配：

| 新CI公开来源 | bytes | SHA-256 |
| --- | ---: | --- |
| [summary.PUBLIC.json](../../records/ci/r29b-0bffe0c5-40827655008/summary.PUBLIC.json) | 3250 | `3b34573203efc77a24180beba4d601953248bc8ffdd900d37f986a8b7f1305e3` |
| [run.PUBLIC.json](../../records/ci/r29b-0bffe0c5-40827655008/run.PUBLIC.json) | 12652 | `679fa80f9be263e797f69bc14a0f3029219cd9cbb929365a5d35497e2c62f1ce` |
| [members.PUBLIC.json](../../records/ci/r29b-0bffe0c5-40827655008/members.PUBLIC.json) | 24227 | `825eba3d2cd91898b4081ffb306951838ece7e95f4439fff2b320768e5d005d3` |
| [artifacts.PUBLIC.json](../../records/ci/r29b-0bffe0c5-40827655008/artifacts.PUBLIC.json) | 16164 | `f4ac556eafbf32ef345f9f9f4d712e9ebec39ea7656af12d5072dfc56a675cb2` |
| [diff-check-scope.PUBLIC.json](../../records/ci/r29b-0bffe0c5-40827655008/diff-check-scope.PUBLIC.json) | 965 | `e094f86658587ee633daa4f317dff21af779221f3d5199eb1a5907eb511f7a31` |

- 只核新归档95个成员：5,845,889字节，全部本地bytes/SHA/4b Git blob同；没有重复旧97、没有重新下载或声称本岗核原ZIP。官方4原ZIP size/digest验证属于root归档回执，文档岗在当前仓库没有原ZIP，不补造。
- 新run source0b、四job success、coverage结束06:18:37Z；从新原XML重新核19/102/183/796、声明和实际testcase一致且各0failure/error/skip；原FE JSON89/89，原coverage JSON行2502/2773、分支713/848、组合88.7876277%分列。
- `new_role_specific_local_tests_in_CI=false`：新tmp765/766不在原tmp/backend discovery，152/133和审核72均单独留证，不累加为796；本岗没有新跑这些测试。
- 原build.log第12行ANSI警告确有尾空格，本岗直接核字节仍在。root全量cached diff-check exit2、其他源码/metadata限定0与首次heredoc终止符SyntaxError均按原回执保留；不把整包称clean，也不改原CI字节。
- 当时QA v2.3后置NP及后续待回归来自root消息，之后仅核下列正式PUBLIC，不读取未公开测试器文件。06:18:12Z只读VM列表的STOP/节省只按root转交记载，自动释放仍引用04:59原详情，不声称新查auto。没有新SUT/云执行。

### 正式PUBLIC本地QA终态（70b24c90）

只按root新指令ff到准确70b24c9082e47130c4a58af8ecdccabc3691c8fe，读取允许的下列两件PUBLIC；bytes/SHA与该Git blob和发布回执一致。没有沿引用读取PRIVATE、原cipher、用例或工作日志，没有联系测试岗。

| 允许公开原件 | bytes | SHA-256 |
| --- | ---: | --- |
| [LOCAL_V2_3_SELFTEST_RESULT.json](../../records/qa-tool/r29b/LOCAL_V2_3_SELFTEST_RESULT.json) | 3802 | `49b0f76e1b2f2a1b736236a21c6d48c74ee7679a09c816408097e06baa755468` |
| [publication-receipt.PUBLIC.json](../../records/qa-tool/r29b/publication-receipt.PUBLIC.json) | 495 | `9f4632ddb4a81b5005d856fd36e9196f014d14758ccf3af369a36ace54d4ccaf` |

v2.3的scope严格为`LOCAL_NATIVE_TLS_SIMULATION_ONLY_NOT_SUT_ACCEPTANCE`；05:58:57.014651—06:10:13.225976Z，676.268秒，400客户60+600网络cohort为true、runtime_metrics_verdict=PASS；整体独立结论NP，状态为`NP_POSTCONDITION_INCOMPLETE_AND_LOCAL_FIXTURE_BUDGET_MISMATCH`。快照114、审计100、后置预算未观察286；实际request/post=5/15、要求15/40，原结果未修改。后续正确预算有限后置回归和经协调授权的一次全新完整E2E仍待，不拼接成功段。SUT/cloud0仅属于该模拟；Darwin未运行正式Linux cgroup守卫，拟4CPU免费Actions通用子集不称8CPU正式环境。旧云r29qa772-01 NP不变。

R29B最终增量资料校核：新增27个本地链接全部存在；恰7个自身路径、没有新建文件；handoff JSON可解析且每个被改旧顶层值都与70b24c90基线逐项同存，旧prompt_refs保留前缀。新增Markdown限定私钥/token形状无匹配。本岗7文件显式暂存后`git diff --cached --check`单独exit0；这只检查本岗作者改动，不改写root原CI归档全量exit2。没有重复旧97或重新运行产品/测试/CI/云。

R29B实质提交 `c7d650a3dcb97b03b3681e505704474b034a3dba` 已实际push到`codex/documentation-r29`；远端精确head核同，worktree clean。只补此次行政回执，最终行政HEAD由回报提供；资料截止仍为70b24c90，不跟随或拼接后发未知绿。
