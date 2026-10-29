# 本地先交付，原两机仅进入一次有限计算窗口

这个目录的工具只搬既有790密文，并执行原receiver/consumer；不改790源码、不重新登录、不造S2、不增加次数，不证明性能通过。部署岗未操作云。原预算/数据/接口由根提供实际值，禁止复制旧窗口实际凭据。

## 准备及配置

新路径建议`/root/t44-r9/opaque-relay-r29-01/relay.py`。两份`*.template.PUBLIC.json`默认不能运行：所有null字段由总协调填写实际值，JSON原始字节SHA写入下述命令。APP的`export_dir`是本轮原producer的全新输出目录；`producer_unit`是单次producer的精确systemd名称。`output_dir`是独立全新relay状态目录。LOAD的`load_configuration`仍是原790 LOAD配置，`receiver_sha256`及`consumer_sha256`从本次已装manifest取；程序会逐件核原manifest的全部文件、当前transfer pin和LOAD scope，不接受旧模板f89摘要。backend原594b08f0修正是这一取值规则的已提交依据；新29日manifest应由本次窗口负责人提供，不把旧2af/ba11硬编码到新配置。

共同的`source_sha/binding_sha256/root_grant_sha256/key_sha256/nonce`须精确相同。nonce是公开关联标识；保护来自精确LOAD源IP、私网监听、原CA/IP TLS校验、全片SHA和原OAEP/AES/HMAC解密，仅LOAD持原私钥。relay没有解密入口，也不会提供private/control/session文件。

`expires_at`限制TLS搬运窗口。独立`cost_stop_utc`不晚于计算窗口结束，建议设开机后45–50分钟，以给总协调阿里云保盘停机留余量；两者均必须在当前时刻后一小时内，expires不能晚于cost_stop。原330秒只检查790的`control.stop_utc`总窗口；600秒包年龄和四类真实session的expires仍由原代码分别验证。新工具的540秒成本余量是另外的条件：原consumer内部最多60秒解封+15秒mirror+300秒load，外层留420秒，异常时精确三cohort cleanup上限90秒，再留30秒落盘。因此不足540秒时不启动consumer，保已下载前缀，不能将其写成原业务或会话失效。

先用仅校验命令：

```sh
python3 -I -B /root/t44-r9/opaque-relay-r29-01/relay.py check --side APP --configuration ACTUAL_APP_JSON --configuration-sha256 ACTUAL_APP_JSON_SHA
python3 -I -B /root/t44-r9/opaque-relay-r29-01/relay.py check --side LOAD --configuration ACTUAL_LOAD_RELAY_JSON --configuration-sha256 ACTUAL_LOAD_RELAY_JSON_SHA
```

## 启动顺序

1. 根完成原GEN/budget/空库bootstrap/idle、资源collector+mirror、S1及原LOAD配置，预写所有命令；此时不签发S2会话。
2. APP先启动relay，建议精确systemd unit、Restart=no、RuntimeMaxSec不超过本次窗口、KillMode=control-group、日志落本轮私有目录。命令为`python3 -I -B relay.py app --configuration APP --configuration-sha256 SHA`。读取新`APP output_dir/APP-ready.PUBLIC.json`；其完整原子发布表明TLS监听已建立，核nonce/source/binding/PID与本unit MainPID再继续。
3. LOAD启动`python3 -I -B relay.py load --configuration LOAD_RELAY --configuration-sha256 SHA`，同样使用有限systemd unit。此时只应收到有界HTTP425等待，不会发SUT请求。
4. 根立即单次启动原APP producer。建议加`RemainAfterExit=yes`保留完成证明。APP relay仅接受producer `inactive + Result=success + ExecMainStatus=0`，或显式RemainAfterExit的`active/exited + MainPID=0 + success/0`；运行中或尚不存在仅425，失败即409。全部metadata/part/拼接gzip+raw hash通过后才发布固定内存快照。
5. LOAD自动收齐最多4片，完整校验，再按原CLI调用790_receive metadata/part；最后排他写CONSUMER_RESERVED后只调用一次原790_consumer。原stdout原字节写`consumer-once.stdout.PUBLIC`，stderr私有保存；顶层只有控制结果，不打印session。

不要把APP监听回执、425、解密完成、`ORIGINAL_CONSUMER_COMPLETED_NOT_FORMAL_ACCEPTANCE`或exit0当正式600秒通过。真实短测各cohort/原始错误/资源覆盖结论仍须另审。一个新目录不能使原matrix一次marker失效。

## 停机与费用

得到结果或失败立刻按原资源helper seal→镜像尾段核验→stop、原GEN owned stop保卷收尾，最后总协调在阿里云将两个**原**实例设为“节省停机”，核均已停止及自动释放`-`。本工具不删除数据、不释放实例，不会再开下一轮。原consumer超时/异常时本工具只对精确namespace三cohort名称、预期image及owner label一致的遗留LOAD容器作停止；身份不符不发信号，保留错误待根处理。

停止guest或停止Docker服务不等于停止按量计算费用。本工具无云账户权限，不能承诺阿里云账单自动封顶；一小时关窗及保盘停机必须由总协调实际执行并核对。若途中不能解决，先保盘停两机，再本地修复，不能保持空转。

## 已实际验证与未验证

初轮9项本地真实TLS测试4.327秒；随后只对受成本字段变更影响的原receiver/once路径、半响应断连及过期cost做3项窄复核1.743秒，其中1项重跑不重复计数，共11个独特场景。四片37KB合成不透明字节经真实TLS，再调用新29日原790_receive CLI导入，完整字节一致。原consumer仅被捕获命令，没有执行、解密业务包或运行压力矩阵。固定IP/CA、拒覆盖/部分文件/断连/路径/symlink/片SHA拒绝属于本工具本地证据。Python3.10仅静态语法验证；Linux/systemd/真实私网/云/SUT/性能均未由部署岗运行。
