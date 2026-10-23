默认连接池只保留5个连接，溢出连接返还后可能反复关闭和新建。此独立候选仅把MySQLSettings默认值从5+10改为15+0，使标准每池峰值仍为15；不合入integration或替换bc5演示。

产品差异严格只有engine.py两行默认literal。其他应用、鉴权/锁/事务/超时/pre_ping/LIFO/rollback/UTC/RC、14冻结文件及原993/930/955字节不变。参数名/种类/字段次序保持；双显式override原样生效，partial size3从3+10变3+0（峰13→3），仅overflow2从5+2变15+2（峰7→17），因此不宣称全部调用者峰值不变。标准6默认池峰90不变，温态保留上界30→90；额外实例另预算，内存/FD/全局余量未知。

新增root预留869从真实Settings驱动实际QueuePool+合成DBAPI，覆盖借满拒绝、返还保留、第二波复用/溢出关闭及dispose；旧配置真实红是返还仅5而非15，候选10案例绿。真实lazy MySQL factory及原选项已离线核对，pymysql.connect未调用，无本机HTTP/SQL/压测。旧930硬5+10历史不改，单文件collect-only为0项/exit5；不把历史负载当作新候选已运行。

准确候选head db87d30449356f3473b645a5c246dcc6c21d7cbe已普通push，等待既有product完整托管检查；本draft PR按现有integration规则触发docker容器恢复一次。完整CI/覆盖分母/容器结果、准确cloc与Issue3/4读回随后归档；当前不预先声称通过，不复用旧CI或ABBA。CI后证据放独立分支，保持此PR head精确绑定。

Agent-Role: database (AI, not student manual edit)
Prompt-Ref: ROLE-database-POOL-DEFAULT-CANDIDATE-v1
Refs #4, #3
