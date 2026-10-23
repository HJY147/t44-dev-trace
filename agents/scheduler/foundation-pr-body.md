Agent-Role: scheduler
Prompt-Ref: ROLE-scheduler-FOUNDATION-v1
Refs: #6

按D001实现JSON三级规则的版本化加载与严格校验，并以now-planned_end纯函数只返回最高当前窗口。到期/微秒/24h边界准确，支持UTC与1000/9999年而不做结束时间+24h。提供显式构造/运行的APScheduler3 BlockingScheduler，可注入同步扫描回调，UTC/60s/coalesce/max_instances=1；导入不启动调度器或线程。

Ruff通过，77项模块测试通过；仅backend/t44/scheduling的129语句与46分支覆盖100%。原静态失败、必要修复及结果见agents/scheduler/foundation-validation.log，原始覆盖数据见foundation-coverage.json。依赖按后端只读hash锁安装，未修改共享锁。复现命令、后续接入约定和复杂度见模块README与报告。

基础模块已实现；数据库候选扫描、事务去重/审计/待发送、消息投递和正式进程CLI尚未实现。无MySQL/RabbitMQ/HTTP联调、AC-07、全产品覆盖率/性能或独立验收。开发中收到D004/U006字段取舍已采用通知（ae60dc3）；实际门面接入仍待责任岗确认。规则采用不等于人的配置结构审批或亲自改码。本PR为草稿，由审核岗另按准确SHA审阅。
