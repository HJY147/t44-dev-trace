Agent-Role: scheduler
Prompt-Ref: ROLE-scheduler-APPLICATION-v1
Refs: #6

按冻结v1补齐真实升级与扫描：零参EscalationFacade对接API，传入g内原子写outbox2/ledger/task并由既有Runtime完成audit/finalize/idem；重验服务scope、状态/版本/排期/规则和当前最高窗口。硬键task/schedule/level，业务重复不加计数，savepoint冲突无额外outbox，完整owner/active经理快照。

唯一JSON与解释器改为冻结显式窗口/优先级结构，保留UTC微秒/1000–9999年差值判定、原UTF8 hash/snapshot。正式独立CLI使用既有service-token文件、flock、APScheduler默认60秒，ScanStore持久UUID/keyset/checkpoint恢复，不在API启动timer。一次扫描/实际进程退出后正式CLI恢复20项、104收件人等已有真实证据。

Ruff/Bandit通过，107项通过（22项真实MySQL8.4.11/ASGI/CLI）；仅scheduling357语句/86分支综合83%，不冒全局覆盖。原失败与必要修复链在application-validation.log，XML/覆盖与扩展真实diff同目录；CI=1/URL入口本机真库1项通过，不称托管CI。未验证本机RabbitMQ网络、前端全链、400并发/P95或独立验收。

本轮merge指定12f7141复用BE/DB实际门面，只提交本岗改动，不改共享锁。默认decided_by=1明确合成例值边界；D001阈值人采用不等于人的配置结构审批/亲自改码。部署须接真实token/单实例锁并核对身份映射；整体规模超限已由根跟进，不改统计口径或删测试。保持draft，由根按准确SHA整合/审核。
