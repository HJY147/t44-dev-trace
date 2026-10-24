# Scan run 事务内去重草案：不准入生产

Agent-Role: database；Prompt-Ref: ROLE-database-SCAN-RUN-DEDUP-RFC-v1。操作者为 AI；本轮没有学生亲自改码、产品测试或独立验收。

## 结论与依据

总协调已明确不批准实施。审查建议 B 的“可省 28–47 行”是事前估算，不能作为已实现收益。基于集成 `162305f888ac094e38448ef95d4748248ae57bfc` 的两个实际文件，完整保留主要读写顺序和事务所有权的候选经过项目 Ruff 100 列格式化及固定 cloc 2.10 计数：

| 文件 | 原代码行 | 未应用候选代码行 | 候选减原值 |
| --- | ---: | ---: | ---: |
| backend/t44/persistence/scans.py | 109 | 129 | +20 |
| backend/t44/scheduling/facade.py | 205 | 186 | -19 |
| 合计 | 314 | 315 | **+1** |

只减少 facade 19 行而忽略新增持久层 20 行，会得出错误收益。当前生产改动为 0，实际生产节省为 0。总协调后来报告 Runtime 新源 `5dcb73cc10c38deb14fae68d33318b04d538fecf` 的全项目有效代码为 5980、超上限 880；这不是本岗新跑的全局计数。本岗实际 `git diff` 确认该提交与本候选基线的两个目标文件完全相同，预算仍适用于这两个文件。

## 最小候选内部接口与适配成本

`candidate-v2.patch` 是未应用研究草案，**不能直接投产**：

```python
def start_run(
    g, run_id, rule_version, rule_snapshot, rule_hash, now, *,
    existing=None, duplicate_lock="update", conflict_error=StatementRejected,
):
    # 返回 (整数主键, 已存在持久行或 None)
    ...
```

- `g` 必须是调用者当前有效事务的 RowsGateway；没有 Engine、factory、commit 或 rollback 参数。helper 只使用原有嵌套 savepoint，不新开 UoW、不提交事务。
- run_id 仍经 UUID 转 bytes16；规则版本、完整 JSON 快照、原文 hash、当前 cutoff/started/heartbeat 和全部计数初值在一处写入。既有 UUID 只核对原有 hash 与版本，不偷偷改为重算 JSON hash 或重写快照。
- `existing` 仅可由可信调用方按同 UUID 读取。`duplicate_lock` 只控制插入唯一冲突后的原查找锁；scanner 传默认 update，API 显式传 None。
- 新插入返回 `(id, None)`，避免给 API 多加一次 SELECT。scanner wrapper 在原 UoW 取完整持久行；重复时直接返回已锁行，避免重复 SELECT。若统一强制返回完整行，API 新建成功就会多一次数据库读取；若以未读回的 Python dict 冒充持久行，则可能改变 JSON/UTC 规范化，不采纳这两个捷径。
- 规则冲突的 exception factory 是为保留 scanner 的 `StatementRejected("Run UUID cannot change rule snapshot")` 和 API 的 `Rejected("RULE_VERSION_CONFLICT")`。不使用宽泛 `except StatementRejected` 做业务码映射，因为那会吞掉未知 run、UUID/字段拒绝等不同错误。
- 该候选还暴露一个**未批准的内部差异**：API 在唯一冲突后查不到行时，原代码会因 `rows[0]` 产生 IndexError；候选显式抛 `StatementRejected("Unknown scan run")`。当前 Runtime 都映射 INTERNAL_ERROR，但不能据此外推内部异常等价。既然本候选已净增行，不再添加适配层人为维持这个罕见分支，也不申请投产。scanner 的原未知 run 错误仍保留。

相比原两段私有实现，候选需要额外返回投影、查找锁与冲突映射策略。它只是展示共享的真实成本；不建议把这些参数引入生产后再为规模数字压缩排版。

## 两个调用方的完整事务边界

