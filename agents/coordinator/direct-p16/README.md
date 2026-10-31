# 下次开机后的单入口

准备状态以READY.PUBLIC.json为准；必须READY_FOR_USER_BOOT才通知用户开机。服务器当前由用户关闭，本轮只本地准备，未连接服务器。原P15没有开始正式压测，其失败和中断记录保留。

用户开启原两台并给当前公网IP后，总协调只运行这一个命令：

```sh
python3 /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/global-latency-repair-20261031/agents/coordinator/direct-p16/after_boot.py --app-ip 当前0mt公网IP --load-ip 当前0mu公网IP
```

不再跑旧p15准备、maintenance、重新排期、完整工期门槛、等待完整scan或人工签发检查。单入口并行安装预打包小工具与启动既有服务；APP正常初始化登录/读取当前版本，原子更新后台凭据；公钥CMS运输后LOAD直接原400客户端/60秒预热/600秒稳态。基础连接尚未就绪时程序会在签发会话之前有界等待，不重试已签发写入。生产源码bcec不改；新mode为诊断压测，明确不冒称原完整准入正式验收。API时间、鉴权、原测量/后置断言不删。

原始请求完整保留，诊断缺失为UNKNOWN。同一轮稳态early/late只读采样CPU/worker及数据库，原sampler字节不变。外部控制日志置W外，防封存时外部写者；原测量结束后自动在14GiB tmpfs用28GiB后处理内存封存，不在原磁盘额外复制12GiB。原指标FAIL/NP仍回收密文。APP采样回收后先报告APP_EVIDENCE_RECOVERED_CAN_STOP_APP，立即通知用户先停64核APP；Mac核LOAD密文bytes/SHA完成后立即报告EVIDENCE_RECOVERED_CAN_STOP_BOTH_SERVERS，再立即告诉用户停LOAD；本地独立解密/判读继续，不占服务器费用。没有VM关机命令/倒计时/云stop/自动新轮次。

只可执行r30directp16一次。初始化或运行失败保留prefix，不盲重试启动；读取公开阶段失败不影响已启动测试的等待和最终回收。若缺关键文件/密文或hash不符，不能假称结果已回收，立即说明真实状态及可停机范围。tmpfs密文在下载核完整前不得停LOAD。用户主动停机则立即停止本地SSH调度，不尝试自动恢复。

保留原主机pin和永久restrict密钥，私钥不复制到LOAD/APP；Mac只中转公开cert及密文，不读取测试PRIVATE或明文token。旧包p14/p15/grant不可用作新mode成功证明。
