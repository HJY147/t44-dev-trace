# D008 发布错误优先级 RFC（仅设计，未准入实现）

后端AI；从根14b57c66d69bf80759417e42af04432cea1ca795新分支codex/backend-release-error-priority-rfc，不混859分支。依据D008/U021：两条件均须满足，评估过期与原批准失效同时出现时，先更新评估，再重新批准。本稿不修改v1.1现行14冻结文件、应用、测试或DDL，不运行suite/SUT/CI。业务决定是用户真实选择，不是用户亲改代码。

## 唯一行为增量与函数I/O

`Workflow.transitionTask(g,c)`输入仍为原事务Gateway、已认证Call、已锁定任务row以及DELIVER/action7请求（expected_version、assessment_id/version、release_version、reason、evidence）。输出成功仍{task,decision}、原CAS/审计/outbox/幂等；失败仍原409结构，稳定错误码不新增。`g.get(release_assessments,id)`必须先按既有规则解析归属及请求assessment_version。

推荐最小实现候选：只在当前“批准引用不匹配”的失败槽内先判断该已解析assessment的`delivery_cycle == row.delivery_cycle && schedule_version == row.schedule_version`，失效选`ASSESSMENT_BASELINE_MISMATCH`，有效才选`RELEASE_APPROVAL_REQUIRED`。在决定批准缺失错误前计算基线有效性；批准引用本来匹配时继续走原domain，避免把新的无条件早期raise提升到原STATE/代码评审等错误之前。不是改查询、改锁或新增门面。可用一个基线布尔值与原require的错误选择完成，不缓存身份/证据，不提前commit，不改成功条件。

`domain.decide(ApproveDelivery)`当前已在有效ReleaseGate中要求reference及delivery/schedule一致，再检查预案批准；该领域函数及ReleaseGate I/O无需变更。原adapter→domain双层职责保留，不为提示顺序拆全状态机。实际净LOC尚未实现/未计，预期小于10行增量，不能报已节省或抵消6307超限。

## 现行真实guard顺序与拟改范围

| 顺序/函数 | 现行 | 本稿候选 |
| --- | --- | --- |
| Runtime.prepare / authenticate | 有效会话/主体/项目权限先于输入；结构校验后幂等识别 | 原顺序不变；旧COMPLETE结果重放先于新业务检查 |
| Runtime.locked_scope | 再实时认证，session→idem→必要project→有序members→有序tasks | 完全不变；DELIVER不新增project锁 |
| Call.task / Workflow | task存在且属该项目→任务expected_version相等 | 完全不变；最大version的原CAS检查位置不借本轮重排 |
| Workflow引用解析 | 原review归属/需要时review_version；assessment存在时先task归属 | 完全不变；跨任务评估仍RESOURCE_NOT_FOUND |
| action7且assessment存在 | 请求assessment_version == assessment.version | 不变，仍先于基线/批准；不把客户旧版本当新基线提示 |
| 批准引用失败槽 | task.approved_assessment_id/version不等请求评估→RELEASE_APPROVAL_REQUIRED | 在作此批准错误决定前，先看delivery/schedule；失效→BASELINE，有效→APPROVAL |
| 批准引用匹配后的domain | state5→经理角色→发布详情/证据→代码评审→release存在/reference/基线→预案批准/防自审/证据 | 原顺序不变，不扩大D008为所有错误的全局总序 |
| CAS及后续 | task version CAS、decision、成功audit/outbox/COMPLETE同事务；拒绝退出后新事务audit | 完全不变；所有D008拒绝都不发布、不改version/decision/批准 |

重要区别：session/项目“认证授权”实际在Runtime前；action的经理角色/状态检查当前在domain，晚于adapter的批准引用失败槽。不能把现行源码描述成“所有角色/状态一定已先检查”。上表保留原槽位，只调整用户明确选择的两失败关系，不在本轮搬动这些晚期guard。

## 新旧结果表（fresh key；已通过既有前置检查）

