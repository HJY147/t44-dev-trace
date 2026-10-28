# ROLE-backend-RESOURCE-WINDOW-20261028-v1

来源：总协调实际派工；操作者为backend AI，用户未亲自修改代码。

实际任务原文：

> 你是T44后端性能分析细分岗。项目 /Users/yang/Desktop/nothing/软件开发大作业，先读AGENTS，另建codex worktree从root协调branch当前HEAD（询问不明先只读，不改共享root）。root正运行同a12 source /P7对P16开发短对照，P7 PUBLIC完整结果可读root私有runtime内仅此明确白名单文件 /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/resume-20261028/p7-matrix-result.public.jsonl（5961B SHA8007971120f72242ca552153a1a9c1f200b44f4cc72bda0b5c89c17293452383），p7-mirror-status-after-seal.public.jsonl（3043B SHAb8abbb98482bd9aebe2c01b18fd1a4c6c1248478b51151a9f4805c66eb4a00fd）；不要扫runtime其他文件/读792独立private，严禁云UI。请分析P7实际数值/吞吐时间分母（barrier vs utcstarted区分），别将0HTTP错误当性能通过。另写小型只读server-side资源窗口聚合脚本供root UI部署：输入显式raw path +SHA（P7 LOAD /root/t44-r9/resource-mirror-r28p7-01/app-raw.jsonl，7516207B SHA2662a505f4034f63ae50f836d0c239cff1f2e018431cf2869af4a496ecbdd283），输入begin/end UTC从cohort actual started/finished。只读/精确hash/有限输出，按role真实CPU p50/p95/max及RSS max、cgroup max、缺失/采样错误/头尾/间隔；CPU单核100%可>100不得当host%，RSS进程和与cgroup memory不同，scheduler缺失保留null。禁止除以零填0/加不同P95。需要看现有resource-stream.py字段和CPU/RSS语义，防误统计。自备合成输入小测不镜像实现，真实产物未运行不可写云pass。P16马上会出root再给白名单。要本岗WORKLOG/module/handoff/prompt/commit push，临时tmp降序：789前端、790后端、791审核、792独立、793部署、794DB、795CI等占用；新文件可788先check未用。先给精准P7读数和可用聚合脚本，后补记录。

实际后续约束：总协调提供唯一可读采样器44079B/SHA3d9f…的白名单；审阅初稿后要求缺失sequence的未知缺口/倒序保留null并补已知样本/pair计数；确认无需重base，元数据由其合并。

执行上的具体改进：先核输入SHA和采样语义再统计，分开started/barrier两个分母；用带null和CPU>100%的手算输入检查CLI，避免把不同P95相加、缺失当0或把进程RSS当cgroup内存。初稿9225B/SHA82c526fe…经过协调精度反馈和静态格式修正，最终9560B/SHAf1df8069…；两个阶段结果如实区分。

产物：tmp/788/resource_window.py、tmp/788/check_resource_window.py、本目录报告/derived读数/verification/检查原件，以及本岗WORKLOG、模块报告和handoff追加。
