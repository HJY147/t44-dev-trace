# PR21 完整产品审核 v1

## 1. 对象、基线与身份

Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-PRODUCT-v1。被审完整SHA：`e01f5dcf9d8ef5a88161fcbc87ab142fba74cdef`，PR21 mainbase `1996d44425e09930b5ba3ae5391b728980241f55`。结论：**不通过，不能放行该SHA**。C-P1/C-P2/C-P4为已复现缺陷，C-P3为真实规模超限。首次checkpoint及原失败输出保留，后续owner修复不会抹去e01失败。

独立树`.agent-worktrees/review-product-v1`/`codex/review-product-v1`；与开发责任岗分离，非独立验收岗。基线为原始T44/课堂两份提交材料、冻结1.0.0、D001/D003/D004及本岗八段十项协议；冻结清单11文件逐一git-show SHA-256全部相符。当前全部产品含scheduler/messaging/前后端/数据库/部署和M2文档在范围内。未读取私有独立用例/日志或联系testing。未改owner实现/既有断言/root索引。

本报告仅审e01；发布时PR已演进至其他head，不能把该失败或后续部分修复误套为新head通过。先前四基础限定审核已由09dd3cf独立归档，结论不扩作完整产品。

## 2. 需求与验收映射

| FR/AC | 所核实现与证据 | 本轮判断 |
| --- | --- | --- |
| FR01/AC01 | api.py:63–125、175–238统一参数/Schema/响应；contracts加载冻结规范；Business38操作；公开985/986与38操作实测记录 | 服务端结构校验、稳定码有真实路径；客户端Iteration偏离导致C-P1；未以行覆盖率证明所有operation×错误分支逐条完成 |
| FR02/AC02 | 冻结DDL/字典、persistence/schema.py与migrations.py；18表226列迁移和负向约束公开证据 | 字段定义与冻结一致；C-P4导致已应用库语义漂移检查不足 |
| FR03/AC03 | Reviews.createTaskReview、review_complete；八段/模板版本、有效清单、证据和非owner守卫 | 静态与已发布用例支持；无法验证证据内容真实性或Git真实作者，不把seed合成评审当真人评审 |
| FR04/AC04 | Tasks.prestart/check_graph、Runtime.locked_scope、Projects.schedule_diff、changeTaskPlan | 同项目/自边/环/前驱/版本/差异路径存在；前端迭代计划消费有C-P1 |
| FR05/AC05 | Workflow:75–157、204–249，Reviews评估审核；domain当前轮次/排期/预案守卫 | 交付、回滚、返工证据链可追；产品记录决定，不执行外部生产回滚 |
| FR06/AC05/06 | domain.decide、Call.cas、Runtime与UoW；真MySQL竞争/独立拒绝/不确定提交公开证据 | 七态/九动作及阻塞原态、非owner禁止代推等有依据；C-P2影响当前状态告知 |
| FR07/AC07 | Scanner/ScanStore、EscalationFacade、OutboxStore/Pika/DeliveryWorker | 最高级/同排期同级一次、事务计数、完整收件人、晚到去重、续扫有真实实现及公开模块证据 |
| FR08/AC09 | 组合根DI、固定锁/工作流、脚本拒空/skip/漏源；五必需主干上下文实读 | 真实门禁存在；e01审核失败/规模不达标，不能因别的SHA CI绿放行 |

正式400并发稳态10分钟/P95≤270ms/吞吐≥1000及独立验收仍无本轮完成结论。AI留痕、学生本人研究成品等提交物的真实性与未完成项按公开资料保留，不编造人工改码十二条或个人观点。

## 3. 责任边界、结构与M2文档

跨模块由api组合根装配Runtime/Business、UoW工厂和通知/升级门面；domain不建连接，MQ网络等待在DB事务之外，API四worker不各启动扫描器。会话/幂等/项目/成员/任务/子记录有显式锁序；普通任务写不事后补project锁。稳定41审计码、状态/动作/角色映射显式定义，未依赖Enum枚举顺序。seed旧规则字段、默认通知门面与故障注入等历史失败/修复原件保留。

M2七个Mermaid已以固定11.12.0 bundle及真实Chrome156.0.8078.47逐个成功渲染，源块hash、SVG/PNG及尺寸在`evidence/product-v1/diagrams/`。本岗目视样查成功/拒绝事务图，未作最终DOCX逐页或打印字号验收。语义核对提交给root的三项文档修正：

- design-report.md:90把每个outbox都画成必需Task，DDL:373及Runtime.outbox允许项目级事件task_id=NULL，应画可选关联。
- :171“死锁/超时有限重试完整事务”须区分实际Runtime转503后调用方原key重试；scanner内至多三次只处理版本/排期竞争。
- :208用run.cutoff分档与实现不同：ScanStore.page以cutoff筛候选，Scanner._execute:85/Facade.create:126以每次当前clock判档；文档须分别写清。

root已明确接收并安排修正文档；SRS服务身份通知scope表述已由root先发现并派修，不重复作新发现。这些不改变冻结规格，新的文档提交不在本报告冒充已复审。

