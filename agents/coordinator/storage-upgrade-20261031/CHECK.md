# 应用机云盘检查与直接复测交接

用户要求直接升级后正式复测，不再安排额外对照实验。

已复核上轮公开telemetry-deltas：API早晚窗口约13.10/11.77核，全部64核可用、无CPU节流；MySQL设备259:0写入2073.33/2067.10次每秒、49.87/48.64 MB/s。数据来源及原字节SHA见CHECK.PUBLIC.json。部署app-campaign.py配置mysql_data:/var/lib/mysql。这证明配置使用持久卷及该设备承担MySQL IO，旧材料未保存真实卷挂载点到云盘ID的映射，不能将映射称为已验证。

用户提供应用机唯一块存储为ESSD PL0 40 GiB / 2280 IOPS。磁盘瓶颈是有依据的候选，尚非已证实根因；cgroup操作计数与供应商计费/限流计数不能直接等同。不能将约91%称为精确磁盘利用率。

最小升级候选：应用机原40 GiB云盘PL0→PL1，不扩容量，标称IOPS2280→3800、吞吐110→140 MB/s。PL1并非固定50000 IOPS。升级后按新级别计费，普通变配不支持降回PL0。本轮没有实际修改云资源，缺少浏览器控制工具；升级价格、任务及最终状态尚未核实。

控制台核对应用机i-bp13uag4r4u9r2hge0mt当前附盘ID与40GiB PL0，再选择修改性能级别PL1；不改压力机盘。可在实例已停止时操作。最终回执记录盘ID、容量、PL1、IOPS、吞吐、完成状态。

复测沿用r30manualp13 / r30materialresume06 / r30restoretransition06，但必须核实这些路径尚未消费且当前候选身份有效；旧p12不得再执行。原400客户端、60秒预热、600秒稳态、P95≤270ms、每分钟吞吐≥1000、零业务错误和全部原断言不变。先完成候选相关启动包/工具本地复核，再通知用户开机。开机后只补当前主机/磁盘/实际数据卷映射、会话及独立准入；正式运行同步采已有IO观测，不添加独立对照压测。完成后回收证据并及时通知用户节省停机。

官方依据：
- https://www.alibabacloud.com/help/zh/ecs/user-guide/essds
- https://help.aliyun.com/zh/ecs/user-guide/modify-the-performance-levels-of-essds/

状态：离线检查完成；云盘升级、现场映射、当前准入、正式复测均待执行。
