Agent-Role: backend（AI只读兼容审查）
Prompt-Ref: agents/backend/POOL-RETENTION-COMPAT-dispatch.md

范围先提交e534dee，已按root ac826cb9 RFC完成后端调用者静态审查。当前本岗生产仍bc5、无候选代码、未跑SQL/业务HTTP/负载/pytest，ff7诊断原件/冻结规格/旧测试均不改。

Settings.mysql_settings只传凭据/库，API LazyFactory、CLI、MQ和scanner都会继承默认15+0；显式factory/两参数override仍由提供者决定，没有新pool环境或DSN-query映射。发现两个实际边界：993_foundation只显式pool_size=3，省略overflow将从3+10变3+0（峰13→3），原断言只核size不能证明两参数override；历史930:161硬要求5+10，不能为候选改它/旧对照结论。CLI无显式engine.dispose，现独立进程退出回收；MQ/scanner有finally dispose，同进程重复CLI调用的额外engine不能从预算中漏掉。

鉴权/401角色裁定、session/member撤销、session→idem→project→members→tasks锁、CAS/幂等、主成功audit/outbox原子及拒绝独立audit、commit-ACK不明语义均须保持原代码；不等于相同负载会返回相同错误。池获取/DB故障仍可能在auth完成前或拒绝audit时沿原分支503，不承诺503消失。标准4API+MQ+scanner总默认峰90不变，但温态保留上界30→90，额外CLI/探针/迁移/滚动重启另计，内存/FD/全局连接余量未知，不能套一次151快照。

已向DBowner提出具体要求并实际读回：[Issue4兼容输入](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6376569009)。DBowner实际消息确认目前只有9d1deff/e03a95c ABBA诊断、尚无默认候选SHA，已收到部分override关注；其公开ABBA评论6376531906/6376532216已实际GET。候选源码/准确源CI/专审/是否合入尚待，不能把这条静态意见当通过。完整一页：agents/backend/pool-retention-compat/caller-handoff.md，AST8调用点：static-receipt.json。源码固定6307超1207仍未解决；本轮作者为AI、不是学生亲改。
