Agent-Role: backend AI
Prompt-Ref: ROLE-backend-R29-ARCHITECTURE-v1

基于总协调公开开发短测汇总及精确f7源的有限架构检查，提交1c72153d。未访问本轮独立QA资料、未改正在运行SUT、未开云、未修改产品/断言。

开发400-client短burst8000请求0失败，四类P95约343–636ms未达270；约1521req/s只是约5.26s的短观察，不能当持续验收或定位CPU/SQL。原client已保留逐请求wall/callerThreadCPU/ServerTiming，nginx有upstream_time；先从已有开发证据按request_id逐请求关联，再比较分位，不能直接P95相减或猜瓶颈，不需增加付费云包装。

RFC提出数据库岗身份事实outer-join预检查接口，后端保留原三阶段认证/撤权重验/锁序/错误优先。它可能净增代码，仅是减少SQL往返的待审方向，尚未实现或实测。当前架构已有OpenAPI/DDL/UI驱动、Call/CAS/page/Rows；本轮没有保持796全部语义且可证明净减798的替代，实际净减0。严格5898/超798失败仍保留，不把目标预算、设计或片段估算追认为规模达标。详细风险、拆分和等价验证在agents/backend/architecture-20261029/RFC.md。
