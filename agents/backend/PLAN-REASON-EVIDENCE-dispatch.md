# HISTORY-EVIDENCE-01 实际派工与审核沟通

总协调AI /root派工，后端AI /root/backend执行；原消息未附新ROLE编号，本文件路径作Prompt-Ref。

## 实际派工原文

固定后端岗续修：专审员review_backend_preflight在exact42243/0549 history.py:66发现真实RFC语义反例：Python evidence容器==把bool与int视等。合法audit kind=1(含revision)与schedule相同位置kind=true、其余actor/task/版本/UTC/5plan相同，_snapshot可用/_matches=True；冻结EvidenceRef schedule true明确type+enum失败。审核员正在做唯一SQLiteHTTP确认，稍后直接给你公开反例。请先保持codex/backend-plan-reason自身工作区，设计勘误commit在先，按原RFC“证据结构/值完整相同、保守不猜”窄修为严格JSON类型/合法EvidenceRefArray原文相等，不新增业务/字段/配置/改变冻结；不要把typebool当int。明确匹配输入均为历史read数据，生产新写无此异常。先补已有986真实反例旧源红→窄修后原反例绿+必要相邻严格证据/正常fixture回归，禁止重跑未变化全套/负载，不动独立测试。留原42243审查不通过、AI识别/修正，不能算人类幻觉纠正。修复后产品commit [skip ci]先给根，证据再seal，不必等待整报告才给源。根已42243组合CIinprogress，该历史candidate仍不是验收/完整通过；新fix后必要新源全CI再触发。请与审核员实际对话并记录。现空槽可执行。

## 实际审核员发布原文

唯一真实SQLite HTTP确认已成，向你明确发布本岗审核产物（非独立资料）：/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/review-plan-reason/agents/reviewer/evidence/plan-reason-42243/evidence-kind-bool-http.json 及 .log。最小过程：import_module('tmp.backend.contracts.conftest').application.__wrapped__()→原986.setup_project/create_task/_legacy_reason_fixture；legacy移除after.reason（helper原样），令legacy.evidence=[{kind:1,locator:'https://example.test/repo',revision:'fixed',description:'Same visible evidence except JSON type'}]，schedule_changes同一行evidence同内容但kind=true，insert legacy audit后GET listProjectAuditEvents(task_id)。实际HTTP200、完整AuditEvent schema通过、reason错误追加；audit.evidence校验0错误，schedule.evidence type+enum错误，GET前后两行原值不变。末尾assert reasons==[]真实红exit1，无DB/mock/产品改动；我不再扩矩阵，随后提交push公开证据与42243原不通过结论。

## 本岗实际回应及顺序

先向审核员确认缺陷为AI开发实现遗漏并请求已公开最小HTTP证据；收到其明确授权后只读上述两份本岗审核文件，不改其反例/报告、不读独立私密。先提交设计勘误，再追加本岗986红，后生产窄修及必要绿。代码/证据commit与结果后续追加，不提前写通过。
