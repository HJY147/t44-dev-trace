Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-FOUNDATIONS-v1
Reviewed-SHA: 4ae865b8dc554813c04aacbb3a5033aa2745c799

字段无关Engine/UoW/Core基础范围审核通过，未发现本阶段阻断。在本PR自有环境复验18项实际测试通过：SQLite真实commit/rollback/资源归还、先commit后丢确认保持CommitUncertain且数据仍在、close错误不遮蔽该语义、捕获SQL错误后rollback-only禁止部分提交、绑定值与标识符/列策略有实断言。

SQLite玩具表＋mock MySQL不等于真实MySQL连接/隔离/约束或项目DDL。借后端已安装t44的环境曾遮蔽本分支namespace导致收集失败，已定位并保留，切回本PR环境18项通过；整合后须在统一锁环境复核共同导入。无18表/业务仓储是授权范围，不硬判缺陷。Q002 pending，不发success/APPROVE/合并。报告将归档reports/reviews/foundations-v1.md。
