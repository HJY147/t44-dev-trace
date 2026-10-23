Agent-Role: backend
Prompt-Ref: ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1

阶段A仅准备，基点397bd7973cfd835c635634d32e0c98ae56d74949（指定父产品43f51570）。唯一新工具tmp/backend/955_perf_profile.py和agents/backend/performance-diagnostics-plan.md列出真实API/Runtime/验证/SQL的输入输出和观测边界；诊断进程仅限t44_profile/127.0.0.1:18082/1worker/≤120秒，baseline/timings/profile分开，不改生产或冻结HTTP，不迁移/seed/登录/发负载。

工具尚未执行、导入、编译或本机lint，没有延迟/CPU/SQL/锁/连接池/验证指标，不能预定瓶颈或声称提速。旧CI317通过不用于证明新工具。准备完成时总协调已通知两份独立报告正式发布并调整优先级为先修业务IAT01～05；本准备稿尚未读取报告，阶段B仍待业务修复checkpoint及隔离库/中性账号/资源空闲。未读未发布黑盒文件/私有脚本，不联系测试、不触不可变API或dev/acceptance/perf。原阈值/安全/事务/校验保持，源码5866超5100仍待解决。实际dispatch已单独归档，原proposed提示词保持历史。
