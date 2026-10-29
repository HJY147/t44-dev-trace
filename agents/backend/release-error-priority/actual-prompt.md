# 本次实际派工（总协调AI原文）

> 用户已实际选D008：当上线评估相对当前任务基线过期且经理旧批准失效时，先要求更新评估，再重新批准；按11/28截止，费用先报价未授权。root已commit/push records/decisions/D008-release-error-priority-adopted.md + records/prompts/U021原文。请新的自有codex分支从root最新开展设计阶段（别混859branch）：先读D008/已有守卫源和v1.1freeze，写 specs/changes/release-error-priority-rfc.md、具体变更的函数I/O/guard顺序表/不变项/原F08历史保持/新回归计划/规格版本与wire版本选择依据。**本阶段只RFC，不改任何冻结文件/应用/测试，不运行suite/SUT/CI**；给新规需同步的准确文件/版本范围，优先选择最小、可审、版本一致路线，别为了一个提示顺序改全架构。鉴权/资源归属/expected_version/请求assessment_version的前置优先不变，评估delivery_cycle/schedule_version失效应在批准引用检查前；missing/跨任务评估及其他action别覆盖。需说明新旧表哪些情形输出改变、必须人确认的尚有歧义（不要自猜，先推进清楚部分）。8min内RFC commitpush给root，随后由reviewer限定设计审/root冻后再实施。859已完成记录先不重跑。实际rolelog/module/handoff/prompt/GitHubIssue3全GET，不代人改码证据。

本岗归档ID ROLE-backend-RELEASE-ERROR-PRIORITY-RFC-v1（AI本地标识，非用户原话）。业务选择者用户；记录设计者后端AI，尚无改码/验证行为。
