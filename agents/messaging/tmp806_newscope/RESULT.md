# tmp806_newscope 实际结果

AI消息岗；ROLE-messaging-SIZE-20261025-v1。结构设计先于首次实测，基线与候选均为已提交快照，计数脚本/分类/生产目录集合不变。

| 项目 | 基线396b646 | 候选c4b3f114a5525c0fe0fd031d2b3603070a2be892 | 净减 |
| --- | ---: | ---: | ---: |
| 全application固定cloc | 5875 | 5862 | 13 |
| messaging/facade.py | 95 | 85 | 10 |
| messaging/broker.py | 129 | 126 | 3 |
| messaging/worker.py | 84 | 84 | 0 |
| messaging/__main__.py | 49 | 49 | 0 |
| 消息模块合计 | 357 | 344 | 13 |

所有其他application文件逐文件cloc不变，包括全部scheduler。after.json绑定真实代码提交c4b3f114，而不是未提交diff；before/after使用同一固定classifier与SHA=bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83的cloc2.10。主应用仍超过5100达762行，本岗未达到100–200目标，不伪报达标。最初15–50是设计估计，原展开风格保留后实得13。

## 真实去重而非格式操作

- Facade三条路径的active成员查询/锁/项目范围统一，复用既有page，两个状态计数使用同一范围；保持项目不存在优先级、当前recipient、share/update锁、CAS和read≠handled。既有page多出的id次排序在唯一id上等价，输出仍按id降序。
- Broker connect/publish/get/keepalive清理与脱敏共享一个小contextmanager，各自错误码仍明确；close自身不递归包装，False NACK与不属于网络的ValueError保持原传播。UnicodeError/StatementRejected均是ValueError子类，移除重复except类型未删死信处理，专门性质用例验证。
- 没有改public签名、owner确认、事务边界、幂等、重试、fallback/confirmed恢复、ACK/NACK/DLQ、DDL/OpenAPI或门禁，也没有移出计数目录。Worker/main未强行再拆helper；跨岗原语只设计交接。

## 开发验证与失败保留

- 既有本岗用例：基线17通过（before-tests-run2.log），候选17通过（candidate-tests.log）。
- 新806性质/故障22项在原396b646归档backend包上通过（before-properties.log有实际导入路径）；现有+新39通过/23integration未运行（after-properties.log）。
- 性质包括9组read/handled筛选与独立计数、分页、项目错误优先级/共享锁、connect错误不被覆盖、publish/get/heartbeat故障脱敏清理、False NACK边界、DB NACK与ValueError子类DLQ。
- 初始没加backend pytest配置导致exit5/0收集，原before-tests.log保留；新测试首轮4个C408，lint-run1.log保留，仅修测试字面量后Ruff通过，不改规则。
- 本轮不读取其他runtime或凭据，不执行真实MySQL/Rabbit、全CI/云、性能或独立验收；历史结果不外推。root统一整合与全CI。

## 跨岗交接（未实现）

1. Scheduler event()可复用既有model投影，保持disposition/handled_count，预算5–15。
2. Scheduler _run和DB ScanStore.start的run字段/查重可共用数据库拥有的gateway内原语；每个调用方仍在原UoW，不能直接调用会开独立事务的Store.start。预算25–50，具体先由责任岗验证。
3. ScanStore.start已经依赖冻结DDL默认字段，Scheduler _run还重复多项默认值；统一默认字段策略预算7–10。
4. Business.outbox与Scheduler create的status/attempts/lease/confirm/time信封可抽BE拥有的纯值原语，预算15–25。不得构造假Business或新开UoW。

以上有交叉，不能相加当已证实收益；root已明确本轮只设计交接并排scheduler下一批。