| 评估/请求/批准状态 | 原行为 | 新候选 | 是否变更 |
| --- | --- | --- | --- |
| 任务expected_version错误 | VERSION_CONFLICT | 同 | 否 |
| 存在但跨任务assessment | RESOURCE_NOT_FOUND | 同 | 否 |
| assessment_version请求不匹配 | ASSESSMENT_BASELINE_MISMATCH | 同，原检查先执行 | 否 |
| delivery或schedule过期，批准引用也失效 | RELEASE_APPROVAL_REQUIRED | ASSESSMENT_BASELINE_MISMATCH | **D008唯一目标差异** |
| 基线有效，批准引用失效/未批准 | RELEASE_APPROVAL_REQUIRED | 同 | 否 |
| 基线过期，批准引用仍匹配 | 继续原domain：通常BASELINE，若更早state/role/代码评审guard失败则先原错误 | 同 | 否 |
| 基线/引用/证据与其它门禁均有效 | 发布成功200 | 同 | 否 |
| 请求id不存在的assessment | 不创建ReleaseGate，继续原domain缺评估/更早guard路径 | 同；不凭None造BASELINE/新404 | 否 |
| 其它action（含回滚8/返工9） | 既有版本/预案/状态守卫 | 同 | 否 |
| 已COMPLETE且当前认证/输入/摘要检查允许的同键重放 | 已保存的业务data或error/code/status及原audit_id | 保留这些保存值，不重跑D008/不新增业务或audit；HTTP动态字段另见下节 | 否 |

### 重放保证的准确范围（R2，按当前源码校核）

依据`Runtime._claim/complete/rejection/execute`与`api.endpoint.handle`实际路径，而非把协调者复述当实现证据：

- 成功写在原主事务保存data、response_status、完成请求的response_request_id并COMPLETE；成功审计及业务outbox仍同事务。拒绝仅在**call已持有claim、被锁行status=1且owner_token匹配、error.status<500（现有Rejected为4xx）、独立拒绝audit及完成快照事务成功提交**时，才由rejection调用complete保存error（移除当次request_id）及response_status。不是全部4xx都必然可重放。
- 5xx、没有claim、owner不匹配、status不是1、拒绝audit/提交失败不属于上述COMPLETE保证。未知commit也不能据客户端503断言“没完成/已回滚”；同键重试须读取实际持久状态，沿原恢复规则处理。
- `_claim`发现已COMPLETE时，仍先经过当前认证/项目权限、既有输入校验与同摘要检查；随后返回保存的业务data或error/code/status和原audit_id，不再执行业务/D008或新建审计。成功data中的audit_id（若该操作有该字段）和错误payload.audit_id沿原保存值，原audit不可变。
- **不保证整个HTTP响应逐字节相同。** 成功每次由HTTP层新建外层meta：当前request_id、`now()`生成的server_time、当前运行contract_version（新规冻结/实施后为1.2.0），replayed=true，original_request_id取已保存的response_request_id（实际完成结果的请求，不保证最早claim请求）。非重放原样沿现有false/null语义。
- 4xx重放由execute用保存error重新合入**本次request_id**，保留原audit_id/code/其它保存错误字段及status；HTTP错误响应没有外层Meta，也不新增original_request_id或contract_version字段。成功/错误的X-Request-ID、Idempotency-Replayed和Server-Timing等响应头按本次请求构造。因此D008不借版本演进重写旧快照/审计，也不声称旧完整响应字节原样返回。

本R2仅修RFC文字，未修改上述源码/冻结/测试或运行suite/SUT/CI；旧F08记录和原设计提交保留。根已技术采用最小scope及1.2.0；晚期state/role不再另问用户、不搬guard，仍交限定设计审核核对。

经理恢复步骤：提交当前基线的新评估→由合规的另一审核人评审预案/批准→经理以当前任务/评估版本重新发布。两条件仍都必需，不复用旧批准；“经理重新批准”是用户流程表述，不撤销现行评估创建者不可自审的约束。

## 规格与wire版本建议（待协调冻结）

