# 独立验收 v2：收件人规模与实际行消息重放子集

结论仍为 **NOT_ACCEPTED_INCOMPLETE**。本阶段两个明确子集通过，没有新增确认产品缺陷；不能替代原MQ01/MQ02中仍未完成的故障竞态。

精确SUT `4c20f32b71635016815420472b9d4bb4fa850df0`。H6 `1cc1bcbbb7e49eea1999d1cc54347e03c9ca2697`、R7 `ee62739d96ebe256744b14d0298e50a58663120c`，run40005729957。908补充先冻结再运行；原manifest/8载荷及此前所有尝试不改。环境仍f118/neutral6b，无产品源读取、SQL写、本地负载或正式性能。286次HTTP响应Schema校验、28次只读SQL、20次实际返回审计引用核对。

**101名经理加1名负责人、20个真实事件的完整收件人集合已观察。** 本次独立初始化99名合成经理，加既有2名经理，共101；20条真实超期任务经调度产生20个level2升级。每个API嵌套事件和数据库outbox快照都包含准确的102名收件人。只读SQL核对每任务102名不同收件人、每名收件人20条通知，总2040行，且无重复(event,recipient)；任务状态不变，升级次数及版本各只增1。

经理本人列表的20条通知为nonfallback。没有逐一检查全部2040行的fallback标记或每人延迟；收件人存在性与逐人传输路径/时延是不同证据。没有将本轮20任务功能测试报成正式性能结果，也没有证明>100成员分页。

**从实际outbox行重建的消息重复发布子集已观察。** 实际join取得wrapper为event_id146/schema_version1/event_type2；按中性协议使用真实direct exchange/routing、持久属性、mandatory和publisher confirm，向broker发布两次。ready queue计数实际为0→2→0，subscription consumer计数一直为0。此观察支持旧计数前置条件不足以判断是否存在轮询消费，不回写此前BLOCKED。

先把经理通知分别标为已读、已处理。发布后等待8秒，SQL的全部102条通知ID/收件人/版本/read_at/handled_at与发布前完全相同，任务也未改变。未捕获原始产品发布字节，不能称为“原始消息捕获成功”；ready队列清空也不能单独证明consumer ACK时机、崩溃切点、confirm丢失或fallback并发事务。

run39998518039的原消息安全捕获BLOCKED、run40003603947的订阅计数前置BLOCKED均保留；LIFE02规范作用域不明的原始FAIL、先前UI问题及未执行范围保持。所有原证据不因本阶段发布或补充而抹除。

ZIP/CMS/证书已核哈希，使用本地0600私钥认证解密成功；环境就绪、harness启动与finally恢复true，harness exit2。恢复完成不代表产品全通过。精确来源、证据hash及范围见同阶段results。

仅本报告和同阶段results明确公开；原脚本/日志/截图、密文解密现场与私钥未开放。白盒、正式性能及其余未完冻结断言仍不宣称通过。