| 路径 | 原算法及必须保留的语义 | 候选草案处理 |
| --- | --- | --- |
| ScanStore.start | 每次自己打开短 UoW；始终 INSERT；只捕获 kind=duplicate；savepoint 回滚后按 UUID FOR UPDATE；成功新行 get；版本/hash 冲突为 StatementRejected | wrapper 保留 factory，helper 不持有工厂；新行 wrapper get，重复直接返回锁行 |
| EscalationFacade._run | 已处于 Runtime 写事务及 create 的外层 savepoint；先普通 SELECT；存在即核版本/hash；缺失则 INSERT 到内层 savepoint；重复后普通 SELECT；返回整数 id；冲突为 RULE_VERSION_CONFLICT | API wrapper 保留第一次普通查找，传入 existing 和 duplicate_lock=None，仅具体规则冲突 callback 返回业务异常 |

API 外层仍拥有 task CAS、escalation ledger、outbox、audit、幂等快照与 commit。helper 不能提前提交 run，不能把规则冲突当普通重复，也不能在 create 的外层 savepoint 回滚后留下孤立 run。scanner 的 start、升级 HTTP 提交与 checkpoint 仍是不同短事务；本次不把它们合并，不触碰 cursor、计数、kill 后重启恢复、tick/recoverable 或状态解释。

## 锁与异常分析的证据限度

静态比较可确认候选不增加数据库查询或行锁种类：scanner 插入失败后仍 FOR UPDATE；API 现有行和插入竞争后仍非锁定查询。原 session/idem/必要 project/member/task/children 的调用位置不变；helper 不回头申请 project、member 或 task 锁，故没有从代码中新增一条跨资源反向锁边。唯一冲突必须在内层 savepoint 退出并回滚后才读取已有行；其他 PersistenceIntegrityError、连接失败和未知执行异常继续外传，不吞异常、不重试整个业务事务。

这只是草案静态分析，**不是死锁、真实并发或故障恢复证明**。若将来另有合理接口再获准，数据库岗只实现 persistence/scans.py；固定调度岗负责 facade 的消费及 HTTP 错误/业务副作用回归。须保留原 MySQL 并发同 UUID、异 hash/版本、非重复约束传播、调用方回滚无孤立行，以及 crash 后 cursor 恢复等断言。因为总协调明确否决本候选，本阶段不排这些运行、不申请新脚本编号，也不等待调度岗实现。

## 实际执行与范围

- 阅读 AGENTS、职责/交接、现有 Rows/savepoint/UoW/scanner/facade、已发表架构审核与原模块测试的相关段落。
- 独立 worktree `.agent-worktrees/database-scan-dedup`，分支 `codex/database-scan-dedup`；产品文件没有编辑。草案仅生成于本岗 patch 和 ignored scratch。
- 首次 scratch Ruff 调用未指定项目配置，使用默认 88 列，触碰了无关旧行；该观察被否决，未作为最终预算。重新从原文件提取限定修改，用 `--config backend/pyproject.toml` 的 100 列生成候选 v2；两个原方法以外的产品内容不改。初始原稿及失误说明保留。
- 实际固定 cloc 工具 SHA256 为 `bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83`；原/候选逐文件 JSON 和 `line-budget.json` 保留。它是未应用候选投影，不是已提交应用源码计数，也没有改变主口径。
- `git apply --check candidate-v2.patch` 退出 0；两个候选文件 `ast.parse` 通过。这只是补丁适用性与语法检查，不是产品自测、覆盖率或验收。
- 首次资料 `git diff --check` 退出 2，仅因 `.patch` 原件中标准空上下文行带单空格；原件不去空格或变造。后续只排除两个 patch 的这项资料检查，其余文档继续检查。产品代码与产品门禁没有修改。
- 未运行 pytest/MySQL/HTTP/MQ/seed/CI/性能；未改 DDL、14 冻结件、依赖、服务/API、测试断言、源码统计脚本或他岗源码；未读取独立测试私有材料，未联系测试实例。

## 后续建议

关闭本候选的实施调度，把“发现重复 → 明确差异 → 实测净收益 → 否决不合适抽象”如实计入 AI 质量过程。其他共享能力应按各自完整实现重新预算，不把本轮净增行、旧估值或未执行的 tick 去重计为节省。规模与性能门槛继续由总协调列为未通过；本岗不设置审核通过或发布状态。
