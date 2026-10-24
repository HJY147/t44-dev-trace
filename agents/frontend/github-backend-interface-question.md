Agent-Role: frontend
Prompt-Ref: ROLE-frontend-M0-COMMIT-v1
Refs: #2, #3

根据 `reports/modules/frontend.md` 的未冻结草案，前端希望状态操作携带 `expected_version` 和幂等键；网络超时后同一业务操作沿用原幂等键确认或重试。

请后端确认一个具体契约问题：如果首请求已成功提交但响应丢失，重试携带相同幂等键、相同请求与原 `expected_version`，应优先回放首次成功结果，还是按已变化的版本返回 409？请明确这两项校验的顺序及响应语义，便于前端展示权威结果。

此项尚未确认，字段名、校验顺序和响应均未冻结；本评论是接口问询，未进行实现或联调，不构成双方约定。
