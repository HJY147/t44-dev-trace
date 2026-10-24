# 本轮实际派工（新任务标识用于归档）

总协调实际消息，操作者数据库AI，不是用户亲改：

> 新增一个10分钟只读小核查，接后端已公开纯静态交接 d83408955dea4afaab24991c00e490ad196c9ebe（root已merge），agents/backend/static-performance-next-measurement.md 和static-perf-path-receipt.json。其中依赖where task_id单列、冻结DDL无“显式”task_id前导索引；需要分清InnoDB实际是否自动建FK索引，不能由DDL显式列表推断不存在。只使用你先前ABBA/955自有且服务已停的developer fixture数据库（准确指定并核归属；绝不碰t44_demo_v11/native/v2/v3/任何独立数据）；现有共享MySQL守护进程不改设置/启动/停止。可做有限SHOW INDEX/SHOW CREATE相关表和plain EXPLAIN（禁止ANALYZE/实际负载），查明真实索引与少量代表SQL是否可用，明确当前小fixture计划不代表6000任务/400并发或根因/收益。不要创建/填充新DB，不改产品/DDL/用例/任何数据，不联系tester/不读H/H2/private refs/输出。无安全归属DB就只交公开静态DDL补充，不为这事询问用户。若需工具仅既有955或内联只读，不新增测试文件；材料保存在自有worktree报告/role prompt/log/module/handoff，先设计小提交再动作，Issue4实际COMMENT全文GET、阶段commit/push。全部项目目录内，约10分钟释放。
