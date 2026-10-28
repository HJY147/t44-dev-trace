# 默认全列查询候选：本地开发验证完成，待根审核/CI

AI 数据库岗；基线 **a12e9e70b963bacafda3242bb6d82e53ee912ff1**，先行设计 **6a1cb86b4a52a4536ec3df475a2b6567dab2f24f**，精确产品/验证源码 **82e92dfc420690980a6e16c88f209d08ab709e49**；分支 `codex/database-select-resume-20261028`。Prompt-Ref: ROLE-database-SELECT-RESUME-20261028-v1；实际派工和 AI 操作者见 prompt.md。

RowsGateway.rows 默认 fields 的 `tuple(t.c)` 改为 `(t,)`，交给既有 `select(*fields)` 生成 Core 全列查询。显式 columns 分支逐字不变；没有缓存语句/身份/业务上下文，没有少查 SQL、减列、删校验或改锁。参数、返回键、错误、UoW/调用方接口不变。本次生产恰一行替换；**固定应用有效行 5933→5933，净 0，仍超上限 833**。

## 语义依据和边界

锁文件及本地安装版均为 SQLAlchemy 2.1.6。[官方 Core SELECT 文档](https://docs.sqlalchemy.org/en/21/tutorial/data_select.html#setting-the-columns-and-from-clause)明确 Table 可作为 select 的参数并展开其结果列。实际比对 rel_2_1_6 的 selectable.py、_selectable_constructors.py 和 cache_key.py 与本地源码，三份 bytes/SHA 全同（sqlalchemy-source-verification.json）。Select 构造按 entity 做 coercion，SelectState 在生成列时展开 Table。Table 的 `_select_iterable` 会跳过 omit-from-statements 列；当前全部 18 个注册 Core Table 均没有这种列，且每表的列 identity、顺序与结果类型已核对。这是当前冻结注册表的等价结论，不能泛化为任意 ORM/selectable 永远等价。

boundaries.json 绑定准确 Git 对象：原 schema/migrations/UoW、全部原 persistence/812 测试、specs/资源/锁文件/CI/计数器及原 catalog-audit 全目录与 a12 完全相同。七种原生审计反例和原 31 case 证据没有删改；本轮没有重跑原生 MySQL，它们不冒充候选的新运行结果。

## 实际验证

Python 3.12.10、SQLAlchemy 2.1.6、pytest 9.1.1、Ruff 0.17.2、Bandit 1.9.4；复用既有 Python 解释器及只读已安装依赖，PYTHONPATH 指向本独立工作树，禁止写 bytecode，关闭 pytest cache。命令/退出码见 commands.json，原日志和 JUnit 原样保存。

| 范围 | 实际结果及限制 |
| --- | --- |
| 最终 tmp/787 契约差分 | 30 passed / 0.56s；18 表 × 8 情景 × 2 方言，共 288 对 SQL/params/positiontup/selected-column identity/compiled-result-column key/name/type 完全相同。覆盖默认/显式全列/重复及空投影、where/IN/predicates、正反排序、limit0/offset、share/update/skip_locked。SQLite 不执行锁；MySQL 仅编译，未证明真实锁竞争。 |
| 同一差分的 11 个拒绝目标 | 非法表/投影/排序、嵌套 ClauseElement、操作符、bool/负分页、非法锁和无锁 skip_locked，原/候选均在执行前拒绝。 |
| 同一差分的真实 SQLite 目标 | 生产 UoW/Rows 实际提交/读取用户、项目、outbox；完整结果键、UTC 微秒、JSON/null、1800 字说明、恶意文本绑定、显式列顺序、空 IN、排序分页/limit0；业务失败回滚、真实缺表错误脱敏与 rollback-only 后无部分提交均通过。 |
| 原 persistence + 812 迁移/默认/seed 全回归 | 138 passed，17 integration deselected，2 条原 record_property/xunit2 警告，90.22s；包括原 native/semantics/gateway/foundation/全量 6000 seed，不改旧断言。 |
| 静态 | CI 同配置限定 Ruff exit0，限定 Rows Bandit exit0，限定源/说明 diff-check exit0。不是完整产品 CI/覆盖率。 |
| 原固定 cloc 2.10 | design 提交 6a1cb86b 的应用字节等于 a12；与精确产品提交 82e92dfc 均实测 5933，逐文件计数相同，--require-range 均 exit1。规模门禁未过。 |

初轮同 30 项通过 12.11s；随后补上已有真实映射目标的显式 JSON/null/长文本断言，并让编译账本写入 pytest 自有 tmp_path，避免复跑覆写归档证据；该目标先单独 1 passed，最终整个文件同 30 项再次通过。重复轮次不累加为新用例。18 个初轮编译账本与最终账本字节相同。没有产品/测试失败；探索中读不存在的 backend/.venv、988_foundation.py、conftest.py、quality.yml 路径失败，纠正为实际路径，不记为功能红。最终临时脚本运行不写仓库证据目录，便于审核者复跑。

## PUBLIC 性能证据及未验证项

仅根转发的[性能岗 PUBLIC 报告 c96dc391](https://github.com/HJY147/t44-dev-trace/blob/c96dc391d5e50ede25d2d3b4a3a9ba709c688acb/agents/backend/cpu-profile-20261028/report.md)和 raw-manifest/query gzip 被读取。解压并实核 query 原件 887024 bytes、SHA `03876a7501eb0e2b9fe9f1a346c7dc42a7e2b9fb9a851dd68d1646b00c128462`，gzip SHA 亦匹配。引用和实核见 public-performance-reference.json。

该岗在准确 a12 上作进程内一表达式候选，198 对 MySQL/SQLite 编译签名相同；无 profiler 的纯 statement construction ABBA 中位数 A1/B1/B2/A2 分别 21.665/16.77958/16.01333/21.14708 us/statement，A/B 为 1.291/1.321，减少约 4.89/5.13 us。它不是本岗 82e92dfc 的端到端运行，未包括 cache-key generation、Session/SQL 执行、MySQL I/O 或候选 HTTP；不把纯构建 22.55%–24.28% 改称整体 API 加速、正式性能通过或云高 CPU/502 根因证明。

新真实 MySQL 结果物化/锁竞争/隔离级别/故障、完整开发 CI/覆盖率、准确源码审核、Linux、独立验收、候选 HTTP/云及正式性能均待总协调调度。本岗未启动 MySQL/HTTP 服务、云资源或负载，未访问原生库/旧 tmp796/原 tmp794 数据或任何独立私有材料，未写研究正文。根当前云仍冻结 a12，本候选未部署；新 source/CI 后才能另作部署决定。
