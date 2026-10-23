# M3 图示与设计说明修订记录

Actor: coordinator_agent（AI）；Prompt-Ref: ROOT-documentation-M3-DIAGRAMS-v1。

这是2026-10-23开发过程中的文档修订，不是补写开发前历史。M2原始提交`44920169130405320e5dab465730467c1987e7df`与其中7图未渲染快照保留；本轮从已有报告修订为8图，实际渲染、查看独立PNG。Word尚未逐页QA。

| 触发证据 | 真实修改 | 验证与边界 |
| --- | --- | --- |
| 用户U011/U012要求需规先行、持续优化及多画图；M2状态图过密 | 将主要交付路径与阻塞恢复分开，中文状态标签与正文守卫对应 | 主图含六个交付阶段，阻塞子图补足第七态；不新增合法边或客户端target_state |
| 产品审核e01指出ER关系不符DDL | TASKS到OUTBOX_EVENTS改为可选任务引用，并解释项目/成员/迭代事件 | 冻结DDL的task_id可空，Business.outbox取call.path.get；未修改DDL |
| 审核核对Runtime后指出重试说法不实 | 说明数据库死锁/锁超时返回503，由调用者保留原key/内容重试 | 区分Scanner对版本/排期冲突最多三次的局部重读；不是任意事务自动重试 |
| 审核核对Scanner._execute与run后指出时钟说法不实 | cutoff限定本轮候选；每次候选请求的clock用于级别计算 | 修正伪码，不把整轮cutoff充当每次事件判定时刻 |
| b49实现清理了重复Protocol | GuardContext名称改为实际TransitionContext | 不声称一个已删除的接口仍存在 |
| 真实门面调用关系 | 架构图由Business/Runtime连接NotificationFacade | 不把HTTP组合根装配误画为业务读写路径 |

渲染工具、源和产物hash见[图清单](../diagrams/README.md)与[manifest](../diagrams/manifest.json)。第一次工具路径猜测失败、依赖安装脚本限制失败及随后明确禁用安装脚本成功的原始日志分别保存在`records/validation/mermaid-tool-install*.log`；使用已有Chrome，没有声称安装了新Chromium。

本轮不改变产品审核不通过的结论：审核报告绑定`e01f5dcf9d8ef5a88161fcbc87ab142fba74cdef`；前端修复、Schema语义漏检修复、代码规模、独立验收和正式性能必须分别以新证据判断。修正文档不替代修复产品，也不计为学生亲自修改代码或亲自撰写研究报告。
