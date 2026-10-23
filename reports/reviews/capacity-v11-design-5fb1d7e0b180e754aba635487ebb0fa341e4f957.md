# 容量生命周期 v1.1 限定技术设计审查

## 1. 审核对象与基线

- Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-CAPACITY-V11-DESIGN-v1；Issue #12 / PR #21。
- 被审准确提交：`5fb1d7e0b180e754aba635487ebb0fa341e4f957`，提案 `specs/changes/capacity-lifecycle-v1.1.md`。本岗独立分支 `codex/review-capacity-v11`。这是审查提案的提交，不是 PR 当前最新 head。
- 父规格：`ae60dc37fdaefecaca33e734a354add6ba9ebe29` 的冻结 1.0.0，`records/spec-freezes/v1.json`。32 份输入均逐字节对照 `git show`，11 份原冻结文件的当前/历史/manifest 摘要全部相同。详本岗 `evidence/capacity-v11-design/static-audit.json`。
- 范围仅本次容量生命周期的业务解释、四个操作、错误、锁序、幂等及 1.1.0 演进。没有审核后续新源码，没有修改产品、原冻结 11 件、DDL或测试断言，没有运行重负载。未联系独立测试或读取其内部资料。

## 2. 用户需求与技术解释映射

U015 原话为“要求先补全人力安排：李四登记工时后才能接任务；张三的未结项任务转走后才能移除（推荐）”。D005 与 Q-capacity-lifecycle 的真实答复记录为 `answered_adopted`，不是仍待采用。它没有逐字定义七状态的“未结项”集合。

| 需求/边界 | 被审依据与实现入口 | 设计判定 |
| --- | --- | --- |
| 先登记接手人工时再接任务 | RFC:7、16；Tasks:121–127 | 方向成立；保留现有 developer 校验，再以任务所属迭代 capacity 校验目标 owner |
| 新计划保留全部未结项 owner | RFC:7、17；Projects:145–152 | 必须全量查询本项目、本迭代全部受保护任务，不仅检查 old capacity 减 new capacity 的删除名单；已不一致的存量活动任务也不能漏过 |
| 开发后禁止转派 | D002:5–9；Tasks.prestart:22–25、assignment:124 | 保持；只允许状态1，或状态3且 blocked_from_state=1，不因补 capacity 新开转派出口 |
| 返工不能绕过人力有效性 | RFC:18；Workflow:190–227；domain/state_machine:193–213 | 7→2 前重新查原 owner 有效 developer 与当前迭代 capacity；原经理、版本、依赖、证据与新计划仍必需 |
| 不引入总预算/自动分配 | RFC:7、20 | 保持单人有效 capacity 引用；不比较 available_hours 与任务汇总，也不引入自动平衡 |
| “未结项”状态集合 | RFC:9、31；Projects:99–105 | 存在真实提案误述，见 D-C1；状态7容量口径另待用户真实答复 |

CapacityEntry 现有 available_hours 为 >0、≤100000、0.25 倍数；沿用该结构，不把“登记”解释为零工时占位，也不新增预算算法。

## 3. 变更与责任边界

backend 负责 Tasks/Projects/Workflow/Runtime 及运行契约；权威契约与版本由总协调串行派发责任岗；frontend 使用权威契约源。数据库层仍为既有项目行锁、RowsGateway、CAS 和 UoW，无新增表列、索引或迁移。项目成员移除/角色变更规则不随这次 capacity 规则隐式放宽。

现有代码未包含新提案的 assignment/rework capacity 守卫，changeIteration 也尚未全量保护 owner；这是本轮计划实现的差异，不作为“提案之前必须已有实现”的缺陷。原 v1 与其历史验收不能追溯宣称已有新规则。

## 4. 契约、错误与版本兼容

