Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-DESIGN-v1
PR #13 head: 717cd65ef73560fde7ff5bca2821c9fe2b20d68a

首次契约/DDL设计审查：不通过，保留本版失败证据，修复后按新SHA另审。

四项设计阻断：
1. P1：幂等快照明确不保存旧meta，表中也无原请求ID/原审计关联；部分成功data无audit_id，重启后Meta.original_request_id的持久来源不明确。
2. P1：升级要求owner＋所有active经理，但模型没有人数上限，响应recipient_ids/handled_count仅允许100；101收件人的合法事件无法表达，不能截断漏通知。
3. P2：UtcTime允许0001年且完整TaskCreate通过真实Schema校验，所选MySQL DATETIME承诺支持域从1000年起；需统一时间域和422语义，未执行数据库插入。
4. P2：12个GET及只读契约校验仍标幂等冲突，GET响应却没有409；无项目参数的dictionaries仍声明PROJECT_ACCESS_DENIED等无触发定义分支。

报告：reports/reviews/design-v1-717cd65ef73560fde7ff5bca2821c9fe2b20d68a.md，含八段、十项及18表逐表判定。提交中12文件与已审内容哈希相同，OpenAPI规范校验通过、18表字典/FK静态匹配；这些不能覆盖上述语义矛盾。

未执行HTTP、DDL、产品测试、覆盖率、MQ/事务故障或性能；缺少运行结果本身不是本轮缺陷依据。不审核自己的M0，不自我APPROVE，不发成功、不合并。经总协调追加授权，核对远端HEAD后对本SHA发布reviewer/stage=failure；执行回执另存本岗证据。
