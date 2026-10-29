# 总协调 AI：5d 组合开发验证

实际提示词 ROLE-coordinator-CI-5d-20261028-v1：把审核允许的两项产品候选与新测试 CI 接线绑定准确提交运行；保留旧失败和新原件，分别计算唯一用例与覆盖率；不把 CI、短诊断、进程成功当独立验收或性能通过。用户最新决定仍为现有严格代码规模和400活跃并发口径。

实际 push `codex/resume-coordination-20261028` 至5d后，由 gh 手动启动 product40682367472、Docker40682640278。GitHub连接器没有新的 workflow dispatch 能力，故仅调度与原 run-log ZIP 使用既有 gh CLI；制品元数据/下载使用 GitHub 连接器。随后通过系统 curl 保持 TLS 校验取回原 ZIP，按每个官方大小及 digest核验；原 run-log ZIP没有服务端digest，单列本地hash。首次 Python urllib 因本机 CA 链缺失拒绝，未接受字节、未关闭 TLS；随后系统 curl 成功。

四个 product 制品与一个 Docker制品全部原字节保存；两个run的原checkout日志逐个核准确5d。JUnit唯一键 classname/name 实得775，0失败/错/跳过；完整覆盖率与标记子集、前端、静态、19表恢复分别解析，机器结果和报告在本提交。一次临时查看前端结果未过滤coverageMap导致输出过长，随后改为明确键读取；没有把打印成功当测试结果。

source_count.py + 固定cloc2.10对5d实际返回 application5935/within_range=false/exit1。之前 fee30 计量原件不改，新增5d独立原件。此提交仅留痕，不改产品，不让新行政HEAD冒作5d被测HEAD。

同时发起 source-only 官方打包40685318398，输入 source5d、stop2026-10-28T16:00:00Z。该任务是运输准备，不是新产品测试。部署v4/回调桥由各owner准备、审核后才准云端；审核发现缺预算回执透传和direct SQL预算准入，已单向派原backend owner修复，当前阻断版未云执行。独立测试只接中性输入，未读其私件或用例。

原LOAD实例由阿里云UI启动，实际只读核到旧容器运行数0和原数据/镜像保留。新的中性镜像由根在部署岗明确授权下仅去三项额外ENV和接受缺省空PYTHONPATH，原f30helper/旧结果不变。该操作后续实际身份及Linux no-SUT结果另记，不混入这里的CI通过范围。
