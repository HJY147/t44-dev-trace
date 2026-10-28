# 默认全列 Core 查询候选

Agent-Role: database；Prompt-Ref: ROLE-database-SELECT-RESUME-20261028-v1。

精确基线 a12e9e70b963bacafda3242bb6d82e53ee912ff1，独立工作树/分支 `database-select-resume-20261028`。本轮只考虑 RowsGateway.rows 的默认 fields 从 `tuple(t.c)` 变为 `(t,)`；显式 columns、参数绑定、排序、分页、锁、执行/映射/codec 和 UoW 均保持原样。此候选有效行净变化为 0，不能算规模减少。

本地 requirements.lock 与安装版均为 SQLAlchemy 2.1.6。官方 2.1.6 文档的 Core `select(Table)` 展开表列；本地 Select 构造对每个 entity coercion，SelectState 在列生成时展开 table 的 `_select_iterable`。后者会过滤 omit-from-statements 列，因此必须核当前 18 表没有此标记并逐表比较列顺序，不能仅以文档推断所有表永远等价。另比对官方 rel_2_1_6 的本地源码字节及 SHA。

限定验证：以 Git 对象动态加载准确 a12 基线 Rows，不修改它；对 18 表编译 MySQL/SQLite 的默认、显式投影、where/predicates、order/limit/offset、share/update/skip_locked，逐项核 SQL/参数/结果列同一。真实临时 SQLite 通过生产 UoW 验证完整映射、UTC/JSON/null/长文本、显式投影、排序分页、提交/回滚、执行错误脱敏与 rollback-only；无效标识/表达式/锁/分页检查须在执行前同样拒绝。现有 gateway/foundation/native-catalog/semantics 与本岗非 integration 回归保持原断言。新验证只用预先检查未占用的 tmp/787_database_select_resume_20261028。

不访问原生 MySQL、tmp796、原 tmp/794、独立私有用例/日志，不启动服务/云/HTTP/负载，不改 schema 审计七个反例、冻结件、计数器或老师研究正文。性能岗 PUBLIC 的 CPU 证据须另标采样源/仪表与限制；本岗开发验证不能宣布正式性能/独立验收。最终提交后用原 source_count.py 与固定 cloc 对精确提交计数，源与证据分开绑定；真实失败保留。
