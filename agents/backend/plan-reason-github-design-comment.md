Agent-Role: backend / AI
Prompt-Ref: agents/backend/PLAN-REASON-DESIGN-dispatch.md
Refs: #28

本轮仅设计，基于已集成A的982623381e9cfa1d6a7bad1de222e160503cbf08，新分支codex/backend-plan-reason。RFC：specs/changes/plan-history-reason-projection-rfc.md；合成新/旧例：agents/backend/plan-reason-design-examples.json。没有产品/测试/配置/14冻结修改，也没有HTTP、MySQL、全量CI或负载。

拟复用现AuditEvent.after的{field:"reason",value:用户原文}，不加字段/端点/版本。新schedule_diff在原成功事务存reason到audit，与schedule_changes/CAS/outbox/幂等原子；失败或重放不新增/重复。旧task历史只在已授权project+task、from/to schedule_version、task version/expected_version、human actor、精确微秒time、完整五项before/after plan和evidence全匹配且唯一时只读投影；缺失/歧义不猜，不改immutable audit。无请求外键，明确保守恢复范围，不承诺任意导入/伪造历史的请求级因果。

changeIteration只改自身，不批改任务；旧iteration audit缺iteration_id/完整快照，不能唯一反推或向任务散发理由。非计划/拒绝audit不参与；after已有理由不覆盖，满50不丢原字段，理由≤2000字符不截断。保留原分页排序/total，每页≤100，先读该页再一次固定精确pair批读，无N+1/无IN交叉乘积+随意limit。

DB需求是RowsGateway.task_schedule_changes(project_id,≤100个(task_id,to_version))：去重、空集0SQL、固定参数化tuple/OR、完整解码rows、稳定排序、唯一键保证≤distinct pairs，越界/重复/SQL异常显式原持久错误。现通用rows只有AND/单列IN，不由后端绕过gateway写SQL；待总协调恢复DB岗确认/实现，旧/database消息工具失败并未送达。

前端6373333383指出的两个真实问题均保留：field标题与通用value格式化。后续frontend owner需标题“原因与决定依据”+原文纯文本；相关成功计划历史缺失/歧义时显示“此历史记录未提供可核对的变更理由”，不泛化全部audit，也不把reason_code当理由。范围/长文/重复理由规则在RFC。

离线8个AuditEvent样例形状通过、14hash一致/31paths38ops；没有实现matcher，这不等于关联正确、DB/HTTP/UI通过。净LOC只有待实现估算，本轮产品delta0；修复预计增加而非减少源码，原6108超5100问题未解。等待总协调设计准入及DB接口交付，才做原986/985有意义红绿/真库/精确CI；不读独立私密、不接触独立岗。
