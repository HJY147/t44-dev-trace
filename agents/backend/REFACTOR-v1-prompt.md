# 实际派工 ROLE-backend-REFACTOR-v1

来源：总协调 /root 实际消息，原文：

ROLE-backend-REFACTOR-v1：恢复后端岗，基于根003ef6b（FE最终b485279稍后合）做真正的重复代码消除/未使用内部兼容清理，以满足3500–5100有效源码要求。5944经FE删83仍约5861，且DB C-P4校验修复会新增，因此不能承诺已过。先源码审查/编辑提出可实质减少的方案：未用domain barrel可转直接namespace导入并移除重复__all__；同构创建默认version/created/updated/context字段与持久行组装可统一受信helper；API/服务重复Schema/错误包/序列化/typed command结构可合理共享。不得压行、minify、转移业务到配置/改计数范围、删必需功能/安全/验证或降低断言。约束领域typed命令、锁序/CAS/幂等/独立拒绝事务、稳定码及冻结API保持。仅改你的backend API/domain/services/CLI和自己的测试，DB/messaging/scheduling改动先经root/owner约定。新测试若必要编号955起先报备，旧断言保持；审核957/959不改，独立验收私有资料禁止。当前正式性能窗口已开放（root10:10UTC通知，尚待测试岗开始回执），期间只编辑/审查/Git，不跑pytest/构建/MySQL或业务请求，等root明确结束再验证。尽早交真实小checkpoint，随后完整模块报告/handoff/prompt和PR16 Issue3交流。先回报保守可行减量与风险，不为数字改坏架构。

改进理由：通过真实重复消除保留完整业务与可读性，性能隔离期间不执行验证；新增测试先领号，私有验收隔离保持。
