# 会话签发前启动的密文交接

目标是消除四片密文的人工GUI搬运，不改变既有 `790_receive.py`、`790_consumer.py`、HTTP矩阵、600秒包年龄、四会话真实到期或330秒总窗口检查。旧窗口没有跑出压力结果，不改旧回执。

APP先运行只读TLS relay，LOAD先运行有绝对截止的等待器，随后总协调单次启动原producer。relay只允许指定LOAD源IP、固定nonce路由，仅在原producer systemd unit终态success后读固定metadata及0–3片；逐件及拼接gzip/raw SHA通过后固定内存快照，拒绝目录列表、任意路径、symlink、私件与半成品。无SUT明文、无目录扫描、无新云权限或SG变更。

LOAD用原CA验证证书与IP，从自己的固定私网源地址连接。只有HTTP425表示未ready可以有界轮询；网络/TLS错误、畸形、过大或不符scope即终止保留前缀。所有片完整核对后才调用原receiver，随后消费器仅一次。新目录与原matrix marker拒绝覆盖或重启；不登录、不续发会话、不生成S2、不自动开启下一轮。

两端配置必须由总协调填写实际新source/binding/rootgrant/recipient/nonce/窗口与路径，再由完整SHA锁定。代码SHA、原manifest及原LOAD配置均现场核对，不能拿模板旧摘要补空。代码只依赖Python3.10标准库；本地回环TLS测试是合成密文，不是云或SUT验收。

一小时云窗由总协调负责阿里云“节省停机”确认；guest shutdown或停止应用不证明计算费用停止。此工具不会启动/购买VM或修改自动释放。配置绝对截止只约束relay/consumer，并不替代原两机保盘停机责任。
