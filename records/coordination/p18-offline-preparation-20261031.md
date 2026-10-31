# P18：重复运行初态修复后的准备

用户原目标保持：找具体原因、真正修复、全本地准备后通知开机验收。P17实际发生的STATE_CONFLICT及原认证失败证据不回写，服务器已被通知可停；准备阶段零SSH/云/SUT，不自动新轮次。

P17独立初始400query聚合为232 state2/168 state3，168全部blocked_from_state2，400owner正确且与启动inventory的state/version一致；这是当轮初始快照，不是当前在线计数。首次请求对已经state3的任务再次BLOCK，原产品按状态规则拒409，说明repeat前置准备遗漏，不是CPU/内存或原后置预算故障。400 escalation任务/配对event均存在且schedule/rule版本一致，原冻结规则在cohort和未来24h（计划规则不变前提）均最高level3，未见同类时间越级证据；不伪称未来实际数据不变。

新backend c7e77a5/ebbf9a15通过原API合法UNBLOCK仅state3/from2，state2零写，全400预检owner/状态和800资源身份后才写，写后GET新CAS，不SQL强改、不吞409、不重试不明写。准确产品bcec/原测量9cf与postfeff/compiledff95保留，BOOT只新RUN18，完整有效身份重新绑定。后端独立18检查（其中5真实本地FastAPI→Runtime→Workflow→SQLAlchemy SQLite）已限定通过，报告721c327c集成33a981dc；部署中文/混合400/rotation等已集成bbf53447。两个旧开发fixture alias误共享问题仅修fixture，不能算产品缺陷或掩盖失败。

新RUN r30posttools18、新REMOTE/root/t44-direct-p18、新W/root/t44-final-20261101/QA753_DIRECT_P18。P17已消费，绝不复用其目录/nonce/密钥/批准。P18 coor沿用已独立审查的READY直接CLI门禁/已封存失败证据回收路径，改到新producer/部署目录；本地11组coor检查通过，候选总包156793B/SHA90a26ca56f9d1b99bed59d946a5ad8809a1cc5cefd212598c5cb39a13453b055仅临时45payload，不是最终READY。

完整本地400/60+600/post回放正在运行，另需同一fixture第二独立RUN域准备/短起步，再新鲜无历史实例核最终入口/有效工具与总包。未完成前保持PREPARING，不通知开机。仅Linux/macOS资源边界如实标记，不下载新环境、不做额外付费AB。

此前GitHub直连HTTP/2/HTTP1连接失败已如实保留；本轮仅对git命令使用已存在系统HTTP代理127.0.0.1:7890后，push20801cc3..bbf53447成功，未改系统网络或SSH配置。后续本地未发布改动仍以实际git记录为准，不把同步失败说成成功。

需规/设计写作继续暂停，所有记录为AI实际工程留痕，不冒学生本人。