1. 全局 CAPACITY_REFERENCE_INVALID 及持久错误 ID30 保持，HTTP422保持。assignment 当前只有 OWNER_NOT_PROJECT_DEVELOPER 等原分支，transitionTask 当前没有 capacity 分支；两者须同时补 `x-business-error-codes`、`x-error-cases` 的具体触发条件、422 响应描述/枚举，不能仅有全局错误枚举。createTask 保留 IAT02；changeIteration 既有此码但需扩展到全量 owner 保护。现有缺失是真实父版本事实，不代表未执行的 v1.1 已实现。
2. assignment 原目标不是有效 developer 继续用 OWNER_NOT_PROJECT_DEVELOPER；通过该校验但不在当前迭代 capacity 用 CAPACITY_REFERENCE_INVALID。rework 按提案“人力无效”合并用 CAPACITY_REFERENCE_INVALID，避免直接调用返回 OWNER_NOT_PROJECT_DEVELOPER 的 helper 后漏声明。保持原授权/状态/版本/证据分支，新增守卫须在任何 CAS、cycle、decision、diff 写入前完成；不要让无权角色先获得容量信息。多重失败的优先顺序需由后端在契约触发依据和回归中写清。
3. 正式信息版本应升 **1.1.0**，URL 仍 `/api/v1`。具体同步清单：`specs/contracts/openapi.json` 的 `info.version` 与 `Meta.properties.contract_version.const` 一起改为1.1.0；`backend/t44/contracts/openapi.json` 与权威文件字节一致；`t44.contracts.VERSION` 从运行副本读取，API:239 与 validateContractPayload:124 随之返回1.1.0。不能只改 info 而被 Meta.const 拒绝。
4. frontend/src/contract.ts:1 直接导入 `../../specs/contracts/openapi.json`，无额外 FE JSON 副本；用相同新源重新构建，核对展示/元数据/错误处理与通知重放现有流程。包自身0.1.0、字典业务版本1不等于契约1.0.0，不为凑同步机械改其语义。
5. 新冻结清单须单独记录 version=1.1.0、父版本1.0.0、原 manifest/父冻结完整提交、真实新提交/各文件摘要、D005及后续状态7答复、变更范围与兼容说明。原 `records/spec-freezes/v1.json` 及11hash不改，旧文件通过父提交恢复。被审时11件仍原样，尚未执行新冻结。只有取得用户状态7答复并修正文稿、完成源/副本同步后，才有正式冻结输入。
6. 无 DDL 变更，无需借本次迁移改变历史 owner/状态/幂等记录。已不一致的数据在新 changeIteration 全量检查中暴露；不能悄悄删除历史任务或自动换 owner。

## 5. 状态、锁序、幂等与事务

**并发方向可行。** Runtime:18–27 当前项目锁集合已有 createTask/changeIteration/成员变更；Runtime:195–200 已对 rework 取项目锁，assignment 当前不在集合。将 assignment 加入该集合，应发生在现有 `locked_scope` 的成员/任务锁之前，不能在 Tasks 已锁任务后补取项目锁。

统一顺序为 session → 本请求幂等行 → project FOR UPDATE → membership 按 user_id → task 按 id → 相关记录。changeIteration 的全量 owner 查询以 project_id+iteration_id+受保护状态为条件，锁任务按 id；项目锁在检查与迭代 CAS/差异写入至提交期间持有。其他三个入口同取项目锁，容量移除与创建/转派/返工因此串行：先移除则后来的激活/转派拒绝，先激活/转派则后来的移除拒绝。既有迭代行锁可保留；不要另开容量检查事务或在检查后提前释放锁。此为静态可实现性论证，不是 MySQL 竞争测试。

rework 应在原状态、经理、版本、依赖、新计划/证据校验均满足且准备写入前，查**当前**原负责人及**任务当前所属**迭代 capacity，不能使用客户端传入 owner、旧审计或旧计划 capacity。失败不得推进 task.version/delivery_cycle/review_cycle/schedule_version，不插 decision/diff/outbox 成功事件；拒绝审计仍依 Runtime:75–97 回滚后独立完成。

Runtime:237–245 在业务 dispatch 前回放已完成结果。新守卫不能放入 authorize/结构校验而阻断旧成功快照重放；已保存确定性拒绝也按原键回放，补工时后发新逻辑请求需新 key，不清空既有幂等行。成功状态、审计、outbox与快照仍同事务；不确定提交仍沿原 key 恢复。当前设计不要求把重放快照冒充当前有效状态，调用方仍 GET 最新任务。

## 6. 已执行检查与限制

