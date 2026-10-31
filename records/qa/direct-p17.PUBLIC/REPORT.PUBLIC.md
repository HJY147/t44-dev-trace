# Posttools v1.2：离线候选，等待新独立复核

原Direct16的NP及157未观察不回写。v1与v1.1已知缺陷冻结保留、不可部署。v1.2仅保留schema强引用寿命修复，补齐reserve后与实际HTTP dispatch前门禁；未dispatch记录以reserved=True消费恰好一份配额，预算耗尽不伪造HTTP错误，不晚计PASS。

有效runtime为旧基底9cf +新post模块+编译器+BOOT组合，准确SHA/binding见tool-manifest和RELEASE，不称整个runtime未变。原client/call/conn/task_equal/val_headers和Metrics为同一函数/类对象，测量循环prefix逐字SHA d522db77778d5bc81dff7c78f9910ac45a137d7e4c6da7b5d43b73e39bf19706。保400/60+600、四P95≤270ms/10分钟桶≥1000/零稳态错误、400快照和400完整历史审计、原response/header/审计作用域与全部audit IDs断言；不提前停止历史分页，不加非契约过滤。

只在post阶段使用64个I/O槽、8个编译验证进程。成功预算仍40秒，grace30秒只清理，不计预算内成功；在途HTTP/验证及owner先退出，再close/join pool/writer。任何缺项、post错误、pending/超期或日志不完整非零退出；13项真实BOOT worker分支退出码回归含旧metrics PASS/independent NP均通过。非零仍封存回收。

|本地内存阻塞传输重放|实际结果|
|---|---|
|5092个真实完整响应+2400变异差分|与原schema校验接受/拒绝完全相同（2000双拒、400双接受），原断言AST保留|
|10000个交替临时schema根|正例全接受、错类型全拒绝，无id寿命误命中|
|400互异合成task，8582次完整大历史dispatch|40秒预算内27.319秒；400快照+400审计；全owner/pool/writer停止，raw完整|
|1秒预算、2秒阻塞响应|64在途；400明确未完成，post_errors0、race0；晚返回不补PASS|
|1个HTTP503|399完成+1 ERROR，非PASS；raw完整、不广播关闭其他在途读|
|6阶段deadline边界|admit/reserve/setup/response/validation/下一页均无预算外新dispatch，reserved最终0、late非PASS、读者退出后close|

所有测试仅本地内存传输fixture，采用原已认证响应shape/历史并重映射合成task/audit IDs，不是新增HTTP/TLS端到端或生产性能测量。主机macOS arm64，8物理/逻辑CPU、24GiB RAM，无Linux8CPU/8GiB cgroup，27.319秒不保证云端40秒。详细时刻/排队/HTTP退出/owner/global close及错误见各PUBLIC JSON。没有新VM/SSH/云/SUT操作，也不追加部署准备。本候选必须另经新无上下文独立工具复核，不能以自检替代其批准。
