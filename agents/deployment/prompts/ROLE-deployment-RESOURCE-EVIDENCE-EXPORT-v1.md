# ROLE-deployment-RESOURCE-EVIDENCE-EXPORT-v1

## root本轮实际派工原文

最终正式3组压测将开始，继续中性部署证据职责。请在你自己的worktree准备完整资源证据回收设计和小型公开helper（先设计后审），只允许读取本岗位创建的 /run/t44-delivery/resource-*.ndjson 与 /run/t44-relay852/host-resource-*.ndjson，记录原始文件hash/大小/UTC范围/样本数/失败数，可将这些中性raw归档；不能扫描或读取任何852私有用例/结果/.env/token/key。需在18:10结束后、18:30释放前完整下载。可用官方文件下载功能，用户已实际下载49,520B原密文并hash一致。程序必须root0700目录/固定受控路径/nofollow、资源上限，不输出原始私有IP。app v3和load host sampler刚实际启动，尚无完成计数。你不能直接浏览器/执行云操作。交代码hash、离线检查、记录报告prompt commit；不要碰主worktree/index。

## root限定审查的本岗原文段落

已审resource-evidence-export.py核心：受控路径/原件SHA/nofollow/600/root700/OEXCL/窗口和原raw保留可行。补一个如实口径点：summarize当前sample只验证number/time/errors，缺proc/services仍可OBSERVED；请在app要求services精确7+proc精确5且值非空str，load要求proc精确5且非空str；任何缺项计invalid/NOT_PROVEN，不能仅errors空得OBSERVED。保留raw原样，不因坏行拒绝保留证据。首样本真实app resource-aa5399ea993f426b82b678f5812c530f.ndjson/09:11:13.775549Z, load host-resource-0a687bf0312940979b8097f1800a2850.ndjson/09:17:47.204093Z；最终SHA等待18:10。

后续root明确尽快交最终SHA/短命令/commit先预上传，不等长封档，结束释放。本次只归档本岗资源指令；无关独立验收提醒不转存、不读取其原材料。

## 设计与边界

先resource-export-design.md；显式路径+完成SHA，不glob/scandir，不读任何852私有，只允许匹配32hex本岗NDJSON，两个host分开。NOFOLLOW/owned600/稳定inode元数据/hash；流式压缩hash+manifest，字段缺失NOT_PROVEN但原raw不丢。实际18:10后root等完成摘要再运行，官方单文件下载/本地全hash核验在18:30前完成是待执行计划，本岗无云/浏览器权限。26离线校准，不新建test代码文件。原682c80不足的缺字段反例实际red，补后78a252…通过；不冒原件已回收或正式性能通过。
