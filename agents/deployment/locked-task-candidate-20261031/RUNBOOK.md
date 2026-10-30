# 第二候选离线镜像准备与现场边界

准确源13acb43a804e717e7485091895378511fe3d9b76，产品字节为a59a90a1；13ac只维护两项开发测试查询预算。原90b镜像不能作为新产品运行。build run41111887081只构建和封装，不启动SUT，不批准上线或性能验收。

构建通过后下载cloud-images-13acb43a804e717e7485091895378511fe3d9b76-41111887081，保存到主树.submission-private/build-candidates/locked-task-13ac-20261031；对bundle-manifest.json求独立SHA，再用本源deployment/cloud-reuse/image-bundle.py verify复核压缩包bytes/SHA、解压SHA、linux/amd64、官方固定上游及backend/web准确revision/archive label。此verify不调用Docker；现场load需实际核config ID，不能用本地静态核验冒现场加载完成。

## 现场前置，尚未执行

两台原VM均由用户关闭。不得请求现在开机，仅在root完成完整CI、审查和新中性测试准备后由root告知。开机后重新验证SSH原hostkey、当前IP/授权、当前磁盘空间、原数据卷/schema/索引、现有服务镜像及资源配置。镜像load要求Linux amd64及12GiB空闲，先确认40GiB原盘当前真实余量；不得擅删旧镜像、卷或历史证据腾空间。

保持原64CPU应用机worker/线程/连接池现场配置及原400客户端、60秒预热、600秒稳态、P95≤270ms等要求；新bundle仅提供镜像overlay，不提供资源配置。新源升级须先显式组合新镜像overlay与原已核资源/TLS配置，使用no-build/pull-never，严禁误用仓库默认值覆盖现场配置。七角色包不代表必须重建数据库/消息卷。

p13已完成且NP_NOT_ACCEPTED，旧run/material/grant均已消费；下一轮必须由root按新源取得新的中性材料与独立准入，不能复用既有grant，不自动创建后继试验。测试退出、相关写入停止及证据回收核验后立即告知用户手动停机，不配置任何自动关机或云stop定时器。旧resume-source-package的stop_utc接口本轮未执行。
