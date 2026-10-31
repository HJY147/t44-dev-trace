# DirectP16 组件离线审核

范围：backend53acbb28、deployment2cf7e380、当时 QA direct-p16.PUBLIC。只读本地代码/PUBLIC文件；未SSH、云、Docker、SUT、PRIVATE或解密胶囊；没有重跑产品suite。用户取消额外准备工期/scan/horizon/grant轮次的授权优先，不将原门禁恢复为本次要求。

需要闭环两项启动顺序问题，已通知root/部署owner：

1. docker start 五个容器不保证 MySQL recovery/API/TLS已连接可用；立即 bootstrap 首SQL/TLS可能失败，签发流程不可盲重试。需要在签发任何session前完成有界基础服务连接就绪，或由总入口提供同等保障。不引入工期/业务资格/完整scan等待。
2. start.py 假设两个worker尚未运行。若VM启动时restart policy自动启动scheduler，atomic token替换后 docker start 对已运行worker无效，可能继续使用旧token。总入口/部署组件必须保证worker停止→初始化→原子rotation→start顺序，不通过完整scan等业务门禁替代它。

其余已核：bootstrap保存400映射/800互异旧ID与真实当前tasks/events，缺事件null，不伪造事件；metadata明确历史import而非当前完整源审计、旧manager/static字段未刷新；实际counts/ordered任务fixture哈希来自DB。123请求仅合成图观察，不保证真实分页数。TLS由原support原字节执行，默认gateway DNS tls-gateway/容器端8443，SNI/Host仍原origin，严格CA不弱化。四session实际读回，公有receipt不打印token，私有文件0600/exclusive失败前缀保留。

部署工具pins与接口对应，原token字节备份/fsync/原子替换/读回，失败停止链，无自动覆盖重试或VM关机。bootstrap写状态INIT_DONE仅表示直接初始化，不是测量成功。

QA PUBLIC delivery14项全部SHA核对通过；ENTRY与adapter原SHA不变。未读取测量runtime实现，因此400/60+600/原断言保留依据公开契约及固定原core哈希，不宣称本岗独立逐行核PRIVATE。DIRECT shell固定8CPU/8GiB/2048pids，docker非零也进入seal；seal固定manifest与原backup，14GiB tmpfs/29GiB可用内存/28GiB后处理与原树上界，未改测量8GiB。observer明确RUNNING400不是400并发HTTP/当前存活400/steady或指标完成。外层固定DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE，不得将原metrics PASS转成正式验收通过。

后续仍需审核root单入口的实际顺序、冷启动/worker问题闭环和最终包hash。当前本地11分钟演练尚未由本岗收取完成证据，不称通过。
