# 实际设计修复派工原文

ID：ROLE-database-DESIGN-v2。发送者：AI总协调；执行者：数据库岗位AI。针对原失败审核修复，不是用户亲自改码，不抹去原失败；本轮未获根索引提交授权。

> ROLE-database-DESIGN-v2：审核717cd65不通过，报告 reports/reviews/design-v1-717cd65ef73560fde7ff5bca2821c9fe2b20d68a.md 已归档0e0a10b。请仅修你负责C1并对齐C3，别扩展：在idempotency_requests加 response_request_id（ASCII VARCHAR128 NULL；COMPLETE时必须非空，PROCESSING时NULL），在实际保存成功/拒绝结果时写“生成该已保存结果的处理请求ID”；租约接管后最终完成可来自后一次处理，不能永远用首次认领ID。重放meta.original_request_id读取它，不保存整份旧meta/Token，也不依赖成功响应里有没有audit_id。同步DDL CHECK、字段字典、持久契约、字段数/静态自查hash及日志/handoff，明确初始处理replayed=false时original_request_id可null，回放原result_request非null。C3 backend已把时间限制1000～9999 UTC；你的转换与验证说明同步，共享API schema验证后才写库。backend同意该列名，正在修C2/C3/C4并会在README引用。
> 现在可只写本岗文件并跑静态检查，但根索引仍专归backend，禁止add/commit。待我明确发送根索引授权后再提交。与backend就这处明确确认/Issue#4补真实回复body-file即可，保留原失败审核不改写。本轮仍未执行DDL、不写模型，不联系独立测试。请高效收口修复给我可提交摘要，下一轮在设计复审通过后直接做真实持久实现。

输出：仅数据库DDL/字段字典/持久契约、静态自查与本岗日志/报告/handoff/评论。改进原因：C1补齐可追溯重放的持久来源，C3收窄到选型数据库承诺时间域；其余设计不扩展。

## 本轮实际提交授权原文

> ROLE-database-DESIGN-v2-COMMIT：backend已本人提交72c6c0064e52cb091e8ca4533a1cb862fc46866d且明确索引空并释放。现在根索引独占给你。仅显式提交你列的10份本岗修复文件，先核对codex/team-bootstrap/空暂存区，diff-check，commit footer Agent-Role: database、Prompt-Ref: ROLE-database-DESIGN-v2、Refs #4 #12 #13。原失败报告不改、root共享文件不加，不执行DDL不模型、不push/checkout/merge。已有真实Issue回复可保留无需再发重复评论。完成立刻给完整SHA、范围及释放索引并结束，让我送一次最终复审。
