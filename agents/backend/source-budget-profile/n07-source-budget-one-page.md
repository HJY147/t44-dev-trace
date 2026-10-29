# N07：6307行的真实删重可行性（AI静态建议，未准入实施）

固定bc5应用；原cloc2.10记录source-count-strict-evidence-combination.json为6307、上限5100、缺1207。本文不重算/改变分母，未修改生产。对照M6-function-contracts.md及真实源码，**目前没有证据支持删去1207行；已实现净省0**。

| 可审候选 | 具体职责/边界 | 可量化证据与未证部分 |
|---|---|---|
| contracts.validator/_absolute_refs→公开evolve | 只替换重复引用树改写/构造，必须保留根解析、format、错误顺序/截断和独立实例 | 既有未应用C文本55→45 cloc，静态净-10；当前源hash相同。不是生产节省，待本轮有限样本也不能证明38HTTP全部等价。即便未来这10行全部落地也只是6297，仍超1197。 |
| ScanStore.start 与 EscalationFacade._run 的scan_runs初值组装 | 两处同14个key，dict分别scans.py:28–43、scheduling/facade.py:78–93；可提议一个受信行构造器 | 只能确认14字段组装职责重叠。调用者的run_id/规则输入、锁/重复冲突错误/重放返回不同，不能合并整事务；helper参数/调用/import仍需代码。未形成格式化/等价稿，**净省计0，不把32物理行全扣掉**；DB/调度owner应另审。 |
| NotificationFacade.list 与 common.page 的分页装配 | 原list里page/size、rows offset/limit、items/total重复；成员S锁、通知-id顺序、unread/unhandled额外COUNT必须保留 | 通用page已经存在，但默认顺序与通知不同，不能直接删查询/COUNT或吞并授权。未有保持SQL与错误顺序的候选文本，**净省计0**。应消息owner先给独立小稿/实际前后cloc，不事先承诺整文件95行可省。 |

**不算重复**：domain.decide的纯typed状态守卫与Workflow持久证据/CAS是不同层；API结构验证、history合法性复核与响应precommit各守不同入口；claim/auth多次实时查询守跨事务撤销，不能按文本相似删除；Runtime独立拒绝事务、outbox去重/故障恢复、migration/seed是已要求功能，不挪计量根外/转不计JSON。既有Call.create/common.model/page已经集中多数默认字段/序列化，未发现可直接再扣几百行的barrel或兼容层。

推荐：如实保持N07未达标，先完成质量/性能真实出口；只把C离线原型与上述两个小型重叠交各owner作后续可审设计，生产净省尚不承诺。不要为1207选择大架构重写，或压行/合并语句/去类型/守卫/审计/功能/修改3500–5100。若最终仍超限，按现资料向人报告；任务范围/老师要求的重大选择等人回来决定，AI不自动放行。

依据：[根选择材料](../../../docs/reviews/source-budget-decision-options.md)、[M6真实I/O](../../../docs/reports/M6-function-contracts.md)、[既有C静态预算](../runtime-plan-loc-budget.json)。本轮只读AST实际核出两处scan初始化14字段；不将毛重复片段冒充净节省。
