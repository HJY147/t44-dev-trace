# P17 escalation 启动输入聚合

仅使用已经认证的本轮启动inventory、P17 cohort时间及原产品冻结源码进行本地计算；未发送请求、未执行新候选，未读开发日志或报告。原400客户端/800任务未改动。

| 已认证启动输入事实 | 计数 |
|---|---:|
| escalation任务 | 400 |
| state=1/2/3/4/5 | 各80 |
| 配对event存在/缺失 | 400/0 |
| 当前任务schedule_version与event一致/不一致/缺失 | 400/0/0 |
| event.rule_version与inventory.rule_version一致/不一致/缺失 | 400/0/0 |
| task/project身份配对一致 | 各400 |
| event.level=3 | 400 |

配对event没有task-state字段，不能计算task/event的state相等性。

条件计算：从源bcec3326提取原 `select_window`、UTC解析函数和冻结规则资源，二者字节摘要均与认证source manifest匹配，未加载产品或执行任何IO服务。inventory与资源的rule_version均为1。以cohort时刻2026-10-31T11:09:54.477064Z及原始planned_end计算，400任务均落level3，均与配对event.level相同；在保持任务计划及冻结规则不变的条件下，24小时后仍400个level3，整个未来24小时内出现更高level的计数0，未升高400，缺资料而不能计算0。计算评估区间端点以及规则边界前后1微秒，使用原select_window选择逻辑。

限制：回收证据中没有单独认证的运行数据库规则全文；版本号一致不能证明其内容等同源码规则资源。因此未来24小时结论是冻结规则条件计算，不是实际未来运行保证。未来计划、规则变动及escalation接口行为未知；本轮没有跑到该接口。上述统计不构成性能、后置或业务接口验收，也不推断产品原因。

脱敏聚合及源摘要见同目录 `ESCALATION_INPUT_AGGREGATE.PUBLIC.json`，不发布任务ID、凭据或私有snapshot。
