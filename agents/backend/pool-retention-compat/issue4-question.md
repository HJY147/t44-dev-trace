Agent-Role: backend（AI静态审查，非学生亲改）
Prompt-Ref: agents/backend/POOL-RETENTION-COMPAT-dispatch.md

对root ac826cb9的5+10→15+0默认候选提出具体兼容要求；本岗没有运行本机SQL/业务HTTP/负载，未修改生产或旧测试。

1. 请DB owner在候选实际派工后仅改MySQLSettings两个默认常量，保持字段次序/构造签名和显式两参数override。Settings.mysql_settings不传pool参数，因此API LazyFactory、CLI、MQ/scanner均会采用新默认；没有新env/CLI pool开关，不能宣称现DSN query已能覆盖pool。
2. 部分override是明确可见差异：993_foundation.py:249仅pool_size=3，max_overflow省略，会从3+10变3+0，峰值13→3；不是所有调用者都“峰值不变”。原测试只断言size3，不能冒称证明了两参数override或改原断言凑绿。显式同时指定pool_size/max_overflow应原样保持。
3. 旧930_contract_abba.py:161硬要求5+10，是固定4c/5dcb旧对照；不得改其断言/历史原件来接受候选。955记录动态配置，本岗ff7数据保持原字节；候选另有准确源CI/专审，不能复用旧930/ABBA为通过。
4. timeout10/recycle1800/pre_ping/LIFO/reset-on-return rollback/READ COMMITTED/UTC/严格mode/隐藏参数及错误映射、Engine按需连接必须保持。资源获取失败仍可能在完成鉴权前变503，独立拒绝audit拿不到连接仍AUDIT_UNAVAILABLE；不能保证同一负载仍返回相同错误或503归零。撤销/实时membership、session→idem→project→members→task锁、CAS/原子audit/outbox/结果、commit-ACK不明保护不得因候选弱化。
5. 四API+MQ+scanner的默认理论峰值6×15=90不变，但温态保留上界30→90；CLI/健康/迁移/重复实例/滚动重启另计，DB内存/FD/其它客户端及服务器max_connections实际余量未知，不能套一次151快照。MQ/scanner当前各独立engine，按需建连不等于启动建满。

DB owner已实际消息确认当前只有ABBA诊断9d1deff/e03a95c、尚无默认候选源码/SHA，并收到部分override关注；其公开ABBA评论6376531906已由本岗实际GET。以上是下一阶段兼容输入，当前不写成候选已通过/已合入。请在你下一阶段实际派工后答复两个默认之外是否确实零差异、partial override边界及准确候选源；无需重复ABBA或本机负载。
