# 定时调度模块基础实现报告

## 范围与依据
- 实际派工 `ROLE-scheduler-FOUNDATION-v1`；base `c5c14aa5504fc3671c040768359570518a3c7507`，独立 worktree/分支 `codex/scheduler-core`。
- 用户已采用 D001；开发中收到 D004/U006 字段/错误码采用（ae60dc3），未进入业务 API/DDL/DB 扫描联调。
- 状态：规则解释与调度生命周期基础已实现；业务扫描、持久升级/去重、通知、运行入口未实现。
- 初始化/M0 历史保留在本岗 WORKLOG；实际操作者为 AI scheduler，无虚构人类技术审批或人工改码。

## 实际代码与行为
- `backend/t44/resources/escalation-rules.json`：schema 1、D001-v1、60 秒、三级阈值/收件人集中配置。
- `backend/t44/scheduling/rules.py`：严格 JSON 加载/验证、UTC 时间解析、纯函数最高窗口判定。
- 临期从结束前 24h 至到期时刻；晚 1 微秒超期；超期满 24h 严重超期；首次跨级只返回最高窗口。
- 时间支持 1000–9999 年、UTC-aware datetime/严格 UTC ISO 文本，最多六位小数；超过精度拒绝而不截断。
- 用 `now-planned_end` 比较避免年末 `planned_end+24h` 溢出；返回内部 `WindowMatch`，不声称已升级/送达。
- `runtime.py`：显式构造未启动 BlockingScheduler，注入同步无参扫描回调，UTC/60s/coalesce/max_instances=1。
- `run_scheduler` 阻塞运行、打断时等待回调退出，其他错误传播；拒绝接管已运行实例而不停止原所有者。
- 导入无扫描器/线程副作用；不嵌 API 多 worker，没有伪成功空 CLI，正式入口待真实回调接入。

## 接口、幂等与复杂度边界
- `load_rules(path=None)` 返回不可变规则；未知/缺失字段、重复键、非法版本/阈值/级别/收件人均拒绝。
- `select_window(now, planned_end, rules)` 不读状态、不读钟、不计次；调用者提供同批时间/规则快照。
- D001 已采用：未交付/未回滚参与，阻塞不停表；业务去重为任务+排期版本+级别，规则版本用于审计。
- 改期开新排期版本；升级与待发送记录应原子提交；通知按事件+收件人去重，降级恢复后不再次提醒。
- 后端/数据库须确认分页、状态/排期版本重校验、唯一约束、事务登记与批次结果；字段规范已冻结，实际接入门面尚待确认。
- 消息岗须确认可靠接收/发布回执、失败/重试/降级处理；无跨模块调用，不把算法确定性称为业务幂等。
- 接入伪代码见 `backend/t44/scheduling/README.md`；业务恢复依赖持久记录，内存 job store 不承担续扫。
- 配置加载 O(C)；单判定 O(R)/额外空间 O(1)，R=3；未来 N 候选 O(NR)/分页空间 O(B+R)，DB/MQ 未实测。

## 执行与证据
- Python 3.12.10；独立 `.venv` 通过 uv 按后端只读 hash 锁同步，APScheduler 3.11.3，未改共享锁。
- 参考锁 SHA-256：`3b15a7bdf93024750835ac20584a140eb93f1dc7476be61bb0af145e8ff0cc30`。
- 实现前查官方 APScheduler 3.x User guide、BlockingScheduler、BaseScheduler，来源链接见模块 README。
- 首次 Ruff 失败为 B004/两项导入顺序；原命令输出在 `agents/scheduler/foundation-validation.log`，未擦除失败。
- 修正后原 76 项通过；发现已运行实例可能被 finally 关闭，补所有权保护与回归后最终必要复验。
- 最终 Ruff 通过；模块自测 **77 passed in 0.35s**，覆盖边界/非法配置、最高级/同刻、真实生命周期/失败/导入。
- 仅 `backend/t44/scheduling`：129 语句、46 分支均覆盖（100%），数据 `agents/scheduler/foundation-coverage.json`。
- 完整命令见验证日志；复现使用只读锁 `../backend/backend/requirements.lock` 及后端 Ruff 配置。
- 未运行 MySQL/RabbitMQ/HTTP、DB 扫描、AC-07、全产品覆盖率、性能或独立验收；模块结果不替代这些结论。

## 交接与后续
- WORKLOG、handoff、实际派工原文、验证日志/数据及 Issue 正文与代码同分支归档。
- Issue #6 回应旧问题：D001 明确业务去重范围，排期版本区分改期；实际消息/数据库门面签名仍待确认。
- 待补：候选门面、原子去重/留痕、可靠通知、停机信号组合根及重启恢复；需后续派工和接口确认。
- 本轮自己显式提交/推送并发 draft PR，交审核岗按 SHA 审核；不自行设置审核成功或合并。
