# HISTORY-EVIDENCE-01：先归档的窄修设计勘误

设计阶段；未应用产品/回归。当前本岗HEAD5b96f29，产品0549；root组合42243的专审结论不通过，原结论/反例不得覆盖。识别者AI审核岗review_backend_preflight，修正者后端AI，不记学生识别/改码。

## 真实反例和来源

审核岗明确公开了本岗审核（不是独立资料）：`.agent-worktrees/review-plan-reason/agents/reviewer/evidence/plan-reason-42243/evidence-kind-bool-http.json`及`.log`。实际SQLite+TestClient+原986 helper/真实RowsGateway，无gateway/matcher mock；合法audit.evidence.kind=1且revision齐全，schedule同位置kind=true，其余字段一致，GET200/schema通过而错误追加reason。原断言exit1；两行GET后未变，不能因此说匹配正确。问题在历史read候选JSON，正常新写先受冻结Schema校验，并无此输入异常。

`history._matches`当前只用Python列表/字典`==`；Python会把True与1视为相等。原RFC“证据结构与值完整相同、保守不猜”没有授权这种放宽。本次实现遗漏，不是新业务或新冻结规则。

## 未应用的最小修法

在原比较位置（原project/task/version/actor/time/plan等守卫保持）依次：

1. 两侧分别调用现有`violations(SCHEMAS['EvidenceRefs'], value)`。复用冻结EvidenceRefs/EvidenceRef约束，保留数组1..30、字段/类型/枚举/仓库固定revision等。非法任一侧不投影，不新错误码，不把损坏schedule候选当合法证据。
2. 两侧合法后，用`json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)`逐字比较。比较的是已解码JSON结构和值：对象键顺序无关、数组顺序有关；字符串原文包括空白/Unicode不正规化，不转数字/布尔，不删可选null字段。`1`与`true`不同；`1`与`1.0`虽均可满足JSON Schema integer，在旧历史比对也保守不当同一生产字形（新请求仍按原normalization接受/归一1.0，完全不改输入语义）。两侧都是合法同字形1.0仍可相同，不声称恢复原JSON原始字节/重复键，数据库只提供解码对象。
3. 没有identity cache/新增事务/SQL/写入，匹配失败只保留原audit响应，缺失仍由前端原范围提示；有合法既存reason仍优先、不查候选。不能把非法audit自身变合法或伪造reason；原响应校验与错误路径不改。

预计只增加json import和比较位置数行；最终按实际源码差异记录，不承诺源码减量。14冻结/runtime/DB/outbox/幂等/锁/DDL/正常写入口不改，不重复未变化全套/负载。

## 准入后开发红绿计划

root已明确授权本窄修，仍先提交本文档：原986增加真实SQLite HTTP、实际JSON列的合成历史，无matcher/gateway mock。保留原例：合法audit.kind1、schedule.kindtrue，其余原API产生字段相同，GET200合法AuditEvent但应无reason，修前实红。相邻覆盖kind1.0与1保守差异、合法精确、对象键换序、原文改变、数组换序；对每案核对证据Schema结果、响应契约、两行读前后不变。至少一个原正常legacy HTTP用例相邻回归。

先旧源红，后窄代码绿，原红/审核不通过不改写。产品checkpoint [skip ci]先通知root，不等纯证据归档；随后证据seal。组合新源CI/专审/独立复验由root继续，修复不等于完整通过。