## 4. 接口与数据库兼容缺陷

**C-P1 [P2，frontend] 真实Iteration.plan被当成顶层字段。** forms.ts:15按record顶层组成计划，FieldEditor.vue:17用i.name显示迭代。冻结Iteration只包含plan对象；959用契约形状记录得到`{expected_version:3,plan:{}}`，原名称、计划时间、容量、缓冲、延期预案全部丢预填，实际迭代选项也无名称。`tmp/frontend/981_fixtures.ts:10`的扁平夹具偏离冻结响应，983只检查表单存在而掩盖缺陷。首次checkpoint误标夹具第12行，此处校正为第10行；原提交保留。应消费record.plan/i.plan.name，夹具须受冻结响应Schema校验。

**C-P4 [P2，database] 迁移结构检查只比名称，漏语义漂移。** migrations.py:57–77以名称集合检查index/unique/FK/CHECK，未比列序、unique属性、FK列/目标或CHECK表达式；已应用路径:127–133依赖其passed返回结构相符。957在隔离Inspector替身保留全部表/列类型/default/约束名称，却改变索引列/unique、FK目标及CHECK为1=1，仍返回`passed=true, defects=[]`，正确拒绝断言失败。**本轮没有改动真实MySQL，也不声称实库已经漂移。** 应逐个比较冻结结构语义，处理反射的等价规范化，再加实际负例；不可改冻结DDL或删除原断言来绕过。

18表DDL仍是此前设计审核的相同冻结内容，schema生成与包内DDL hash一致；本轮实库迁移/恢复证据来自已发布owner记录。它们不消除C-P4的漂移检测盲区。

## 5. 业务、事务、故障与减量

成功路径Runtime:240–264将任务/子记录/成功审计/outbox/幂等COMPLETE及最终response_request_id同事务；claim先于Workflow版本检查。rejection:69–101在失败主UoW退出后独立落拒绝/错误快照；审计不可用503不伪称已入库。UoW不确定commit不被cleanup rollback冒充确定未提交；RowsGateway SQL错误标rollback-only，savepoint回滚局部唯一冲突再回读。SQL值参数化，表列/排序限制受信注册表。

身份先于请求体与重放；成员逐请求、写事务内重核，服务主体仅允许scope内createEscalation。普通用户只访问参与项目，通知还要求本人收件人；口令Argon2id、session只存摘要、API/CLI撤销锁与日志脱敏有实际路径。没有据此宣称未执行威胁模型或所有越权分支通过。

评审非owner且当前对象/轮次，评估创建者不能自审；改期清当前预案批准，返工清旧批准并推进轮次/排期。依赖图项目锁/排序任务锁及DFS拒环；成功CAS和拒绝审计分别有真实MySQL记录。outbox租约owner fencing、publish mandatory/confirm、DB消费后ACK、同event锁补缺失通知、终态fallback和confirmed缺通知恢复互相配合；同事件晚到不会重置read/handled或二次提醒。APScheduler独立进程、共享flock、持久游标只在确定结果后推进。

**C-P2 [P2，frontend] 历史重放状态被宣称为当前状态。** OperationForm.vue:37–40先await saved刷新，随后仍用原result.data.task.state写“任务现为…最新记录已刷新”。959明确mock幂等原结果state2/v2而权威刷新state6/v9，最终提示仍为“任务现为开发中（同一操作结果已确认），最新记录已刷新”。这不改服务端数据，但错误确认当前进展，违反D001重放快照边界；须用权威GET结果或只说明原操作已确认。

**C-P3 [P1，集成协调] 有效代码5944行，超过5100上限844。** 使用原source_count.py/政策/固定cloc2.10、指定提交归档，require-range真实退出1。下列是owner可选的真实减量方向和估计，未实施、未承诺全可叠加或足够达标：

| owner/位置 | 依据和可做动作 | 估计有效行 |
| --- | --- | --- |
| FE/styles.css | root83条候选的33个自有类词在当前全部TS/Vue均无引用；清旧connection/records-table/shortcut/context等规则，保留动态类和第三方类并做1440/390回归 | 83–95 |
| backend/domain与scheduler内部导出 | 生产从子模块导入，domain/__init__58行和scheduling/__init__21行旧barrel仅基础测试用；确认内部API后移除无生产消费者的重复出口，测试机械改import但保留全部断言；state_machine/workflow可用模块namespace去重长符号清单 | 合计约100–145，需确认内部兼容 |
| DB/seed.py | 400行中重复project/task/version/created/updated基字段、task/pointer同组None；抽受信行构造器/共享初值并保留全分布、manifest、幂等与15000记录 | 60–100 |
| scheduler/rules.py与ScanStore | rule_version/code/recipient_roles旧兼容属性当前只有991基础断言用，生产用label/recipient_kinds；recoverable未被tick调用而另写查询，可删除或统一受信过滤门面，保留hash过滤和恢复语义 | 约15–25 |
| API/rules/公共工具 | 两份_unique_object、common.now与utc_now等同类基础工具可收口；状态命令公共state/role/evidence守卫前置须保持错误优先级与证据断言 | 约15–35 |

