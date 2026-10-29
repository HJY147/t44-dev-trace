# 实际派工（总协调AI原文）

> R2设计已891d67679288b10a958be105688cd22cd686cf38限定审核通过，root已实际merge RFC+review到integration；doc merge三冲突保留859/RFC两历史，记录records/validation/D008-RFC-merge-resolution.json，root干净。现准入**spec草稿同步阶段**，自有新codex分支从root最新：仅修改 specs/backend-design.md、specs/contracts/openapi.json、specs/contracts/README.md、backend/t44/contracts/openapi.json 以及自己的role记录/prompt。按准确D008/RFC R2设1.2.0 info+success Meta.const，两OpenAPI逐字同；candidate_schema1.0保持；transitionTask描述/x-error-cases明确最小原批准引用失败槽优先，别扩大到所有state/role/其它action全局顺序；4xx缓存/动态envelope按R2。原1.1历史段落保留，显式1.2草稿待freeze。root自己同步AGENTS/requirements/businessrules并负责新v1.2manifest，不改DB/DDL。可以执行纯Schema/设计1130验证及新旧结构白名单diff(31/38/130/错误enum稳定、仅两const/info/说明变化)，**不可改workflow或测试、不可跑应用suite/SUT/CI/服务/负载**；未冻结不实施。8min内提交draft SHA/各文件hash/验证真实结果和未核项，用户原选择不记亲改。自己日志/module/handoff/实际prompt/GitHubIssue3全GET/push。若旧检查因版本实际错误先核需求并记录，不降断言。

作者后端AI；归档ID ROLE-backend-RELEASE-PRIORITY-SPEC-DRAFT-v1为AI本地标识。
