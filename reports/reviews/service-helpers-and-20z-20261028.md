# 服务私有封装与新20Z工具限定审核

## 1. 对象、角色与边界

操作者为 AI reviewer，提示词 `ROLE-reviewer-NARROW-SERVICE-20Z-20261028-v1`。独立 worktree 从 `80e891b6` 建立；本岗没有编写或修改被审产品、工具、原测试，也未读取783/792独立私件或联系测试岗。

产品候选为 `5cd0ad43d93bb9066e67bda04337815e6f6fa1b1`，准确产品父基线为 `f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f`，设计与交付留痕为 `50b52755`、`a0ea5969a9f139280592dd6c225ab8cc71945dee`。只变更 `services/reviews.py` 与 `services/tasks.py`。审核分支保留f7产品，用准确Git归档候选作为本地夹具，不自动把新候选带入root的云版本。

工具对象为 backend `7779681010de99cbb4d5946ded9c4bcd5f8ae132` 与 deployment `d7b65303f67075c2239584d61c18ace65e4addfa`；对照旧 `20eb4ae3`、`e1bfc9e7` 和原限定审核 `9538bf50`。此处不审核后续新建的汇总PUBLIC运输包。

## 2. 需求和准入约束

原3500–5100有效应用行数口径未变，含前端/CSS、CLI、迁移与造数实现。原权限、状态、版本、归属和错误优先级不得因重构移动，原业务/密封/预算/截止门槛不删改。20Z是另建目录和新授权的候选窗口；不得改旧16Z文件续用消耗或过期的授权。当前工具只支持短开发诊断，本审核不扩大为600秒性能或功能验收授权。

## 3. 产品行为和错误顺序

`Reviews._assessment_versions(g, task_id)`只统一两次按`-rollback_plan_version`、`limit=1`的原查询。它在原相同调用位置返回原列表：新建评估仍以空列表得到版本1，审核仍保留原`[0]`行为，没有新增空表兜底、提前查询、排序或资源归属变化。

`Tasks._editable_task(g, c, code)`统一原三次`manager → task → prestart`，转派传入`ASSIGNMENT_EDIT_LOCKED`，增删依赖传入`DEPENDENCY_EDIT_LOCKED`，`current_state`原样传递。owner、乐观版本、人力容量、依赖重复/环、edge归属、CAS与审计保留原相对顺序。

本岗用准确AST将两个helper按实参展开，删除其定义后分别比较**整个模块AST**，两模块均与f7完全相同；展开次数为查询2、编辑3。原986测试文件SHA仍`754739a7f0292856fe902ac51bfdae2a31d4a10ae9fe281007576e05a80c25bf`，187条Assert AST保留。此证明针对这里的静态组合，不宣称所有动态子类或外部调用情形已验证。

## 4. 接口、事务和工程价值

没有HTTP/OpenAPI/DDL、SQL网关形参、消息协议、事务或锁边界变化；新增私有方法不形成新的公共接口，也没有全局框架或排除目录中的实现迁移。统一查询策略及任务编辑入口有有限维护价值，收益实际只有4行，不能当作解决剩余规模差距的方案。旧/新抛错的内部堆栈形状可能因增加函数层变化，不作为业务响应差异或测试绕过。

## 5. 20Z原件和运输链

P64新manifest SHA为`2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de`。本岗逐件核13运行文件：9件逐字相同，bootstrap、authority、HTTP、transfer四件只变确切16→20截止常量及`EXACT_16Z_WINDOW`标签。原业务、seed44/04:00Z、80/800/8000、零think、会话TTL、一次性标记、失败处理与默认拒绝均保持；原16Z目录及新七片修复目录的Git差分为空，旧46测试未改。

新delivery SHA为`305c5a722ee94d1339b2400a292bbc83416e6c40ba3c0a4b7fc49efdcfd41352`。本岗重新计算七片完整raw/UI的长度和SHA，UI中base64解码恰等于完整raw，再解出各压缩payload，13运行文件加manifest共14件全部与准确Git原件逐字相同。最大raw11750字节，完整raw的base64加300为15968，完整UI加300为16090，均小于18000。此次没有重新执行旧68项或原安装回放；前次回放结论仍只属于其准确16Z版本。

