# 默认池15+0独立候选：范围先行

数据库AI；ROLE-database-POOL-DEFAULT-CANDIDATE-v1。新分支codex/database-pool-default-candidate从root5408c05377d4f0084c6ae4eb596351add2004b67建立，含完整ABBA及backend445015f一页交接。依据root ac826cb9a788992297fe27d547bfcc208f83f1bc RFC；已实际GET Issue4评论6376569009，原文backend-input.json。此设计checkpoint未改产品，不合入integration或替换bc5演示。

## 唯一产品差异与调用者契约

只将backend/t44/persistence/engine.py的MySQLSettings.pool_size默认5改15、max_overflow默认10改0。除此之外整个生产树零字节差异；不增逻辑、配置开关/映射/依赖、表/API/DDL/14冻结件。参数名/种类/字段次序不变，构造默认值仅这两处有意变化；显式参数仍按原构造规则生效。

| 构造方式 | 原值/峰值 | 候选值/峰值 | 影响 |
| --- | --- | --- | --- |
| 两参数均省略 | 5+10/15 | 15+0/15 | 标准默认每池峰值不变，更多保留 |
| 仅pool_size=3 | 3+10/13 | 3+0/3 | partial override峰值明确改变 |
| 同时size=3/overflow=2 | 3+2/5 | 3+2/5 | 双显式override完整保留 |
| 同时size=5/overflow=10 | 5+10/15 | 5+10/15 | 旧配置可显式保留 |
| 仅overflow=2 | 5+2/7 | 15+2/17 | 另一种partial override也受默认影响；不宣称所有调用者峰15 |

Settings.mysql_settings只传凭据/数据库，所以API LazyFactory、CLI、MQ/scanner继承候选默认，显式factory独立；不声称现有env/DSN-query支持池覆盖。标准4API+1MQ+1scanner六默认池理论峰仍90，温态保留上界30→90，最多多60闲置连接；按需建连，不启动即建满。CLI/健康/迁移/备份/滚动实例另计。服务端内存、FD和全局余量未知，不套一次151快照。

auth/session/member实时检查、撤销锁、session→idem→project→members→task锁序、CAS/幂等/audit/outbox/提交不明分类，及timeout/recycle/pre_ping/LIFO/reset rollback/UTC严格mode/RC/隐藏参数均保持原字节；代码不变不保证相同负载错误分布或503消失。旧正式失败、6307超1207和人工材料缺口不改写。

## 有意义的新增模块回归及历史保护

root已正式预留tmp/backend/persistence/869_pool_defaults.py（next868），仅本阶段使用。原993全部断言及930_contract_abba.py硬5+10历史工具原字节保持，不以改历史断言凑绿；955 ABBA及其原件不改/不重复。

先在旧配置运行新增default目标真实红，验证实际QueuePool返还只能保留5而非候选15；再实施两常量。869从真实MySQLSettings取配置驱动实际SQLAlchemy QueuePool+合成DBAPI：借满→额外借用拒绝→返还保留→第二波复用/溢出关闭→dispose全部关闭；覆盖上表构造方式。合成池仅测试边界使用即时timeout，生产原10秒超时由真实engine构造选项另核；无HTTP/SQL/真实连接/压测。另从真实Settings组合根到lazy create_mysql_engine核实际池参数和原选项，防止只镜像常量。既有原测试不改，完整suite由托管真实MySQL/MQ执行。

## 精确源、规模与一次托管触发

设计先commit；产品checkpoint包含两常量/869/必要记录，普通push触发一次product完整工作流；同一精确head创建面向codex/integration的draft PR，按既有workflow只另触发一次docker-application容器恢复工作流（product PR规则不匹配该base，避免重复）。不重跑既有负载或正式协议。实际run/head/PR合并快照及覆盖分母/未测源、故障/容器结果逐项绑定，任何失败保留再窄修，不预写通过。

原固定source_count.py/cloc2.10基线5408c05实测6307/--require-range退出1，候选预计有效行不变，提交后实测。AST/字节核对严格只有两个default Constant节点改变；冻结14、原993/930及其他生产文件逐字相同。CI后证据在独立evidence分支归档，保留candidate PR head精确等于已测SHA，不因记录push再次跑CI或用旧检查冒充新head。

最终交付准确候选SHA/draftPR、两工作流真实状态/原件、cloc和Issue3/4精确GET读回；只交候选不合root。准确源专审与后续盲测/生产准入由root另调度。
