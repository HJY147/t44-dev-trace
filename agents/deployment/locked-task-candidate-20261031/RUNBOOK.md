# 第二候选离线镜像准备与现场边界

准确源13acb43a804e717e7485091895378511fe3d9b76，产品字节为a59a90a1；13ac只维护两项开发测试查询预算。原90b镜像不能作为新产品运行。build run41111887081只构建和封装，不启动SUT，不批准上线或性能验收。

构建通过后下载final-dual-13acb43a804e717e7485091895378511fe3d9b76-41112638628，保存到主树.submission-private/build-candidates/locked-task-13ac-20261031；对backend-bundle-manifest.json求独立SHA，再用构建ref e523bf08的deployment/cloud-reuse/final-image-bundle.py verify复核压缩包bytes/SHA、解压SHA、linux/amd64、官方固定上游及backend/web准确revision/archive label。此verify不调用Docker；现场load需实际核config ID，不能用本地静态核验冒现场加载完成。

## 现场前置，尚未执行

两台原VM均由用户关闭。不得请求现在开机，仅在root完成完整CI、审查和新中性测试准备后由root告知。开机后重新验证SSH原hostkey、当前IP/授权、当前磁盘空间、原数据卷/schema/索引、现有服务镜像及资源配置。镜像load要求Linux amd64及12GiB空闲，先确认40GiB原盘当前真实余量；不得擅删旧镜像、卷或历史证据腾空间。

保持原64CPU应用机worker/线程/连接池现场配置及原400客户端、60秒预热、600秒稳态、P95≤270ms等要求；新bundle仅提供镜像overlay，不提供资源配置。新源升级须先显式组合新镜像overlay与原已核资源/TLS配置，使用no-build/pull-never，严禁误用仓库默认值覆盖现场配置。七角色包不代表必须重建数据库/消息卷。

p13已完成且NP_NOT_ACCEPTED，旧run/material/grant均已消费；下一轮必须由root按新源取得新的中性材料与独立准入，不能复用既有grant，不自动创建后继试验。测试退出、相关写入停止及证据回收核验后立即告知用户手动停机，不配置任何自动关机或云stop定时器。旧resume-source-package的stop_utc接口本轮未执行。


## 新源替换入口（只读planner已准备，现场尚未执行）

`deployment/cloud-reuse/locked-task-plan.py`从原七角色公开快照、现场Docker inspect和明确原Compose配置文件构造计划。必须传当前完整渲染config的root核准SHA，不接受猜测配置。它只读Docker，不load/stop/start/up；保存完整inspect至0700目录的0600 PRIVATE文件，不输出Env或Cmd秘密。新旧overlay均只指定api/consumer/scheduler/web镜像，不改变其它配置；生成命令严格no-deps/no-build/pull-never，保留mysql/rabbitmq/tls-gateway。

示例（所有CURRENT字段是现场事实占位，不是已验证值）：

```sh
python3 deployment/cloud-reuse/locked-task-plan.py   --expected CURRENT_SEVEN_PUBLIC_JSON   --package NEW_DOWNLOADED_PACKAGE_ABSOLUTE_DIRECTORY   --manifest-sha256 414e3069bddc03adedea3671cb5de7c9382f46f9f44bb77799c5cc7112856bd7   --directory CURRENT_ORIGINAL_COMPOSE_WORKING_DIRECTORY   --config CURRENT_ORIGINAL_COMPOSE_CONFIG_ABSOLUTE_PATH   --rendered-config-sha256 ROOT_REVIEWED_CURRENT_RENDERED_CONFIG_SHA256   --output NEW_ABSOLUTE_PRIVATE_PLAN_DIRECTORY
```

多配置文件须按原顺序重复--config。原config/工作目录从现场原标签及受控历史资料读回，缺失或变更必须拒绝，不能临时用仓库默认Compose替代。若原容器当前Config.Image与渲染配置不符，本planner拒绝并交root核原overlay，不自行修补。

在执行生成的apply命令前，root须先核原渲染配置与inspect完整Env/Cmd、worker/pool、限制、卷/挂载、网络/端口、健康检查和restart policy一致，原回滚镜像仍在；暂停原发压和相关旧worker写入，保留准确旧镜像与私有快照。用e523构建ref的原final-image-bundle.py import接口加载并取真实receipt，它不会启动业务服务；先核下载包和导入证明，再执行明确计划命令。planner不代替import或此现场完整一致性核对。

替换后重新观察全部七角色，核基础设施ID/卷不变，应用镜像ID为本包、平台/实际source/runtime正确，Env/Cmd、worker/pool、限制、网络/挂载/TLS/健康与原配置一致；原resume脚本硬钉旧七ID，不能用于替换后的成功声明。旧scheduler服务会话自然可能过期，需沿原合法材料入口重新发行/原子轮换，并由新独立冻结准入流程检查；本岗不生成测试grant。任何失败保留前缀，按rollback overlay恢复原应用镜像；不删卷、不重建schema、不seed。

本地只执行py_compile、--help与错误manifest参数拒绝（在Docker调用前且无输出目录）；未运行现场planner/import/apply/rollback，未证明当前七角色配置或部署成功。
