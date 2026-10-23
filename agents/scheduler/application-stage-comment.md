Agent-Role: scheduler
Prompt-Ref: ROLE-scheduler-APPLICATION-v1
Refs: #6

完整应用模块已有真实代码：默认零参EscalationFacade rules/list/create返回冻结data；同Runtime UoW重验scope/state/任务/排期/规则/窗口，原子outbox2+ledger+task版本/计数+审计/幂等快照。硬键task/schedule/level不随rule_version绕过，savepoint真实唯一冲突不留临时outbox；owner+全部active经理快照，临期only owner。

APScheduler独立进程和正式python -m t44.scheduling已实现，ScanStore固定cutoff/keyset页/UUID/游标/心跳/计数，确定结果后推进，实际进程在commit后/checkpoint前退出后可用CLI恢复。默认60s/coalesce/max_instances1，单机flock；不在API多worker内启动timer。规则JSON现是冻结显式窗口结构，raw UTF8 hash+snapshot保存；decided_by=1为契约合成例值边界，不冒称用户真实DB身份/逐条技术审批，部署须核对映射。

最终107passed（17.49s），其中22项真实MySQL8.4.11/ASGI/CLI：20超期全覆盖、重复/崩溃恢复、并发、改期、终态/blocked、savepoint/回滚/拒绝审计、104收件人、跨rule_version硬去重、冻结GET/202。Ruff/Bandit通过，仅scheduling覆盖83%（CLI子进程未汇入），非全产品或独立验收。原失败与100/106/107必要修复链、XML/覆盖在本岗application-*；无本机RabbitMQ网络/P95/独立验收或全局代码规模达标声明。规则扩展真实diff只变1临时配置/0解释模块，生产仍仅D001三级。

部署接口与实际命令另交Issue7；根按现有PR19准确SHA集成审核，本岗不自行发布审核通过状态。
