# P13 / PL1直接正式复测

本轮产品source90b和七个运行镜像、已应用索引不变；用户报告应用机0mt原云盘已升级ESSD PL1、40GiB、3800IOPS。现场有效配置及盘ID尚待读回。没有追加AB实验。

## 开机前

核验本包READY_MANIFEST.PUBLIC.json中全部文件SHA、归档字节和语法；本包不含真实账号、会话、许可、测试私钥或PRIVATE用例。仅在总协调已完成本地准备后启动原实例；公网IP变动时使用原主机公钥绑定的SSH更新工具，临时授权过期则按原USER_ONLY脚本重新安装，不能关闭HostKeyChecking。不要让64核应用机等待SSH排障。

## 开机后

1. 验证原主机指纹和当前授权余量，核对原APP64核/LOAD16核与实际容器、镜像、资源边界。读回APP真实MySQL卷/挂载点/块设备映射及云盘PL1事实，更新中性身份资料；用户回报不冒充现场核实。
2. 仅用本轮RUNBOOK及run入口生成r30materialresume06 / r30restoretransition06的新材料。保持800原任务资格、真实会话有效期、schema与source/bundle/import精确绑定及原维护的完整写前预检；旧输出不可覆盖或删除重跑。
3. 把当前中性资料交新独立测试实例审核。qa/公开接口只允许身份及零SUT prepare；真实一次grant须待当前资料与实际prepare回执复核，不能给旧批准改名。
4. 新run r30manualp13按原ENTRY一次运行，仍为400客户端、60秒预热、600秒稳态、P95≤270ms、每分钟吞吐≥1000、零业务错误及全部原断言。coordinator/dispatch_once.py只封装原ENTRY，不更改测量工具。同步采已有受限IO观测，不增加独立磁盘压测或额外AB。
5. 执行退出、所有写入停止后按qa/公开接口密封原workspace，下载密文及receipt核SHA/bytes、回收APP中性观测；及时通知用户原VM可节省停机，保留磁盘数据。独立解密与判定在本地进行，FINISHED不是PASS。

身份、会话、输入、schema、排他性或资源事实变化则重新审核。旧p12及其grant已消费，绝不再次启动。本地准备通过不等于现场、正式压测或性能通过。
