# VERSION 2 合成算法原型准入设计

root明确授权放开VERSION1旧全表digest/精确分布，原业务断言不得删除。当前稳定回退5f77938，持久Python1691→1623净68。新分支codex/database-seed-v2-optimize-20261025。

目标而非成果：尝试seed348再净80–120；不够按真实量记，不压格式或将算法放到未计量外部数据。VERSION=2、operation syntheticSeedV2；CLI参数/结果键和manifest形状不变，旧库拒绝，不迁移/覆盖旧sealed数据。

新构造规则：每项目任务按归一化6天slot排序，state6的planned_end落其slot中点，其他状态的结束时间相对anchor、受seed确定；所有planned_start/end落项目迭代区间，任一完成前驱结束早于后继开始，避免旧固定2小时/75分钟及窗口失败脚手架。保留全部1..7任务状态、三独立manager/developer/reviewer、member roles1/2/4、评审逐轮失败→最后通过、delivery/rollback决策和相应评估/计划批准指针；记录reviews+decisions精确等于records，默认40P6000T9000D15000R。

以冻结schema默认值和同类JSON注解为唯一来源，统一证据/合成文本及可推导主键；DAG按合法(project,child,delivered predecessor)候选枚举截取dependencies，容量不足必须完整rollback。可统一时间戳，但必须保留task created≤review≤assessment created≤reviewed≤delivery≤rollback的顺序。

迁移/Rows/lease/CAS仍使用稳定68代码，不再改严格guard。新开发测试新增版本2业务性质/全量FK、指针、JSON、容量、时间和再现性；旧975固定digest仍按935历史实现执行，不改旧golden声称新算法等价。新fixture变更不替代MySQL/独立/性能证明，真实新库验证由root统一freshCI。
