# ROLE-backend-CONTRACT-v2 实际派工

来源：总协调本轮实际任务；以下为原文，不是用户提示词优化版，也不算用户亲自修改代码。

> ROLE-backend-CONTRACT-v2：专职审核717cd65不通过，真实报告 reports/reviews/design-v1-717cd65ef73560fde7ff5bca2821c9fe2b20d68a.md 已由reviewer本人提交0e0a10b739c9b14e9ee42c8e8f70b16da24cba6e。请只修设计中你负责的C2/C3/C4，避免扩展：C2不截断经理，不新增人数上限；recipient_ids去掉max100，handled_count允许INT UNSIGNED范围，所有事件/计数的嵌套响应/例值一并一致。C3共享UtcTime统一MySQL DATETIME(6)支持1000～9999年、UTC Z最多6位；真实FormatChecker+负向0001/0999和边界1000/9999验证，跨字段/只读contract validation同域；扫描算法用now-end差值避免9999+24h溢出，通知scheduler。C4逐操作删除GET/只读验证幂等x-business-error-codes，对齐response允许codes/HTTP及真实可触发依据；/dictionaries无项目范围、无资源ID不能列PROJECT_ACCESS_DENIED/RESOURCE_NOT_FOUND。增一个真正检查注解/response一致且GET不含幂等错误的设计校验，不制造假业务HTTP通过。
>
> C1由database下一轮加response_request_id持久字段并约束COMPLETE非空，保存“实际生成已保存结果的请求ID”（可在owner恢复后最终完成时定格，不一定首次租约认领请求）；你先在README/backend-design明确采用该字段构造重放meta，不存整个旧meta/凭据。可发database消息让其后续对齐，数据库现在未运行。
>
> 当前根分支codex/team-bootstrap，索引已被reviewer明确释放，现专归你；只显式提交本岗契约/设计/自检/日志/handoff/本次实际prompt与Issue正文，不能加root gate-probe文件或他岗文件。原失败报告与日志不改写，另留修复真实验证结果。Issue#3/#12实际答复要点用body-file。commit footer Agent-Role backend、Prompt-Ref ROLE-backend-CONTRACT-v2、Refs #3 #12 #13。只commit不push/checkout/merge，不宣称冻结或产品通过。完成回完整SHA、各C修复证据、尚未执行和释放索引；下一轮直接编码。

实际产物映射：三份既有后端规格的定向修订；本岗可重复运行设计检查、修复前/后日志、Issue答复正文，以及本岗日志/报告/handoff。没有修改原审核报告、v1原始日志、数据库DDL或产品实现。
