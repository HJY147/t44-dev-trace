# 有界只读运行用量快照：中性环境补充设计

作者：协调AI。来源是独立岗位只提出的环境能力需求，不包含其私密案例、负载细节或预期结果。先形成接口设计，再由部署岗实施；当前文档不表示能力已经可运行。原14件冻结、应用及正式性能阈值不变。

## 范围和接口

新增无参数 `control.py runtime-usage`，仅观察本次Compose项目固定mysql/rabbitmq/api/consumer/scheduler/web六服务。沿用已验证的项目、唯一64位container ID及project/service标签校验，拒绝任意容器、命令、路径、SQL和参数。不能请求完整inspect、进程argv、环境或凭据。旧runtime-metadata命令与其完整性规则保持。

采用一次有界Docker CLI stats调用，显式传六个已验证ID，`--no-stream --no-trunc`，固定Go模板只输出ID及CPUPerc/MemUsage/MemPerc/NetIO/BlockIO/PIDs。命令stdout/stderr只在内存白名单投影，不进入公开控制日志或保存完整异常；容器不运行、缺行、重复、外来ID、格式错误、超时均保留unknown/失败，不按零填补。返回stdout始终单个JSON；退出0仅代表六项观察完整，非零代表不完整，不是业务或性能判定。

JSON版本1固定顶层：`schema_version, observation_complete, started_at_utc, finished_at_utc, services, limitations`。services为上述六名对象，每项固定 `container_id, observed, sample_started_at_utc, sample_finished_at_utc, cpu_percent_cli, memory_usage_cli, memory_percent_cli, network_io_cli, block_io_cli, pids_cli, error`；值保留Docker原单位字符串，不凭格式化值伪造字节精度。失败观测值为null，error只用稳定白名单码。时间表示调用包围窗口，不声称六容器原子同刻取样。须公开文档列举成功与不完整样例及这些准确字段。

run.py仅在context新增runtime_usage能力声明，不自动采样、不改产品启动资源或负载；由tester独立决定采样时机并私密取回。采集墙钟耗时和负载影响不能被认为不存在。若适配当前Docker实际格式需要修改合同，先显式补本RFC并通知中性调用方，不能悄悄换字段。

## 解释限制

Docker CLI的Linux内存用量扣除缓存，不是RSS；PIDs包含内核线程，不是进程数。网络/块I/O是格式化累计量，不直接等于每秒利用率或真实物理设备耗时；CPU百分比的Docker采样窗口不等于整个600秒窗口。单次或前后快照不能证明全程峰值、其他流量来源或物理同机。RSS仍属未提供能力，不用working set冒名。

以上语义已核官方[stats命令文档](https://docs.docker.com/reference/cli/docker/container/stats/)，资源限制与实际用量应区别，见[官方资源约束](https://docs.docker.com/engine/containers/resource_constraints/)。不以未设置限制推断无限硬件。

## 验证和交付

先设计、再实现、新测试编号由总协调预留。仅对ID/标签校验、六项完整与缺失/重复/外来/错误格式/超时/稳定错误/无秘密投影及旧命令兼容做必要合成守卫；没有本机Docker时不冒称真实stats已经运行。保留原失败并Ruff按现有CI配置。真实观察是否完整由后续准确环境绑定及tester本轮实际调用验证，不回填过去正式运行的unknown。

实施、真实测试结果、来源hash、局限、Issue7实际交接及明确代码SHA由deployment岗位封档。它是中性运维工具，既不算生产源码削减，也不等于应用压测或独立验收通过。