保守总量约270–400行，仍与844有缺口，且C-P4修复可能增行。不能把这些候选当成已经减量；禁止minify、移动seed/业务函数到排除目录或配置规避统计、改分母、删功能/安全守卫/必要证据。继续由owner提出可读、可测的结构精简并以原脚本复算。

## 6. 实际执行、公开证据与限制

| 类型 | 实际结果与来源 | 严格边界 |
| --- | --- | --- |
| 本岗959 | Vitest5.0.5/happy-dom真实加载目标Vue/TS，2项正确行为断言失败；log/command与脚本已归档 | 明确mock成功响应，不是live浏览器/API或独立验收 |
| 本岗957 | 真实check_schema调用，Inspector替身baseline及语义变化都passed；拒绝期望断言失败 | 不是真MySQL漂移/DDL实验 |
| 本岗规模 | 原脚本固定cloc2.10，5944、range=false、exit1 | 不改政策/源代码；报告绑定e01而非证据自身提交 |
| 本岗资料/图 | 冻结11hash匹配；全部输入git-show/工作树相同；7图实际渲染成功 | 不是业务测试/最终Word排版验收 |
| 托管CI原件 | 265d89b run39931640641的gzip JUnit摘要hash/原XML复核：整套317pass/0fail/0error/0skip，Python2399/2724=88.07%，FE308/334=92.21% | e01 backend/frontend/其用例/product工作流未变；static/config两文件增加凭据守卫，不能谎称全CI源码零diff；覆盖率不证明夹具正确 |
| Docker原件 | 31f4dff run39932723829 passed；4API worker、凭据rotation、共享flock拒第二扫描、停写备份/隔离恢复19表行数及EXTENDED checksum相同 | owner托管synthetic2项目40任务，非本岗新跑/性能/独立验收；到e01仅ops plan提示和README变化，不能将恢复CHECK通过消除C-P4 |
| 当前门禁实读 | main strict五上下文reviewer/stage/static/contracts/coverage/frontend，管理员也受约束；e01 run39935050279 static/frontend success，contracts/coverage cancelled，原status pending且空 | 尚无该SHA全部必需成功；本岗最终只发绑定e01的failure，不自我APPROVE或合并 |

初始PR Review因root尚未push本地e01而422（当时remote86dfd7d），读回无重复；root推入PR祖先后绑定原e01 COMMENT成功。Git原始Vitest log EOF空行导致资料diff检查失败，原始输出保留，命令级仅豁免blank-at-eof；没有降低产品门禁。公开证据核对曾误设全CI零diff断言，发现static/validate_config真实变化后修正分类，未声称错误检查通过。基础旧测试没有重跑，完整既有CI结果没有冒记为本岗执行。

完整证据目录`agents/reviewer/evidence/product-v1/`；实际prompt及续派在dispatches/ROLE-reviewer-PRODUCT-v1.txt。性能、独立验收、最终人工经历/学生成稿未核对为完成；未等待这些才提出实质代码缺陷。

## 7. 十项门禁判定

| 项 | 判定及证据 |
| --- | --- |
| 1 身份与版本 | 通过：独立tree、指定e01和冻结11hash、目标manifest；不自审产品 |
| 2 需求与范围 | 不通过：C-P3超限；全产品/M2均纳入，无基础旧范围排除 |
| 3 接口兼容 | 不通过：C-P1真实Iteration嵌套消费差异，原fixture不受Schema约束 |
| 4 数据兼容 | 不通过：C-P4漏约束/索引语义；18表定义冻结与已跑迁移另记 |
| 5 状态机 | 领域/服务端已查路径与公开测试支持；C-P2当前状态告知错误，不能作全流程通过 |
| 6 权限/秘密 | 已查实现及公开记录范围通过；未声称全部安全分支或生产威胁模型已验收 |
| 7 事务/并发 | 已查原子/拒绝/锁/CAS与公开MySQL证据范围支持；本岗未重跑实库全矩阵 |
| 8 幂等/故障 | 不通过：C-P2前端误读重放；服务端、MQ和扫描证据按明确范围支持 |
| 9 测试真实性 | 失败真实保留、公开原件可绑定；C-P1夹具形状错误说明覆盖绿不能替代契约质量；正式性能/独立未完成 |
| 10 门禁/合并 | 不通过：本岗failure、代码规模超限、e01两产品job取消；不得合入主干 |

## 8. 结论与复审条件

**e01不通过；C-P1/C-P2/C-P4修复、原政策规模达标及新SHA必需门禁收口前不得发success或合并。** 本岗将failure只绑定本次已审完整SHA，链接公开缺陷评论；不把对旧祖先的failure当成最新PR head已审，也不替root执行合并。

修复由原owner实施，959/957原断言保持；拿新完整SHA及明确差异复审受影响项，原e01报告/初失败输出不覆盖。性能/独立验收及最终学生提交项继续分别留真实证据，不以技术设计、CI或本报告代替。后续完整SHA的新发现不倒填本轮；报告不嵌自身证据提交SHA以避免自引用。
