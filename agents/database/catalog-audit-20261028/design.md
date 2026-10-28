# 原生目录补审计：先行设计

AI数据库岗；基线22f666e2，应用基线f4bd382d。用户2026-10-28恢复开发；总协调认可先分析后修复，预留编号794。本次不以修复隐瞒规模增长，不再尝试被真实反例否决的raw SHOW hash替代。

## 已证问题与依据

前次c99871b9原生报告显示：真实MySQL8.4.11的DESC索引经过锁定SQLAlchemy反射后丢失排序信息，而956的假Inspector负例具有该字段，因而假例拒、真实例漏。当前check_schema还未核对列AUTO_INCREMENT、表引擎/默认排序规则、字符列字符集/排序规则及CHECK ENFORCED。

冻结field-dictionary.md第10–11行、schema.sql及打包schema_v1.sql已要求统一自增id、InnoDB、utf8mb4_0900_ai_ci、指定ascii_bin字符列；原索引均默认升序BTREE、完整列且可见，原CHECK均强制执行。只检查这些已冻结性质，不增加业务条件、表、列或迁移版本，不改变REST/API、锁/marker/目标库、错误协议或既有CHECK/FK归一化。

## I/O、责任及失败边界

- 输入：原check_schema(engine)的明确MySQL连接与从原已验SHA DDL构造的TABLES元数据；新增四次只读INFORMATION_SCHEMA查询，分别读TABLES、COLUMNS、STATISTICS、TABLE_CONSTRAINTS。
- 输出：原passed/defects/tables/columns形状不变；新增缺陷码明确指出原生目录性质不一致。SQL错误继续交原migrate SQLAlchemyError处理，不吞错或当通过。
- 只检查冻结18表与必需索引，忽略原允许的额外非唯一辅助索引；不以运行数据、表AUTO_INCREMENT计数、统计/引擎估算行数判断DDL。
- 字符集和排序规则的期望来自可信元数据的列显式值及表默认值；非字符类型的原生NULL/JSON特殊性质先在新空schema观察后显式处理，不依当前目标值自行认可。
- 现CHECK表达式、外键动作与当前库归一化、默认值/类型/空值/主键/索引兼容路径保留。ASC/BTREE、NO ACTION/RESTRICT、当前库限定、冗余括号与合法字符引导符仍须通过。

## 计划验证

在根许可的官方MySQL8.4.11 binary上启动本岗新socket-only、mysqlx关闭、128MiB实例；资源只在项目tmp/794新目录，受570秒运行+30秒清理上限约束。只用新数据库，不读取旧runtime/env/凭据，不操作原PID7980/13306。停前核child PID、datadir命令、pidfile、@@datadir，数据保留。

先以未改旧实现记录六项真实漏判，再以同一新DDL基线逐项变异/恢复核修复；加升序/计数/字符引导符/括号/外键等价正例及原956语义负例。保存实际SQL、原生目录、检测结果与恢复结果，设置错误与产品失败分开。补migrate重复拒绝断言与非MySQL模拟目录单元测试，不修改原业务断言。真实8.4.11通过仅证明该版本/平台，不能冒称Linux、8.0或正式独立验收。

当前参考：[STATISTICS](https://dev.mysql.com/doc/refman/8.4/en/information-schema-statistics-table.html)、[COLUMNS](https://dev.mysql.com/doc/refman/8.4/en/information-schema-columns-table.html)、[TABLE_CONSTRAINTS](https://dev.mysql.com/doc/refman/8.4/en/information-schema-table-constraints-table.html)、[TABLES](https://dev.mysql.com/doc/refman/8.4/en/information-schema-tables-table.html)。本次已浏览官方资料；原生元数据提供索引排序/可见性、列额外属性/字符集及检查执行标记，不能由SHOW字符串等价假设替代。