建议新业务规格/契约**1.2.0**，父为现行1.1.0；不将用户新选行为伪装为1.1补丁或回写旧freeze。沿用项目1.0→1.1显式行为演进方式，非宣称外部标准强制该版本号。HTTP路径仍/api/v1、31paths/38ops/130schemas，既有409两错误码/稳定DB ID/所有字段和18表226列不变。由于运行`contracts.VERSION`直接取info.version，权威/运行两副本`info.version`和`Meta.contract_version.const`必须同为1.2.0，外层meta明确新规版本；客户端须同步权威源。`ContractValidationResult.schema_version.const`保持**1.0.0**：candidate结构未变，不能全局替换模板/规则/包版本。

冻结前需同步的准确范围（本阶段均不改）：

- 总协调：`AGENTS.md`、`specs/requirements.md`、`specs/business-rules.md`显式D008增量；新`records/spec-freezes/v1.2.json`父指向原v1.1，旧v1.json/v1.1.json绝不回填。把本RFC列新review/freeze输入。
- 后端：`specs/contracts/openapi.json`及逐字运行副本`backend/t44/contracts/openapi.json`：上述元数据/版本状态、transitionTask.description、该操作x-error-cases中两个409触发条件的相对优先；不改错误enum/response codes/输入输出结构。`specs/contracts/README.md`和`specs/backend-design.md`追加D008与本顺序表，原v1.1历史保留。
- 数据库：无需DDL/迁移/字段或稳定错误ID变化。若新冻结集合继续纳入`specs/database/field-dictionary.md`/`persistence-contract.md`，owner仅追加新版本引用/拒绝审计原语义澄清；不能让旧1.1段落历史文本被全局替换。根决定无语义差异时可复用其原hash，而不是为版本号强改。
- 前端owner：`frontend/README.md`当前1.1说明需显式1.2；`tmp/frontend/981_fixtures.ts`/`982_client.test.ts`当前未找到硬编码1.1，仍须核对动态SPEC版本断言。候选结构schema1.0不改，表单/API字段无需发明新版本字段；若要改中文处理引导另由前端设计，不阻本错误码契约。
- 冻结后实现仅`backend/t44/services/workflow.py`此失败槽及已授权回归文件；包版本、domain命令、锁文件、MQ/扫描/DDL/池均无本轮需求。新测试需root给号或复用原986/985；859不改不重跑。

## 新回归与原历史

待新规格冻结/正式实施派工后：用原HTTP fixture真实开发/评审/预案审批/改期形成同task、请求评估version仍匹配、但schedule stale且task批准引用清空，旧源记录原APPROVAL，新源应BASELINE（409、失败新事务audit、task/version/decision/outbox无业务变更）；另delivery_cycle stale的合成受控历史边界应独立说明，不能set_state冒真实完整流程。基线有效未批准仍APPROVAL；重建评估+不同合规审核人重新批准→发布成功。并发/真实MySQL只按后续授权，不提前宣称。

保留邻接：请求assessment_version不匹配、任务expected错误、无会话/跨项目、跨任务/不存在assessment、旧同键重放、新键再检查、其它action、引用匹配但代码评审/状态失败顺序。全量准确源/前端版本/Schema校验与独立复验由后续分阶段安排，不把纯RFC当测试。原F08失败、未执行尾部及旧source/规格/Word/ZIP原件保留；新D008不能倒写其预期或把原FAIL取消。独立资料不读取/不联系tester。

## 需要明确的边界（不擅猜）

1. D008只选“基线过期与旧批准失效”的两失败关系。对晚期domain的错误state/非经理角色/失效代码评审与该双失效同时出现，用户未给全局顺序。推荐保留现adapter槽位（即双失效仍BASELINE），不新增全局角色/状态前置；需总协调和限定审核确认这一技术范围。若要求角色/状态等提前，是额外可观察行为，须另列规则，不混成本提示修订。
2. 不存在assessment的原路径未明确为新的404；本稿保持旧行为，不因D008擅补。除非审核指出冻结另有强制依据，否则不向用户追加选择。
3. 新wire元数据1.2.0使旧严格1.1客户端须随权威源同步，这是显式版本演进代价。版本命名/freeze集合由协调者技术决定；若另选编号须两副本/Meta一致，内层1.0 const不动。

本阶段未发现需要费用/机器的动作；11/28截止和“先报价再考虑”是规划/费用边界，不作为预算授权或新架构许可。