- 已执行 `git status --short`、`git diff --cached --name-status`（本岗索引为空），从准确5fb1d7e建立独立worktree；静态读取 AGENTS、协议、U015/D005/QA、D001/D002、相关冻结规范及32份实现/契约输入。
- Python 标准库进行 `git show` 字节/hash绑定、11项当前与 ae60dc3 历史摘要核验、JSON 契约/版本/available_hours 提取及 AST 成员保护状态/项目锁集合提取，退出0；结果见 `agents/reviewer/evidence/capacity-v11-design/static-audit.json`。这不是产品测试或真实并发复验。
- `gh pr view 21` 实读 draft，当前远端 head 为 `102f2c9fc06b1bbf9dc7c7c19ea9d354f8e56773`；本报告只绑定已给5fb1d7e，不错当最新实现审核。
- 首次猜测 D002 文件名及 frontend/src/config.ts 不存在，相关读取退出1/2；已定位实际 D002-prestart-edit-boundaries.md、frontend/src/contract.ts，重新读取，不把失败命令记通过。
- 未运行 HTTP/MySQL/DDL/前端构建/单元或集成用例/性能/独立验收/CI刷新；新功能没有此类通过证据。没有读取任何独立测试资料。GitHub COMMENT 命令与实际返回另存本岗回执；未发 reviewer/stage 状态。

## 7. 问题与十项判定

**D-C1（设计澄清阻断）：RFC:9 错称沿用现有成员使用保护，实际包括状态7。** `Projects._change_member` 的状态查询明确列 PENDING/DEVELOPING/BLOCKED/PENDING_REVIEW/PENDING_RELEASE/**ROLLED_BACK**。若把提案当统一保护口径，可误将成员删除/降角色的状态7守卫一起放开。根因是 root 的 AI 提案概括错误，本岗 AI 静态发现；不是用户/学生识别或亲改代码。

收到总协调后续真实消息：其已接受事实更正，要求现有成员保护1–5+7不变；另已向用户具体询问“已回滚尚未返工能否移出迭代工时；推荐允许但返工前补回”，该**新增边界待真实答复**。本岗不以原 U015 泛称“未结项”替用户选择，也不把新待答倒写为 D005 整项未采用。待答及 root 后续追加 D005/RFC 不属于本报告5fb快照已审内容，不声称已核对那些新文件。

其余明确准入条件为第4/5节具体清单：全量 owner 子集检查、assignment 项目锁、rework 当前有效人力、原拒绝/重放、1.1元数据/源副本/父链同步。总协调已在真实后续消息中采纳这些**技术设计建议**，不冒称人类逐项审定。未发现需要增加 DDL、放宽D002或引入总预算算法的理由。

| # | 清单 | 本轮判定与证据 |
| --- | --- | --- |
| 1 | 身份与版本 | 通过：reviewer审他岗提案；32输入绑定5fb；独立树 |
| 2 | 需求与范围 | 有条件：U015采用属实；D-C1与状态7具体解释未决 |
| 3 | 接口兼容 | 有条件：复用ID30/422方向成立；两新增操作声明与第4节同步待实施 |
| 4 | 数据库兼容 | 通过（设计）：不变DDL/字段；11原hash一致，不代表新功能已执行 |
| 5 | 状态机 | 有条件：D002与7→2原出口保持；capacity状态7待人答 |
| 6 | 权限与范围 | 通过（设计）：同项目developer/经理与服务器权威owner，禁止跨项目泄露；运行未验证 |
| 7 | 事务与并发 | 通过（设计方向）：项目锁前置及全量检查可实现；真实MySQL竞争未验证 |
| 8 | 幂等与故障 | 通过（设计方向）：保留已有快照重放/拒绝/不确定提交；新实现未验证 |
| 9 | 测试证据 | 通过（真实性边界）：仅静态/hash/JSON/AST，不冒记产品测试 |
| 10 | 门禁与合并 | 未验证/不放行：本轮不刷新产品checks，不发布success，不合并 |

## 8. 结论与后续准入

**除状态7具体容量口径外，给限定技术设计有条件准入建议；当前不能正式冻结1.1.0或放行依赖7解释的实现。** 需先保留 root 提案错误/本岗 AI 发现纠正的真实链，修正“沿用成员保护”的措辞，取得新增具体问题的人类答复，提供修正后的精确提交。不能由技术审核替人选择容量7口径。

责任岗实施时落实第4/5节清单。后续提供权威/运行副本一致的新版本冻结、源代码精确SHA及成功/拒绝/幂等/容量竞争/存量不一致与返工回归证据，再分别审源和测试。已有全产品失败门禁和旧审核历史保持；本轮无APPROVE、无reviewer success、无main合并。
