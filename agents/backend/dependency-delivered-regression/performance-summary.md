# 性能和规模：已知线索与未证实（后端AI核公开材料）

准确当前根f986应用与候选C=b66fa36逐字相同；C只增加依赖边查询project_id，不改5+10池。该一行有合法FK读集等价证明；DB自有小夹具EXPLAIN估9216→1但仍filesort，尚无实际扫描/运行收益。C开发CI510通过不代表正式性能达标。

| 已有公开依据 | 可以说 | 不能说 |
| --- | --- | --- |
| bc5契约短profile：每请求1acquire/1实时auth，三候选4/5/5 SELECT；32并发acquire14.525ms、SQL9.239ms、dispatch6.123ms均值 | 并发增加伴随更多墙钟等待，连接生命周期是可核线索 | 区间inclusive重叠，非纯poolwait/SQL锁/纯队列，不能加总或解释正式503 |
| DB单次32并发、四段各4秒ABBA：5+10 P95 91.59/92.60ms、新建436/427；15+0 P95 74.47/72.91ms、新建0 | 增加保留数在该样本减少连接重建 | 非400×600/270ms通过或生产收益；六默认池峰90相同、保留30→90，内存/FD/故障代价未充分测 |
| 静态listTasks10S/2U，升级列表10+3P S/2U（P≤100） | 有重复实时鉴权、逐事件读取、分页/COUNT及规模相关成本 | S不是所有网络往返，未证明哪项是原正式瓶颈；不可直接删除授权/项目X锁/审计 |

原正式失败不取消，本轮无新计时或运行。下一步真正需要的是同一准确SUT/负载下关联结构化错误码与连接/执行fetch/锁/dispatch/编码资源证据，先分因再做单候选；任何测量仍由root协调，不在本轮启动。

规模固定cloc6307，超5100计1207；没有已证明可净省1207的等价方案。种子370/迁移321/Rows299/Runtime276是有职责的文件，不是可直接删除行数；未应用C原型草案即使省10也不解决缺口。人需要决定的较大事项：保留全部需求继续重大可审重构并承担工期/回归风险；或由学生向老师确认范围/规模是否允许明确变更；截止仍超则如实列未达。未取得人/老师新原话前不改统计根、阈值、功能或作自动放行。

来源：agents/backend/static-performance-next-measurement.md；agents/backend/bc5-contract-diagnostic/result.md；agents/database/pool-retention/result.md；agents/backend/pool-retention-compat/caller-handoff.md；agents/backend/dependency-query-candidate/report.md；docs/reviews/source-budget-decision-options.md。本轮只读这些公开开发材料，不读任何独立材料/860、不联系tester。首覆盖搜索误猜986_api.py路径exit2，随后rg --files确认真实986_http.py；不是测试或产品失败。