部署profile SHA为`60660d2a10c6aba9de92bf843270e95ab2014292badc88d6579eac70224e3e66`；builder/helper/receiver逐字不变，GEN只变截止，resource只变截止及其GEN SHA。新GEN为`9edafbbff0586b5f77a701bd37f715685fba4169abaae510474343af75a8b427`，helper仍305f。静态核builder字符串没有deadline/stop绑定，因此同f7源码镜像身份不因新截止必须重建；本岗未读取实际云build binding，也没有实际确认镜像可用。准确d7的GitHub wrapper完整2567字节，base64加256为3680；下载后逐件校验再安装，无token/可变分支。新的汇总包不继承这项wrapper长度结论。

## 6. 本岗实际验证和原始问题

证据在 [778审核材料](../../tmp/778_reviewer_narrow_20261028/exact-audit.PUBLIC.json)。固定cloc2.10 SHA为`bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83`；本岗对f7和候选准确Git归档各65个应用源文件实际计数，结果**5898→5894，净减4、超上限794，规模仍不通过**。没有改统计脚本或分类；本岗没有另行运行`--require-range`，不能把owner的exit1写为本岗执行。

本岗执行原986中七个相关名称的参数化子集：**17 passed、106 deselected、0failure/error/skip，1条既有Starlette/httpx弃用warning，JUnit5.035秒，进程6.066秒，exit0**。使用SQLite与进程内TestClient，明确通过pytest配置覆盖把`pythonpath`指向本岗Git归档candidate/backend，执行前核两模块实际导入路径，避免worktree自身f7覆盖候选。原marker配置保持，未改原测试断言。与owner的17项是重复确认，不能相加为34个独立场景。

原owner43行为差分加1个错误顺序mutant辨别属于owner自测，不是本岗重跑，也不是原产品红转绿。本岗最初只读探索把旧部署路径放到不含该目录的backend commit，Git读取失败；首次AST审核器错误地把查询表达式helper按编辑语句helper处理，断言失败，仅修审核器分派后完整模块相等检查通过。首次HTTP导入探测主目录旧venv缺sqlalchemy，未开始测试，随后换用前次已批准的现有runtime venv，没有安装依赖。三项事实在attempts记录保留，不记为产品缺陷。审核脚本限定Ruff及diff检查通过。

## 7. 十项检查和未验证项

| 检查 | 本岗结论 |
| --- | --- |
| 准确源与变更范围 | 两个产品文件；工具分别绑定777/d7 |
| 需求和错误优先序 | helper展开后整模块AST相同 |
| HTTP/DDL/模块契约 | 无变更 |
| 权限、版本、资源归属 | 原调用顺序保持 |
| 事务、锁、审计和回滚 | 原语句保持；未测native锁 |
| 测试与证据真实性 | 原187断言保留；本岗17实际通过 |
| 规模 | 5894，仍超794，不通过 |
| 截止、一次性及角色预算 | 只静态核新窗口派生，旧原件保持 |
| 完整运输边界 | 7片字节链/16090及d7 wrapper3680核准 |
| CI、双机、独立验收与正式性能 | 本岗均未运行，保持未证明 |

未读取实际phase、budget、CA、运行角色、服务TTL、Linux停止回执或新grant；没有通过本审核发起HTTP或压力。完整CI、真实MySQL、真实HTTP socket、云资源链、独立F/P与学生本人研究正文不由本岗关闭。

## 8. 限定结论

这两个服务私有封装未见新增限定阻断，可作为root的单独集成候选；主干/发布仍需准确组合的原检查，不能借用f7 CI作为新候选CI。5894行不达标，未形成794行安全闭合方案。777/d7新20Z原件未见新增静态阻断，最多支持root预装和新环境预检；不构成prep/pressure/F/600秒授权。原16Z与旧运输失败结论不回写，不改独立用例，不冒称人工改码或学生研究报告。

GitHub限定讨论已发布并逐字回读匹配：[Issue12评论6473102439](https://github.com/HJY147/t44-dev-trace/issues/12#issuecomment-6473102439)，绑定技术提交`dfa980a20850e125d5d67279b12bcda5db2fce9f`，没有使用同账号自我APPROVE或发布整体通过状态。

行政收件文件首次暂存diff检查还发现两份生成镜像的额外末尾空行（exit2），仅规范生成文件末尾换行，API正文及原pytest输出未变；该检查失败也保留于attempts，不作产品缺陷。
