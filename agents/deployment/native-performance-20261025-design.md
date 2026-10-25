# 第二独立原生性能环境准备（未准入应用）

2026-10-25部署AI，root明确源c8cea7e82805de5283ce67501769fa9a4efc1047，目标仅新t44_p829_20261025和指定performance-db/application-env.json。既有functional运行不改、不停；不得读取admin、identities或任何独立目录。新API18097/8worker、AMQP25697/EPMD24397/dist35697/CLI45716–45725均先bind检查空闲；独立performance父目录、新run/Cookie/user/vhost/CA。

从固定已审本岗模板逐字派生，输入只准functional/performance两组精确配置，本次仅performance。每个模板旧Git SHA/文件SHA、每项允许文字替换及次数、输出SHA留清单；不改任何原文件、旧run/controller或初始buildmanifest。新baseline prepare也为c8，应用worker argv和实际8worker检查一致；源/锁/私有文件/拥有权/认证/停止逻辑不变。应用08:46:30、broker08:47、08:50总上限不延长，08:45后不启动新进程。

先真实prepare、new broker/guardian、绑定c8和prestart build（processes为空且不能当运行准入）；未获root确认functional结束/旧functional DB连接已停前不启动API/consumer/scheduler。数据由DB岗负责，不猜datasetIDs/不seed/不修改业务；新scope由root真实CLI签发实际P1。正式native-build在实际启动后新文件一次冻结，prestart不改标签。

只使用新appenv连接只读max_connections/Threads_connected/Max_used_connections元数据，连接随probe结束关闭，不改MySQL配置。API8*15=120是源码pool最坏容量，不是当前连接；两辅助engine各15最坏总150，实际单线程使用更低仍须观察。保护的其他客户端/探针/余量须列出，不能把max_connections和当前低连接当吞吐通过；最终是否运行由root phase准入，性能/独立通过/实际停机和回收均待真实后验。新增门禁测试用tmp/819_native_performance，不能读私有用例。
