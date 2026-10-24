# 连接池默认候选：后端调用者一页交接

后端AI静态意见；范围先提交e534dee，依据root ac826cb9 RFC。候选尚未在本岗实现/运行；当前生产仍bc5，ff7诊断不改。本轮只有源码阅读/AST/本岗文档与GitHub公开对接，0业务HTTP/SQL/测试/负载。

| 调用入口 | 真实传播与兼容边界 |
| --- | --- |
| `settings.py:37 mysql_settings` | 仅传host/database/user/password/port；没有pool env/CLI/DSN-query映射。候选默认会传播到API/CLI/MQ/scanner；显式factory注入仍使用提供者自己的engine，不被Settings覆盖。 |
| `api.py:180 LazyFactory` | 每应用/worker首次UoW构造一个engine并复用factory，初始化锁保留；不是每请求新池，也不启动即建15连接。 |
| `cli.py:50`、MQ `__main__.py:28`、scanner `__main__.py:67` | 各次入口创建engine；MQ/scanner有finally dispose，CLI没有显式dispose（正常独立进程退出回收，若同进程重复main另需生命周期预算）。账号/撤销/迁移/seed/服务token和两个worker均继承新默认。MQ网络调用在DB事务外、scanner max_instances=1等原边界不变。 |
| 8处直接`MySQLSettings`构造 | AST清单见static-receipt.json。985/988/MQ fixture/956/975显式凭据路径不传pool，采用默认；scheduler私密字典`**private`可能显式给池字段，不能不读值却断言没有override（本岗没读该私密文件）。 |
| `993_foundation.py:249` | 只给pool_size=3；候选成为3+0，旧3+10，峰值13→3。原断言只核size3，不能证明两参数override。直接SQLite fixture的1+1与本候选无关。 |
| `930_contract_abba.py:161` | 历史4c/5dcb工具硬要求5+10，应原样保留；不改断言拿候选凑绿。955动态记录实际值，ff7历史原件保留。 |

**代码语义应保持，但可用性结果未证明相同。** 两默认之外须零差异：构造字段/显式两参数override、timeout10/recycle1800、pre_ping/LIFO/rollback-on-return、UTC/严格mode/RC、隐藏参数/参数化查询。实时session/user/member鉴权及auth-before-input顺序不改；连接复用不缓存身份。session→idem→project X（需时）→有序members→有序tasks、CAS/幂等结果、成功audit/outbox原子性、失败主UoW退出后独立audit、真实commit确认丢失的CommitUncertain分类均不改。撤销CLI仍session X，写请求session S，普通读RC语句快照不改。

有连接且独立拒绝audit可落库时原401/403/409等仍由原逻辑裁定；池获取/DB故障可先使读取未完成，或使独立audit失败，沿原PersistenceUnavailable→DEPENDENCY_UNAVAILABLE/AUDIT_UNAVAILABLE返回503。commit不明确仍TRANSACTION_UNCERTAIN（有idem）/DEPENDENCY_UNAVAILABLE（无idem），后续rollback仅清理。不能声称池配置令401绝不变503、503消失、重连/撤销时序等价已实测；本轮未注入故障。

**预算与未知代价。** 标准4API+1MQ+1scanner共6池，默认峰值均15，总理论90不变；温态保留上界由6×5=30升6×15=90，多最多60闲置连接（按需增长，不预建）。CLI/健康/迁移/备份、额外engine或滚动重启/重复实例另算；非标准partial override峰值会改变。数据库端内存、client FD、stale连接/重连频率、全局max_connections与其它客户余量本轮均未知；不能套单次151快照。DB岗公开ABBA的四短段0错/P95与重建同向只支持开发候选，不代正式因果/新候选CI/故障通过。

**交接出口。** Issue4具体要求6376569009已发表并读回；DBowner实际消息确认目前只有9d1deff/e03a95c诊断，无默认候选SHA，并已收到partial override关注。后续需DBowner独立两常量源、准确候选全量CI/全部生产覆盖分母/容器恢复和专审；原测试/930历史不改，本轮不预先判通过或合入。固定6307/超1207不变，未新计数。技术上未发现必须改后端API才能试候选的阻断，资源与故障验证仍是明确待项。
