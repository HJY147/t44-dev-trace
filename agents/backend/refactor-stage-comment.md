Agent-Role: backend
Prompt-Ref: ROLE-backend-REFACTOR-v1

本轮仅后端重复消除：移除未用domain re-export/__all__，共享受信创建上下文/insert→get和opaque会话发行，typed命令、冻结API、稳定码、守卫、锁序/CAS/幂等/独立拒绝事务保持。相对003ef6b生产git物理diff净减112行，最终cloc及全产品3500–5100仍未达成结论。

729344e远端GHA39937742613真实失败：本岗namespace迁移导致模块commands被局部字典遮蔽，18 failed/299 passed及Ruff I001/F823；原始日志已保留。现改cmd别名保留原断言，正在以新checkpoint远端复验。本机正式性能安静窗内未跑pytest/build/MySQL/HTTP，不把历史测试/覆盖率当当前重构通过，不声明独立验收/性能通过。
