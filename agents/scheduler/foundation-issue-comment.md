Agent-Role: scheduler
Prompt-Ref: ROLE-scheduler-FOUNDATION-v1
Refs: #6

已实际实现 JSON 规则加载/严格验证、now-planned_end 最高窗口纯判定、UTC/六位小数/1000至9999年边界和可注入同步回调的 APScheduler 3.11.3 BlockingScheduler 生命周期。默认使用 D001 三级窗口和60秒周期；导入无启动副作用。未建立空CLI或真实DB扫描。

回复消息岗：D001 已采用同任务+排期版本+升级级别一次的业务语义，改期开新排期版本；规则版本用于审计，不授权同排期同级重复升级。D004/U006 字段/错误码取舍现也已由用户采用（ae60dc3），具体业务门面仍须责任岗确认。请数据库/消息岗确认原子升级登记+待发送记录及事件/收件人去重的可调用门面；本轮没有实现这些持久能力。

回复部署岗：采用独立调度进程；本轮只有 build_scheduler(scan_callback) 与 run_scheduler(scheduler)。正式命令、SIGTERM组合根、就绪/退出码与恢复核对待真实回调接入。max_instances=1只限单进程，不提供跨进程安全；业务恢复依赖后续持久记录，不依赖内存job store。配置结构为AI技术选择，不冒称人的技术审批。

最终77项模块自测通过（0.35s），仅 backend/t44/scheduling 的129语句/46分支覆盖100%；Ruff原始失败/修复输出保留于 agents/scheduler/foundation-validation.log。没有MySQL/RabbitMQ/HTTP联调、AC-07、产品性能或独立验收。接口约定/复杂度见模块README，真实状态见 reports/modules/scheduler.md。
