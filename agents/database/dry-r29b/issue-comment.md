Agent-Role: database AI
Prompt-Ref: ROLE-database-DRY-R29B-20261029-v1

R29B 已形成并推送实际小候选，基准 a92e5e73da93ba23748c3bab113103036c395d50，精确产品/测试源 8f29030756139061341e0a636c8774ca790964bd，分支 codex/database-dry-r29b；待总协调决定是否采用，没有代根合并。

唯一产品diff是 migrations._catalog_defects 四项查询注册从有序 (label, query, expected) 三元组序列改为 label: (query, expected) 映射，按.items()原顺序执行，删除重复中间结构。四份只读SQL、预期签名、全部原生catalog比较、CHECK parser、DDLhash/版本/锁逐字不动；seed/rows/scans、冻结接口/DDL、依赖和原测试断言均无修改。

原固定 cloc 2.10 与 source_count 对精确提交实测应用5887→5883/65文件，净减4，migrations374→370；严格范围仍exit1，超5100上限783。未找到≥798或百行安全方案，不将这个小整理说成规模闭合，也不通过计数口径、excluded资源或压缩语句取得数字。

本地新6个精确父源差分加原persistence/812/消息980/扫描990+974联合133通过、43未选、3原警告，52.26秒，包含原默认6000任务seed exact摘要与V2全量性质。先行56目标与此重叠不累加。差分覆盖成功、组合缺陷顺序、四个query阶段异常的SQL前缀和连接上下文退出；原CHECK/原生catalog/迁移顺序回归未修改。限定Ruff/format/Bandit通过，AST边界校验确认除注册和循环解包外完整产品模块相同。

首次新增临时文件format红及初次push TLS失败真实保留，修正/重试后通过。没有真实MySQL、完整CI、coverage、HTTP、独立验收、云或性能执行；无PRIVATE/未公开测试读取，无测试岗联系。证据与本岗四件归档 agents/database/dry-r29b/，后续封档只补证据，不改产品源。
