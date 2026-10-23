Agent-Role: deployment
Prompt-Ref: ROLE-deployment-M0-COMMIT-v1

依据调度岗已提交的 [records/handoffs/scheduler.json 草案](https://github.com/HJY147/t44-dev-trace/blob/253276093ba0557d9446aab358bb02faeb03d845/records/handoffs/scheduler.json)，数据库接口拟保存扫描批次/检查点与唯一升级业务键；本岗 `reports/modules/deployment.md` 已将单实例约束、持久状态与启动续扫列为运行输入。两者均未冻结、尚未实现。

请确认后续运行契约：APScheduler 是独立进程还是嵌入 API；单实例保证由哪一岗提供；应交付什么启动命令、健康/就绪信号及失败退出码；重启/恢复时哪些持久记录是续扫依据，何时允许就绪？这些信息将决定 Compose 启停顺序和恢复核对，当前没有收到确认，本留言不把任何候选拓扑定为实现。
