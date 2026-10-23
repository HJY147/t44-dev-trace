Agent-Role: scheduler
Prompt-Ref: ROLE-scheduler-APPLICATION-v1
Refs: #6

实际调度入口已实现：容器命令 ["python","-m","t44.scheduling"]，必须是独立服务，API worker不启动timer。环境DATABASE_URL及匹配T44_DATABASE；T44_SCHEDULER_TOKEN_FILE=/run/secrets/scheduler-token.json，文件必须可读且无group/other权限（0600），不能把Token写进Compose/日志。

初始化复用现有后端命令：python -m t44.cli service-token --name scheduler --project-id REAL_PROJECT_ID --token-file PRIVATE_FILE。项目ID必须来自真实初始化，可重复--project-id覆盖全部应扫描项目；它签发实际service会话和escalation:write scope，没有新增JWT。会话默认TTL来自T44_SESSION_TTL_SECONDS（后端默认3600），部署需安排受控轮换，调度每次重新读取文件并由Runtime重新鉴权；新凭据先写新私密文件再原子替换既有路径，勿打印Token。

默认JSON在t44/resources/escalation-rules.json，API与调度须加载同一已采用版本/原文（同镜像/资源挂载）；CLI --rules或T44_ESCALATION_RULES只指定调度实例，不要给两端不同配置。v1 metadata decided_by=1是冻结契约合成示例，初始化责任岗须如实映射实际决定者，不能冒称用户就是DB ID1。

默认锁文件为临时目录t44-scheduler-数据库名.lock，可用T44_SCHEDULER_LOCK_FILE指定。保持一个scheduler容器；若同主机多容器可能启动，须共享同一锁路径才能由flock互斥。这不是分布式租约，数据库业务唯一键另兜底。SIGTERM等待运行回调，启动/once错误exit1、成功exit0；周期失败会留未完成run并由APScheduler脱敏记录，健康应看持久heartbeat/完成状态，进程在不等于扫描成功。

真实一次扫描：python -m t44.scheduling --once；恢复指定已存在UUID：python -m t44.scheduling --once --resume-run UUID。固定cutoff/keyset/checkpoint已真MySQL验证，实际子进程突然退出后恢复20条无重复。周期自动恢复当前hash下120秒旧心跳run，旧/不同hash不被静默改写，须原配置恢复或审核处置。以上为真实已实现接口，Compose接入由部署岗执行，本岗未改部署文件。
