# ROLE-frontend-PLAN-REASON-v1

总协调实际新阶段派工摘要：固定前端岗Issue28，从root3f59d88干净工作树建codex/frontend-plan-reason，读技术准入RFC/回执；后端尚未给完整候选，不准用旧API冒充新出口。范围是AuditEvent.after唯一合法reason的中文标题与原文纯文本，包括2000字/换行/HTML样式/日期和操作名，不走通用display。重复reason不任取；仅相关成功改期/明确7→2返工/项目迭代历史无可核对理由才提示，非计划/失败/残缺返工不猜。保留actor/time/evidence/beforeafter，不改冻结/API/session/R1/UI002。先设计提交、旧源真实红、新源必要组件/全前端一次；872等新后端/隔离环境后只新建本岗合成资源，记录真实写入/版本/身份。自己分阶段commit/push、Issue28/新draftPR及正文读回，精确专审/CI/隔离验收不冒称通过。

本岗执行提示：将“唯一理由值合法”和“哪类审计应显示缺失”分开判定；保留原数组，避免多条reason或状态条目用find()静默选第一条。用真实DOM textContent断言原文，HTML不执行、日期/操作名不改写；字段格式化仅对理由特殊处理。后端负责来源关联，前端不能凭当前计划或时间补写历史理由。

改进理由：先前静态协调发现“label已有reason”并不足以保证Diff中文/原文；用组件边界和准确后端版本证据验证实际呈现，不把新增字段猜测当实现。全部为AI岗位工作，不计学生人工修改。


实际后续协调提示摘要（本次已执行，不是用户原句）：root交付BE0549ea89、18089/PID12156/archive，允许读取0600合成账号供脚本内存登录，仅新建唯一[synthetic]项目/迭代/任务；旧18080仅限该新project一次真实changeTaskPlan用于legacy来源，再new18089读。禁止SQL造历史，缺失场景若不能自然形成仅组件；专用5176/cache，完成关自己Chrome/UI，新API根管理。执行872前先核冻结request/response schema和TaskMutation.task解码，避免UI002已发生的驱动字段/嵌套误解；源码hash绑定不能冒称进程鉴证。

产物对应：41776d0设计→c79cd99 auditReason/RecordView/983，22真实组件旧15红7绿→22绿，完整24新增+65原有=89绿；872仅新project42/iteration42/task6002，oldAPI真legacy1次+newUI2000字2次，六PNG/HTTP/版本/SHA保留。原红不删、不把开发绿变成独立验收；真实used prompt为本文件，本次仍为AI自动迭代而非学生亲写。
