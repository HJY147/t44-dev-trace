# 容量生命周期1.1冻结前契约一致性复审

## 1. 对象与基线

Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-CAPACITY-V11-FREEZE-CHECK-v1；Issue #12 / PR #21。准确被审提交 **59daa2c6caecbe2f5fe968630dd8eca2fa70fd8e**。与已审bbc RFC、D005/D006、原1.0.0历史及首次9aeb报告差异核对；首次失败报告保留。此结论只覆盖本次规格/契约冻结源，不覆盖尚未提交的业务守卫草稿或产品运行。

本岗独立codex/review-capacity-v11工作树先合入a787、9aeb，最终fast-forward59daa；读取内容以提交git-show/hash绑定，不触root索引或owner工作树。

## 2. 需求映射

已采用D005/D006落实到AGENTS、requirements、business-rules、backend-design、API README、OpenAPI及DB字典/持久契约：迭代capacity保护状态1–5，状态6/7可移出；7返工前补回有效项目developer与当前迭代工时；项目成员/开发角色保护仍1–5+7；D002不解锁开发后转派。

createTask保持原capacity守卫；assignment在原允许状态/有效developer后核同迭代capacity；changeIteration核本项目/本迭代全部状态1–5 owner（包括旧名单不变但已有不一致的情况）；rework保留原授权/状态/版本/证据/依赖后、CAS前重验人力。不增DDL/预算算法/状态出口。用户逐字采用与AI事实纠错链保留，不归为学生识别/亲改。

## 3. 本次纠正与责任

首次9aeb两份assignment description错误地用“有效developer且已登记，否则CAPACITY”合并原错误，F-C1由reviewer AI发现、root派BE owner修。owner aa748d1与集成59daa在两份契约只精修同一description（各9406行），明确：无效developer→422 OWNER_NOT_PROJECT_DEVELOPER；有效但缺当前迭代capacity→422 CAPACITY_REFERENCE_INVALID。原业务错误、响应与触发条件未因修正文案改变。F-C1限定关闭，原报告/错误原句与修复diff均保留。

开发公开995静态脚本只有两行变化：打印真实路径、fixture.contract_version从0.1.0-draft改为SPEC.info.version。没有修改原101收件人/UINT32断言。此版本化fixture问题在当前新schema出现，不否定早期不同源/时间的设计结果。

## 4. 接口/数据库/历史一致性

两份权威/运行契约字节一致，SHA256均 **a77a5cd635b8f6a9927b60f9befac017055442504e34a95b40eddda809e2782f**。静态核对31路径/38操作/130schema，路径/operationId集合不变；info.version与Meta.contract_version.const均1.1.0；只Meta schema的该const改变；全局错误码枚举保持；top及38ops元数据frozen-v1.1。

assignment/transition新增CAPACITY_REFERENCE_INVALID，三处business-error-codes/x-error-cases/422响应一致；createTask/changeIteration只扩展原capacity条件；所有原错误case无删除、非capacity条件不改、相对顺序保持。129项结构检查不能代替运行时错误优先级实测，但本次文档声明不再互相冲突。

DDL原件/打包副本/父版本字节相同：18表226列。DB文档明确capacity跨行不变量由服务同UoW核对，不靠新触发器/CHECK。原records/spec-freezes/v1.json字节不改，11历史摘要均从ae60dc37fdaefecaca33e734a354add6ba9ebe29可恢复；当前有意演进文件不能虚称仍等于旧hash。

**59daa提交内尚无records/spec-freezes/v1.1.json。** 本报告准入其语义源供总协调随后生成独立manifest，不能把frozen-v1.1文字当成manifest已生成/已核对，也不把后续并行freeze变化当本轮已审。新清单需记录父1.0.0、完整源SHA/各摘要、D005/D006与实际差异。

## 5. 锁序、错误与幂等

各增量规格一致：session/idem→project FOR UPDATE→user_id有序members→id有序tasks；assignment在成员/task锁前加入项目锁，capacity/owner获锁后重读，changeIteration核完整owner集合，与创建/转派/返工同项目串行；不另开提前提交事务。原普通路径不事后补project锁。

requirements流程图明确仅表示准入条件，不规定/改变既有错误优先级；BE/README/DB文档均保留原守卫。rework新增人力校验在原合法性守卫后、写入前；assignment有效developer错误先于新增capacity错误。旧完成快照先重放，失败不增业务版本/轮次/decision/diff，独立拒绝审计与未知提交原key恢复不变。目标人容量移除与激活竞争须安全拒绝一方；合法A→B后移除A允许依次成功。以上是契约/原理一致性，非并发执行证明。

## 6. 实际执行与原件

本岗实际：独立树git rev-parse/status/fast-forward、限定git diff/cat/git show，标准库静态脚本分别对9aeb及59daa运行，均退出0、129结构项通过，18份输入hash保存。初查人工语义失败与静态结构通过可以同时成立，未以计数绿色忽略F-C1。

- `agents/reviewer/evidence/capacity-v11-freeze/static_check.py`：仅JSON/hash/git show，不导入产品或测试。
- `static-9aeb40c.json`、`static-59daa2c.json`：各自准确源/计数/hash，原结果保留。
- `correction-diff-and-owner-evidence.json`：修复diff、公开owner脚本/log hash与出处。

本岗读取已提交owner before/after日志：1130设计checks/38ops，从2fail exit1→0fail exit0；该命令由backend执行，不冒记本岗运行或产品HTTP测试。未启动服务/DB/测试、未运行OpenAPI依赖校验/产品单元集成/性能/CI/独立验收；无独立内部资料接触。原2空格DDL提取误计在首次报告如实留，正式脚本按4空格确认18/226。

## 7. 十项判定

| # | 检查 | 本轮结论 |
| --- | --- | --- |
| 1 | 身份/版本 | 通过：18输入绑定59daa，固定reviewer审他岗规格 |
| 2 | 需求/范围 | 通过：D005/D006及bbc映射，成员与capacity边界分开 |
| 3 | 接口兼容 | 通过（静态）：F-C1关闭，新增分支/Meta/副本声明一致 |
| 4 | DB兼容 | 通过（静态）：18/226、DDL不变，父v1历史可恢复 |
| 5 | 状态机 | 通过（契约）：1–5保护、6/7释放、7返工再验，原D002不放宽 |
| 6 | 权限/数据 | 通过（契约）：原有效developer/项目范围保持 |
| 7 | 事务/并发 | 通过（契约）：project前置及同UoW全量owner，不是实测 |
| 8 | 幂等/故障 | 通过（契约）：原快照、拒绝审计、未知提交恢复保持 |
| 9 | 证据真实性 | 通过：本岗129静态/owner1130设计/产品测试严格分开 |
| 10 | 冻结/产品gate | 仅语义源准入；manifest待生成/核对，产品gate另审不放行 |

## 8. 限定结论

**59daa2c6caecbe2f5fe968630dd8eca2fa70fd8e 的本次冻结源未发现剩余语义阻断；F-C1限定关闭，可由总协调生成独立1.1.0冻结清单。** 原1.0清单/摘要和首次失败报告保留。

本结论不等于新manifest已存在/已审、业务实现完成或总体验收。新业务源码及真实回归按后续精确SHA另审；本轮未发reviewer/stage状态、未APPROVE、未合main，不改变旧e01失败。
