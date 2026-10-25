# 公开 MySQL 成本与共享项目门：预准入交接

作者、代码/验证执行者：后端 AI。设计 baf1f9e，当前工具 checkpoint 416866688d2153d97664f9f7e062537fd1386ab8。产品零改动；root/限定审核准入、真实 MySQL 并发及收益均 PENDING。

## 已核公开原件

root 核官方 ZIP 后发布的 CI 40169575755 / head81c909 mysql-before.json；本岗实读 SHA b17f0fd502f9342ec11f9ae12064edccb11f139b3a90997c6be022f5ec333a9e。离线分析 source9f7643c / exit0，之后 e97cbeb 只改格式，未把新源码冒作旧执行；完整输出 mysql-before-summary.json。Linux/Python3.12.15、FastAPI0.161.1、SQLAlchemy2.1.6、jsonschema4.26.0、referencing0.37.0，DB observer4edbf…；四路径各12 measured，与4 warmup和4 profile分开，56均200、cleanup_errors空。

下表为普通样本中位数，单位ms。Rows与cursor是重叠的inclusive层，不能相加；响应校验仅parent_id=0，未把请求校验混入。

| operation | handler CPU | client墙时 | 响应schema CPU | Rows CPU/墙时 | cursor CPU/墙时 |
|---|---:|---:|---:|---:|---:|
| getTask | 6.998 | 10.881 | 0.879 | 3.930/5.440 | 1.657/2.972 |
| listTasks(20) | 20.508 | 24.905 | 11.711 | 5.363/7.165 | 2.238/3.873 |
| transitionTask | 17.261 | 25.357 | 0.959 | 10.313/14.380 | 4.765/8.785 |
| validateContractPayload | 3.226 | 6.149 | 0.247 | 1.569/2.158 | 0.676/1.172 |

list响应校验占handler CPU约57%，全部构造器仅0.136ms；不能只缓存构造器推定可解决。transition的Rows26次、cursor28次含savepoint，原三认证/两UoW不减少。Runtime exclusive包含DB调用，不是纯业务调度；profile-only的TLS大值受profiling开销影响，不能作为普通请求或云根因。此轮顺序数据不证明项目X锁造成原云慢请求，global ref原型小路径无一致改善，继续不合入。

## 拟候选与开发验证

设计详见design.md：仅graph_lock内的一处project lock参数，_PROJECT_LOCK仍X，START/UNBLOCK/REWORK为S，成员S、ordered target+pred X、三个认证点、两UoW、CAS、错误/审计/outbox/幂等保持。S不升级，图/成员/iteration/assignment writer全X。实际锁序不能只由ORDER BY文本推导。

DB岗拥有低层真实Runtime/EXPLAIN/P_S驱动；本岗tmp/834_shared_gate_http.py另有7个真实HTTP开发case，均只collect，**尚未执行MySQL**：不同START同时到业务、图writer实际projects等待边、前驱真实ROLLBACK后START/DEVELOPING-UNBLOCK拒、capacity/manager-role写先提交后REWORK拒、同版本START一成一VERSION_CONFLICT。实际等待须有精确req/block connection及projects/tasks资源；pause仅原locked_scope之后的Business.dispatch，或在原locked_scope调用前记录当前连接ID，原业务不替换。

HTTP驱动只CI=true及显式allow、localhost且非13306、独立空`t44_gate_http`，root先迁移；自身无DDL，不读旧env/token，账号由原初始化及API，token只内存。要求HEAD和3个实际源码逐字Git匹配、DB helper SHA匹配，输出O_EXCL|O_NOFOLLOW0600，报告不含Token/DSN/SQL正文/LOCK_DATA。仅诊断连接加innodb_lock_wait_timeout=5，明确记录，不变产品连接配置。fixture清理每项独立尝试、原异常不被覆盖，失败不冒绿。

先做真实SQLite顺序fixture校准，仅验证输入/正常业务链/原错误/拒绝副作用：初2项1红1绿，capacity=[]违反冻结minItems1，**不是产品缺陷**；保留红log/XML。仅替成另一有效developer容量并保留reviewer非任务owner的独立评审角色后，2项绿。新增UNBLOCK顺序fixture仅该1项绿/其余2deselected，没有把重复角色例累计；当前3个唯一fixture目标已绿，MySQL7仍未运行。Ruff首B905红后strict=True修正；分析器首format exit1后单独格式修，均不冒首轮全绿。两次patch上下文不匹配未部分改文件，后按实际上下文修。

## 精确执行接口与规模

root准备的独立schema `t44_gate_http`，环境：CI=true；T44_GATE_ALLOW_MYSQL=true；T44_GATE_EXPECTED_SOURCE=实际CI HEAD；DATABASE_URL与T44_DATABASE=t44_gate_http；T44_GATE_DB_PROBE=tmp/833_database_performance/833_mysql_lock_probe.py；T44_GATE_DB_PROBE_SHA256=46dc00a57ff79ec51c0d8bcc92dd32c5bdcb76e794c8c9417c89bbb2c42256fb；T44_GATE_REPORT=新不存在的JSON文件。执行 `PYTHONPATH=backend python -m pytest -c backend/pyproject.toml tmp/834_backend_performance/834_shared_gate_http.py -q --tb=short --junitxml=<新文件>`。root统一一次fresh CI，本岗未触发CI/云/本地MySQL。

当前tmp三文件为113+663+137=913物理行（含空行注释，**不是cloc**），均是新增诊断/开发测试。产品/backend/frontend/deployment/合同DDL对d60/ade5逐字未变；正式原口径6316、超1216仍失败，未新cloc，实际产品节省0。拟一处表达式可能增加产品行数，只有准入后实际固定cloc才可报告，不能以测试排除制造达标。

后续：root/审核准入后才写生产参数；必要邻接回归和fresh MySQL真实并发均须新源绑定。此前formal 600秒0组、270ms/零错、502根因、规模达标和独立验收都不因本阶段通过。原78bb及清理E/raw保持，未读独立829/839/841/852私件，不联系测试岗；本记录不能算学生手写研究报告或用户亲自改码。
