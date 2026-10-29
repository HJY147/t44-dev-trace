# R30 实际结构候选，待计量，未准入集成

精确父源7374b3637b06465d448fc2e81952ba18fc676315，独立树codex/database-architecture-r30。旧R29B不改。

代码候选已真实写入migrations.py：五份固定INFORMATION_SCHEMA查询取tables/columns/indexes/checks/foreigns，共用TABLES生成同形快照，再由同一feature投影比较；取消旧Inspector记录与metadata临时dict的往返。CHECK parser和migrate完整函数保持原字节，DDL/hash/版本/锁及全部其他产品文件不改。

结构方向已获root限定准入；原794/956白盒注入点尚不适配新结构，原测试保持不动。若计量值得继续，先交逐项旧输入→新原始行/feature字段映射及原assert/负例清单，经root审核后才迁移fixture；不以修改断言变绿。当前未称新候选已通过回归或原生MySQL。

已发现规范化快照适配器本身有成本：格式化后的实际Git差异+185/-169，物理净增16（不是cloc）。下一步仅静态和固定计量；若没有净减，保留候选patch/准确源码commit后撤回，不继续扩大或迁移原测试。没有预填百行收益。

准入必须保持的完整行为：column_set、类型/unsigned/fsp/default/nullable/charset/collation；主键仅id；每个必需索引完整列序、unique、prefix长度、方向、种类、可见性及unique精确集合/冲突；FK完整集合、列序、跨schema、动作规范化；CHECK完整集合、原parser语义和enforcement；多余非unique辅助索引和额外表的原接受边界。当前实现尚需行为差分确认，不能把feature键子集比较单独当完整性证明。

释放门之前仅阅读/设计/编辑（含编辑用formatter，无check/test/build/基准）；已收到root明确释放后才进行静态/计量。没有云、外部库连接、PRIVATE读取或测试岗联系，不新增依赖，不声称HTTP收益。
