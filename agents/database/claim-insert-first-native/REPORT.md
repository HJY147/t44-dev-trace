# INSERT-first候选真实MySQL拒绝证据

Prompt-Ref: ROLE-database-CLAIM-NATIVE-20261031-v1。仅本地自有socket MySQL8.4.11，非SUT/HTTP/云验收或性能对照。产品原版本90b，候选后端a2839e17；本岗不改backend实现或原测试断言。

## 结果

候选runtime SHA347efe971362ec3ae6d145bedc9a61ab6400c498499642c2bb4c66ce5c51a86b，原90b runtime SHAa8b6a6711f2a88249f760e05badd80c911ead6e25824e9d4400d8b3b1844a239；双方原DDL SHA c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4。

服务器启动默认显示REPEATABLE-READ，但测试engine明确设READ COMMITTED并实际SELECT读回READ-COMMITTED，与source90b engine.py97一致。不得用RR空gap假说归因当前产品延迟。SQLAlchemy2.1.6、PyMySQL、原initialize_mysql_session、原UoW及原DDL，flush_at_commit=1/sync_binlog=1，未关闭pool rollback。

- 候选16线程同时准备同一个新业务幂等key：1取得owner、4按原语义IDEMPOTENCY_IN_PROGRESS、11 PersistenceUnavailable；handle_error仅采异常类与errno，11项OperationalError errno1213死锁，另15项1062为预期duplicate。异常路径位于duplicate INSERT后原FOR UPDATE读。候选拒绝；不能靠自动重试隐藏该并发退化。
- 原90b相同脚本/数据形状/RC：1取得owner、15按原语义IN_PROGRESS，无底层driver错误。随后完成回放、hash冲突、16不同key同前缀、过期lease新owner抢占/旧owner fencing、插入事务rollback、撤销/过期session、新service scope claim等10项检查通过。
- 候选首项失败即停止后续检查，不能把原版本后续10检查的通过套给候选。未测候选云P95、未证明本轮P95唯一根因，也不宣称原版在所有可能调度下绝无死锁。

## 实际执行与资源边界

创建全新分支codex/database-claim-validation-20261031及独立datadir/socket，实际命令：PYTHONPATH=backend .agent-worktrees/.runtime/database-scale-r29-venv/bin/python agents/database/claim-insert-first-native/check.py candidate3，随后baseline1。路径均相对项目根解释，脚本在本worktree运行；候选Runtime只读从后端独立worktree加载。

前置尝试如实保留：项目.venv缺pymysql，改用既有database-scale-r29-venv；首个init因日志置于新datadir内造成非空被MySQL拒绝，保留失败目录，再改新v2数据目录与外置日志；v2首并发异常未收errno，保留RESULT.PUBLIC.json。candidate3增加无参数errno事件采集后得到上述明确反例。没有清理/覆盖原始失败。

候选和baseline自有server均finally执行mysqladmin shutdown，退出0且socket消失，原始PUBLIC结果含该证据。另有pid7980本地MySQL归属不明，本岗未连接或停止。服务器skip_networking，未修改其他库或全局配置。令牌仅RAM、不输出；原server私密日志和datadir留ignored runtime，PUBLIC不含SQL参数或Token。

## 交接

该候选不能集成或云复测；保留原90b行为。下一候选应从90b干净分支出发，不能叠加被拒INSERT-first。后端和root已收到实时反例；本岗可后续对新主事务行复用接口做RC一致性与锁边界验证。本次没有云访问、产品修改、额外正式测量或新后继run。
