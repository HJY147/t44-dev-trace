# 数据库最终候选（本地验证，待统一 native CI）

产品/新 owner 测试：`b9d15aca2d1716c0a85b1c5f4e5ff285a89f5dfb`，基准 `5868779e949adef066fe26bffbc4f2e8afee7649`。依赖由 backend 岗独立锁定 `sqlglot==30.25.0`（`4c71161f`）；本树仅取该锁，不重锁其他依赖。

- 手写 CHECK Pratt 解析改为 MySQL SQLGlot AST：完整词法覆盖、单表达式、表达式节点与注释拒绝边界仍在；只正规化标识符大小写/引号、括号与合法 charset introducer，不运行优化器。字符串大小写、参数及逻辑/算术树保留。官方明确 parser lenient，故不能以“能 parse”替代门禁：[SQLGlot 文档](https://sqlglot.com/sqlglot.html#faq)、[MySQL 方言](https://sqlglot.com/sqlglot/dialects/mysql.html)。
- 列签名一次比较类型、长度、unsigned、fsp、nullable、default；内部 CLI 缺陷标签从 `:type/:nullable/:default` 合并为 `:column_definition`，HTTP/API 错误码与报告字段不变。Index/FK 的 expected 元组直建只适用于完整 Frozen v1，metadata/DDL 原字节及原 769 两方言完整编译比较保留。
- Outbox 通知在原事件锁与 UoW 事务中批量 INSERT；去重/顺序、回退边界、重复消费和失败回滚保持。engine 将已校验设置拆为 URL、连接与池参数；UTC/严格模式/连接清理不变。
- 原四条原生目录 SQL 及整个 `_catalog_defects` 函数 AST 与基准完全相同。迁移版本、checksum、显式库、MySQL8.4、空库、锁、marker/partial failure 与重验门禁保留。

最终本地回归 **239 passed / 27 integration deselected / 24.10s**，含 18 新 owner（196 表达式、38416 对旧新等价关系）、原默认 6000 seed golden、V2 关系/时间性质、769 metadata 双方言和原消息/查询/池守卫。确切耗时见 final-local.log。Ruff/format/Bandit 通过，无 nosec 或规则豁免。新通知测试实际观察单次 executemany 和完整回滚；不称正式性能提升。

原计数器/cloc2.10 对提交源实测 **5880→5806，净减74，65文件**；migrations370→307、delivery159→153、engine93→88。严格范围仍失败（exit1，超706），未达到250–350本岗目标。seed/Rows/UoW/Scan 复查后没有可在当前冻结输出下诚实再减百行的重复实现，保持原字节，不用格式、搬实现或删校验补数。

**未执行**：真实 MySQL8.4、全新镜像完整 CI/覆盖率/HTTP、独立验收、云及正式性能。总协调下一步必须在新候选镜像跑 native 全量，让 MySQL 实际返回的全部 CHECK 形式经过新解析器；本地239不能替代。未读 QA PRIVATE/用例/工作日志，未操作云。

失败如实记录于 verification.json；首次 Bandit 原JSON保留，初期 pytest 失败完整文本在本 chat 工具输出，未伪装成归档原始 XML。提示词/边界/命令/计数与本岗四件同步。
