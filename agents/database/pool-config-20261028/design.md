# 显式连接池容量配置：先行设计

Agent-Role: database；Prompt-Ref: ROLE-database-POOL-CONFIG-20261028-v1。准确基线 `b9847f8a946a310b90e8fb228a0e5c1061612e13`，独立分支/工作树 `database-pool-config-20261028`；不包含尚未整合的 select(table) 候选 82e92dfc。

backend责任岗已委托本岗仅修改 `backend/t44/settings.py:mysql_settings()` 的两个 MySQLSettings 构造参数，并实际确认名字 `T44_DB_POOL_SIZE` / `T44_DB_MAX_OVERFLOW`。候选为直接 `int(os.getenv(..., "5"))` / `int(os.getenv(..., "10"))`，预计新增两有效行。没有 ENV 时每个默认值及所有原有字段与原 MySQLSettings 相同；任一显式 ENV 只覆盖对应字段。不增加 Settings dataclass 字段，不改 DATABASE_URL/TTL 来源。

MySQL URL/显式数据库/T44_DATABASE 匹配判断仍在原位置，先于新参数转换；无效整数文本直接 ValueError，不能静默回退到默认。转换成功后的 pool_size 正整数、overflow 非负整数以及原 timeout/port/identifier/credential 校验继续由原 MySQLSettings.__post_init__ 负责，不改它的源码、校验或异常文案。两个新参数按 pool_size 后 overflow 的正常 Python 参数顺序转换。新 ENV 不会在 Settings.from_env 提前读取，数据库仍由持久化 owner 按原生命周期创建。

仅本地配置契约检查：无ENV与单独ENV、A5/10/B15/0/C20/0以及64worker的5/0值解析；非法整数文本和0/负边界明确拒绝；原URL/库匹配错误优先于非法新参数；Settings中已有DATABASE_URL与TTL/其他字段保持原来源；构造原engine验证容量确实传入QueuePool且PyMySQL connect未被调用，最后dispose。目标回归只选原无外部组件的配置解析与lazy-engine/session初始化目标；不运行全量seed、HTTP、SUT、云或原生MySQL。

本轮没有性能实验。未来16worker的 A5/10 与 B15/0 同最大240连接，可隔离保留池与churn；C20/0为320加reserve64等于旧配置384，需要实际读回新目标MySQL max_connections与其他角色预算再准入。25/0×16为400还未计其他角色，不能默认为可用。64worker时5/0为320加reserve64；不能沿用64×(5+10)=960。此处只有整数预算设计，不是已创建连接、实际MySQL设置或性能通过证据。

新测试只放已由根预留且核空的 `tmp/786_database_pool_20261028/786_*.py`；不改原测试、engine/schema/SQL/事务/鉴权、CI、计数器或研究正文，不读任何独立私件。设计先commit，实施后实际记录命令、原始结果、精确源码与实际计数，交根审核及CI；默认配置不因费用充足而自动改变。
