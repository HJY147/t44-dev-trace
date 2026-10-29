# R29B 本地原生 catalog 查询注册候选

基准 a92e5e73da93ba23748c3bab113103036c395d50，隔离树 codex/database-dry-r29b。

四个限定模块共有1191物理行，当前没有发现可安全删除的百行职责重复块。实际候选只改 migrations._catalog_defects 的 queries 注册：由 `(label, query, expected)` 四组三元组改为 `label: (query, expected)` 四项有序映射，循环解包相应调整。四个标签唯一且静态，Python 3.12 dict 保持插入顺序。没有增加新辅助函数、依赖或动态SQL。

该差异不是规模闭合方案；初步对单文件 cloc 374→370，预期应用5887→5883，必须在阶段源码提交后用原计数器确认。原生属性的预期构造、四份只读 SQL、缺陷格式与遍历、CHECK parser、DDL/hash/版本/迁移锁全部逐字不动。seed/rows/scans 不改。

先跑原 catalog/语义/迁移顺序回归；新增精确a92e旧源差分验证成功、组合缺陷顺序及四个查询阶段异常的SQL顺序和上下文退出；随后运行原 persistence、seed性质与下游本地回归。没有配置或连接真实MySQL，不读PRIVATE/未公开用例，不联系测试岗，不操作云，不代根合并。
