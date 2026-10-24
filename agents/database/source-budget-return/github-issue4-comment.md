数据库AI；ROLE-database-SOURCE-BUDGET-RETURN-v1。先行设计d8f91d7后，按root f986782和原cloc2.10/SHA/已提交应用根静态复核：仍6307行/66文件，上限5100、超1207（需净减当前19.14%）；66项逐文件code值与C6307/b66fa记录完全一致。backend5208，其中persistence1691/services1613/scheduling642/domain423/messaging357/contracts55/根427；frontend/src1084+index15=1099。seed370/migrations321/rows299/runtime276/CSS267/workflow247/api244是职责规模，不是可删预算。

现无可信保持业务/守卫的1207行缩减方案，生产本轮节省0。旧仓储兼容删除、seed受信row-builder、BE公共create/会话、FE未用CSS已经在当前数字中；不得再次扣减。scan-run等价helper旧314→315净增1；DDL AST整对替换可能增3–53，46/1及13混用旧parser兼容失败保留；CHECK-only旧估39–46仍未准入。3b9c907仅旧validator草案55→45（投影10，未全等价/未实施）。

新静态小候选：NotificationFacade.list的21行页装配交现有common.page，保留membership S锁、-id、全部谓词、rows→serialize→total/unread/unhandled三COUNT顺序；仅给page增加可选order_by，其他调用不变。完整两文件227→224，纯内存草案只投影省3行，未写生产/新源码文件/未运行。请BE/MQ owner后续若认为值得，再独立确认SQL/错误顺序/额外COUNT边界；本评论不请求现在实施或测试。

即使不应提前扣的乐观10+46+3=59也仍差1148，不能说“再重构即可达标”。无压行/移出计量根/配置藏逻辑/删权限事务审计；不需用户决定class/manager等技术细节。公开数值/候选/风险/历史快照见agents/database/source-budget-return/{current-count.json,static-receipt.json,notification-candidate-budget.json,report.md}。原静态STDIN命令漏dash的exit2已保留再更正；不把它算产品或测试错误。无源代码/冻结/DB/服务/测试/CI配置变更、无运行负载，不读独立材料/contact tester。Refs: #4。
