# 容量生命周期 v1.1 设计差异复审

## 1. 对象与基线

Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-CAPACITY-V11-DESIGN-v1；Issue #12 / PR #21。准确被审提交为 **02ecdea9ced90cd46cbca898f123d6409f45ba80**。本岗仍在独立 codex/review-capacity-v11 工作树，直接读取 `git show 02ecdea:文件`；没有用5fb工作树旧提案冒充新提交，也没有merge/check out其他岗位分支。

旧5fb首次报告 `capacity-v11-design-5fb1d7e0b180e754aba635487ebb0fa341e4f957.md` 保留发现与当时待答历史；本报告更新结论，不覆盖旧稿。范围仍仅这次容量生命周期技术设计，不是产品实现审核。

## 2. 真实需求与解释

U015/D005已采用“先登记工时接任务、有未结项任务先处理再移出”。用户随后对具体问题真实答复 U016：“允许移除；以后决定返工时，必须先补回有效的人力安排（推荐）”。D006与Q-rolled-back-capacity.json记录 answered_adopted；现在**无此业务边界待答**。

新RFC:9明确：迭代 capacity 保护状态1–5，6/7可移出；7→2返工前补回有效人力。项目成员/开发角色保护仍是1–5+7，二者分别约束，D002开发后不可转派不变。D005/RFC原“沿用成员保护1–5”是 root AI 的提案错误，由 reviewer AI 静态发现并由 root纠正；不归为用户/学生识别或亲改。人的U016选择与AI事实纠错分开留痕。

## 3. 差异与职责

5fb→02仅五件变更：D005、RFC更正，新增U016/D006/对应问答；35份审核输入的新提交摘要已保存。Task/Projects/Workflow/Runtime等实现输入与旧审逐项hash不变，因此旧报告的代码路径/锁序论证仍适用；本轮没有引入或审核未提交实现。

四入口范围不扩大：createTask保留capacity引用；assignment只对允许转派状态增加当前迭代接手人守卫；changeIteration全量保护本迭代状态1–5 owner；action9 rework激活前重验原owner有效developer与当前capacity。无新增DDL、预算算法、状态出口或开发后转派权限。

## 4. 契约与版本

新RFC:20已明确正式1.1.0的 `info.version` 与 `Meta.contract_version.const` 同步；权威 `specs/contracts/openapi.json`、后端运行副本 `backend/t44/contracts/openapi.json`/元数据/说明同步，FE直接导入权威源并核对fixture/版本断言。新manifest记录父版本/原freeze历史与差异，原1.0.0的11hash仍保持，本轮复算全部相符。

CAPACITY_REFERENCE_INVALID维持ID30/HTTP422；assignment/rework须补逐操作business-error-codes、x-error-cases和422响应声明，changeIteration扩展其触发描述。assignment有效developer失败仍保留原OWNER_NOT_PROJECT_DEVELOPER；rework按RFC人力无效归CAPACITY_REFERENCE_INVALID，不能误引未声明分支。最终精确声明和实现顺序由责任岗在源码/契约复审兑现。

## 5. 正确性与并发

assignment应加入Runtime项目锁集合，在membership/task锁前取project。createTask/changeIteration/rework已有项目锁路径，可复用session→idem→project→有序成员→有序任务顺序，容量检查与CAS在同一UoW内完成；不另开检查事务。对changeIteration查询本项目/本迭代所有状态1–5任务owner，对新capacity作完整子集检查，包括旧版本已不一致的任务，不能只查本次删除的人。

rework仍须原经理、状态7、版本、新计划/证据、依赖守卫全部成立，在写task/cycle/decision/diff前查当前有效人力；6/7移出capacity合法不等于允许无capacity直接7→2。成功审计/outbox/快照同事务，失败不推进业务版本且独立留拒绝审计；同键已完成结果（成功或确定性拒绝）仍先回放，不受新guard重新执行影响。未知提交仍原key恢复。上述是可实现设计，没有运行MySQL竞争证明。

## 6. 实际证据与限制

`git show --stat`、`git diff --name-status 5fb 02`及Python标准库读取新五件全文/JSON，重新对35输入在02提交计算SHA256，断言所有实现输入未改且11原freezehash一致，退出0。U016/D006/QA真实已读；证据为 `agents/reviewer/evidence/capacity-v11-design/static-audit-02ecdea.json`，首次32输入的原静态JSON/AST结果原样保留。

无产品源码变更、HTTP/前端构建、单元/集成/真实MySQL/性能/独立验收/CI刷新；没有接触独立内部资料。未改原11冻结件、DDL、root索引或owner测试。本轮Github仅COMMENT，不发reviewer/stage状态、不APPROVE、不合并。

## 7. 发现收口与十项判定

D-C1在02限定关闭：事实混同已改正；状态7容量边界由真实U016/D006补足，人的决定与AI纠错明确分离。未发现本次技术设计仍需阻断准入的确定矛盾；不把尚未实现/运行本身判作设计缺陷。

| # | 检查 | 本轮结论 |
| --- | --- | --- |
| 1 | 身份/版本 | 通过：35输入绑定02，独立reviewer审他岗设计 |
| 2 | 需求/范围 | 通过：D005/D006真实采用，1–5/6–7与成员边界分开 |
| 3 | 接口 | 通过（设计）：既有ID30/422扩展，明确两操作新增声明；待实际契约复审 |
| 4 | DB兼容 | 通过（设计）：无DDL/字段变更，11原freeze保留 |
| 5 | 状态机 | 通过（设计）：D002不变，7→2新增有效人力守卫，无新出口 |
| 6 | 权限/数据 | 通过（设计）：服务器本项目owner/迭代，不放宽成员保护 |
| 7 | 事务/并发 | 通过（设计）：project前置/全量owner检查同UoW；运行未验证 |
| 8 | 幂等/故障 | 通过（设计）：保留原快照、拒绝审计和不确定提交语义；运行未验证 |
| 9 | 证据真实 | 通过：仅静态/hash/JSON/AST，未造产品/独立结果 |
| 10 | 产品门禁/合并 | 本轮不适用且不放行：设计准入不能替代源码、测试、最终gate |

## 8. 限定结论

**02ecdea9ced90cd46cbca898f123d6409f45ba80 的容量生命周期提案可准入责任岗实施；D-C1已限定关闭，无该业务边界待答。** 这是明确范围内的技术设计结论，不是1.1契约已冻结、代码已完成、产品checks通过或整体验收。

下一输入为责任岗实际改动的权威/运行契约、1.1新manifest父链、完整源码SHA，以及成功/拒绝/旧键重放/全量存量owner/容量移除与assignment-create-rework竞争/7移出后返工拒绝与补回成功的真实回归。最终源和测试另审；历史失败不覆盖，不发整体success，不merge main。
