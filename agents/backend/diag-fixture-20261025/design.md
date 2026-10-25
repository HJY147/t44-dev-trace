# Source935 新诊断 P：准备器与短窗驱动设计

操作者：AI 后端岗位。仅开发诊断，非独立验收。父协调本轮明确授权全新
`t44c_r9diag935_p`；禁止旧库、13306、任意 runtime/private 读取。

最小两步：先用已封 b767 观测模块及原 Settings/T44_DIAG_* 启动 API；该模块不读
sessionpacket。然后根在 app 容器执行 801_prepare，load 机器执行 801_http。

准备器输入是根显式提供的 private accounts 路径（manager/developer/reviewer 各含
username/password/user_id）、新输出目录、原 TLS URL/CA、精确数据库 host/port/user
和原产品 DSN 环境。必须先逐字段校验新库声明，拒 root/13306，再建 engine。
从真实数据库读 seed marker、40 projects、成员/产能/任务/依赖，不猜 ID。原 CLI
service-token 为实际项目全集发令牌；三角色通过真实 TLS 登录，核 user_id 和成员。
选每个客户端独占的状态变更任务与另一独占提醒任务，最多 400 客户端；跨项目轮转。
状态变更采用 BLOCK/UNBLOCK，待受理用 manager、开发中用原 developer。开发中
前驱必须真实已交付。提醒先实际 create，再用新幂等键请求 existing-event 去重；
检查 created=false、event ID 不变、版本不再增加。所有准备请求不计短窗结果。

私密 packet 仅含会话、TTL、实际任务快照、合法路径和规则；不复制原密码或 DB
凭据。输出固定 FD、O_EXCL|O_NOFOLLOW、0600，不打印正文/令牌/异常详情。
中途失败保留已生成文件/真实业务变更，绝不覆盖或偷偷回滚已提交事件。

短窗驱动为 stdlib HTTPSConnection、严格 CA/主机验证、每客户端独立持久连接、
无自动重试，客户端每轮依次 GET/contract/transition/existing-escalation。
每次新幂等键；真实响应版本驱动下一次请求；任一异常/版本/事件语义不符终止该
客户端并保留匿名失败。启动 barrier 有界，整体 duration<=120s/请求 timeout 有界；
根原容器 21:00 UTC hardstop 不变。结束写新私密 updated packet，恢复状态不靠猜测。
输出匿名 request UUID、状态、字节、wall/CPU、连接创建次数、writer 时间、每路径
量化统计。持久连接语义与正式冻结工具可能不同，不能借此替代 400/600/270 验收。

本地只跑 owned stub/offline/SQLite 开发检查。真实新 MySQL/TLS/CLI/session packet
执行由根负责，未跑的部分明确为待执行。对旧 independent 资料不读、不联络。

根后续明确要求区分原6000-task seed与本地400-task开发fixture：先只读输出实际
候选counts，`--inspect-only`不发服务令牌/登录/业务写；不足400保留counts并拒绝，
不是业务缺陷，不改guards，可先slots1或40。最终实现只选DEVELOPING/developer
变更槽，另一提醒候选池排除全部合格变更任务（比只排除最终选中槽更保守）。原
seed算法150/project前60已交付，余90六态循环→600 developing，前驱索引均<60，
是静态性质；本次真实数据库是否满足仍以root实际profile为准，当前NOT_PROVEN。
