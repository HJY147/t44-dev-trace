Agent-Role: database；Prompt-Ref: ROLE-database-SCAN-RUN-DEDUP-RFC-v1。

本阶段只做设计，未改生产。[完整RFC](https://github.com/HJY147/t44-dev-trace/blob/6aeb7e67d90767b7408967a6782e13c569e9d423/agents/database/scan-run-rfc/design.md)和[真实预算](https://github.com/HJY147/t44-dev-trace/blob/6aeb7e67d90767b7408967a6782e13c569e9d423/agents/database/scan-run-rfc/line-budget.json)已提交；[未应用补丁](https://github.com/HJY147/t44-dev-trace/blob/6aeb7e67d90767b7408967a6782e13c569e9d423/agents/database/scan-run-rfc/candidate-v2.patch)仅供复核，不能直接投产。

按原 cloc 2.10 和项目 Ruff 100 列，scans.py 109→129，facade.py 205→186，联合 314→315，净增 1。实际生产节省 0；不能只记 facade 减 19 行。旧审核 28–47 只是估算，总协调已明确否决此候选，不安排调度岗实施。

事务内 helper 不应拥有 UoW/commit。scanner 的始终 INSERT→duplicate 后 FOR UPDATE、自有短 UoW/完整行返回，与 API 的先普通 SELECT/调用方业务 UoW/整数 ID 返回/具体 RULE_VERSION_CONFLICT，需要保留各自适配。草案还存在 API 罕见未知 row 内部异常类型未等价，已公开列为不能准入，不靠宽泛捕获掩盖。

仅 git apply --check 与两候选 ast.parse 通过；未执行 pytest/MySQL/HTTP/MQ/seed/CI/覆盖率/性能，未改 DDL/API/冻结件/测试断言，未联系测试岗或读取其私有资料。若未来另有准入方案，DB 只改 persistence，固定调度岗消费 facade；本次不需要消费。root 最新全局 5980/超 880 为其报告，本岗只核两目标文件与新 Runtime 源相同，不冒称全局计数通过。
