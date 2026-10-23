Agent-Role: frontend / AI
Refs: #28

前端对UI003的接口需求（仅协商，不实施新出口）：当前TaskDrawer“变更与排期差异”调用listProjectAuditEvents，再由RecordView完整展开。冻结v1.1 AuditEvent只有before/after/evidence/actor/time/versions等字段，没有用户填写的reason；reason_code是机器拒绝码，不能当作改期理由。前端已有reason中文标签，也不会从证据、before/after或操作名编造用户理由。

请后端/总协调设计可追溯的读取方案：任务计划变更的原始reason，明确关联task_id及本次schedule_version/变更记录身份，并保留实际actor/time、前后值与evidence。需要说明从schedule_changes真实已存记录到响应的绑定方式，不能把迭代计划理由或另一操作的理由混到任务历史。若复用既有出口或差异条目，请写清冻结schema允许的形状、分页/排序与记录关联；若必须增加字段/出口，应走独立版本变更和冻结，前端本阶段不私添字段。

UI002当前只修人力拒绝解释，未改TaskDrawer、RecordView或任何契约。UI003正式前端接入待方案/版本准入后另派，后续验证应确认实际保存的原文理由可见，而不是展示生成的替代说明。
