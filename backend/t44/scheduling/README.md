# 调度基础模块与尚未接入的业务扫描

依据是用户已采用的 `specs/business-rules.md`（D001）。D004 的字段/错误码取舍已由用户采用（ae60dc3）；本模块仍没有业务 API、DDL 或数据库调用。

`load_rules(path=None) -> EscalationRules` 读取 `t44/resources/escalation-rules.json`。schema 1 校验版本标识、严格字段、三个有序且代码不重复的级别、阈值、收件人角色和 D001 的 60 秒周期；重复 JSON 键、未知字段、布尔冒充整数和不能表示的阈值均拒绝。资源的默认值是真正执行的 D001 三级规则，临期/严重超期阈值由 JSON 给出。

`select_window(now, planned_end, rules) -> WindowMatch | None` 只返回当前最高窗口及规则版本/收件人角色，不声称创建了升级或送达通知。两项时间接受 UTC-aware `datetime` 或 `YYYY-MM-DDTHH:MM:SS[.1至6位]Z/+00:00` 文本；拒绝非 UTC、无时区、超出 1000–9999 年或超过六位的小数，不把输入截断成微秒。到期时刻尚属临期，晚 1 微秒即超期，超期满 24 小时属严重超期。计算仅使用 `now - planned_end`，不会对年末的计划时间做 `+24h`。这是内部边界，不代表 HTTP/数据库接入已经实现或验证。

`build_scheduler(scan_callback, rules=None) -> BlockingScheduler` 接收同步无参扫描回调，返回未启动实例；UTC、60 秒 interval、coalesce、max_instances=1。`run_scheduler(scheduler)` 在专用进程中阻塞运行，KeyboardInterrupt 时等待执行中的回调结束，其他错误继续向上传播。进程组合根未来负责将停机信号接到 `scheduler.shutdown(wait=True)`。已有运行实例拒绝再次交给 run，且不会关闭原来的运行实例。

导入包不构造或启动调度器。不要在 FastAPI import/lifespan 中启动它；API 多 worker 不拥有扫描器。本轮故意没有 `__main__` 或空扫描 CLI：正式 `python -m t44.scheduling` 入口要在真实存储与消息回调可接入后由本岗补齐。内存 job store 只保存可重建的周期任务，不保存业务恢复/去重状态；max_instances 仅限制本进程，不能代替跨进程持久去重。

后续调用约定（业务语义依据 D001/D004，实际接入门面签名仍待责任岗确认）：

1. 每批使用一个 UTC `now` 和已加载规则快照，通过数据库门面分页读取未交付、未回滚任务；阻塞不暂停计时。候选携带任务、排期版本、状态/版本、计划结束和收件人标识。
2. 调用纯函数只得最高窗口；无匹配则跳过。事务内重新核对任务/排期与状态，再以“任务 + 排期版本 + 升级级别”登记唯一升级并同时保存待发送记录。规则版本用于审计，不独立授权同排期同级重复升级。改期保留差异并产生新排期版本。
3. 数据库岗提供唯一约束/原子登记，消息岗提供可靠接收/发布确认与消费确认；消息按事件与收件人去重。MQ 不可用时生成有标记的站内待办，同一事件恢复后不再提醒。调度不直接改业务状态。
4. 升级次数由成功持久登记决定，不能因扫描/投递重试再加一次；拒绝、重复、失败与批次统计分别留痕。重启重新扫描并重试未完成持久记录，不能仅前移内存游标而永久跳过失败项。

上述业务扫描、事务登记、幂等键唯一约束、留痕、重启补扫和消息降级均**尚未实现**。需要数据库/后端/消息责任岗共同确认接入契约，未进入联调，未做 MySQL/RabbitMQ/HTTP/AC-07 独立验收。

伪代码（仅约定，不是当前运行结果）：

```text
snapshot_now, rules = utc_clock(), load_rules()
for page in candidate_facade.pages(snapshot_now):
    for candidate in page:
        window = select_window(snapshot_now, candidate.planned_end, rules)
        if window is None: continue
        transaction.revalidate_and_record_once(candidate, window, pending_delivery=True)
message_facade.retry_pending_deliveries()  # 同一事件沿用原稳定标识
```

读取/验证配置时间和空间为 O(C)，C 为配置长度；每个纯判定 O(R) 时间、O(1) 额外空间，当前 R=3，因此为常数。未来扫描 N 个候选时判定为 O(NR)，分页内存 O(B+R)（B 为页大小）；数据库筛选、唯一键查询、事务争用和消息重试的代价取决于未接入的索引/实现，此处不把它们宣称为 O(1) 或给出吞吐实测。

官方参考（2026-10-23 查阅，安装版本 APScheduler 3.11.3）：[User guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html)、[BlockingScheduler](https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/blocking.html)、[BaseScheduler](https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/base.html)。选择 BlockingScheduler 对应专用进程；coalesce/实例限制/关闭等待按这些接口实现，未使用 APScheduler 4 API。
