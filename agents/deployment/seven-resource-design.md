# 七服务只读资源采样：先行设计

固定C app、Composeproject=t44及mysql/rabbitmq/api/consumer/scheduler/web/tls-gateway七项；不复用六服务usage合格声明。先只读ps发现唯一64hexID，inspect严格投影ID/project/service/running，拒外来/重复/停止。每次再核原七ID标签，然后一次stats no-stream/no-trunc白名单字段；固定四/proc文本与UTC/monotonic时间包围，不读Env/日志/密码，不改任何服务/权限/网络。

root私有/run/t44-delivery下resource-UUID.ndjson排他0600，最长20min且绝对UTC08:44停止；start-to-start目标10秒，命令/proc/磁盘写入/调度有真实overhead，超时/缺项独立失败样本，无修复或性能门禁判断。最终hash/bytes/实际样本/失败数为安全摘要。部署岗仅本地纯函数检查，不在云端执行，845预留必要边界。
