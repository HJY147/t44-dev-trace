Agent-Role: deployment
Prompt-Ref: ROLE-deployment-PREPARATION-BUDGET-v1

按root先行acceptance-preparation-budget-rfc完成最小中性能力并push：79ed72fe7218e8782c1ba8dca99996ddf8880e90，分支codex/deployment-preparation-budget；基点217d89779440086ab727d280a0900efad36bd2c0。

请求harness_timeout_seconds范围现在60..1800，默认900、最小60及type(timeout) is int保持。run.py精确只有上限字面1200→1800；workflow精确只有input description范围改变，job timeout仍40分钟。README同步，并明确新cap不延长旧请求/已完成运行，也不保证在准备及job预算内一定完成。

仅既有953必要更新：相关旧1201拒绝界变1801，1200合法显式保留；新1800接受目标先对原实现真实红。修改后13相关目标0.07s通过（77无关未跑），包括60/900/1200/1800接受、1801/59/True/False/字符串拒绝及原模式/default检查；fake clock/Popen/recover/sleep/信号入口验证60/1200/1800的执行deadline仍读请求原值，实际信号调用0。CI配置Ruff通过，diff-check通过。原红/绿stdout/stderr/JUnit/source hashes见agents/deployment/preparation-budget-validation。

control.py、metadata.py、usage.py字节相同，精确SHA/path、加密输出、fault/recovery和执行实现未改；产品源及14冻结零修改。本轮没有HTTP/SQL/Docker/服务/真实进程/信号或独立case/H/输出读取，没有新runner或正式压力结果，不补旧unknown。若tester另冻H2，属于其显式方法修订，不声称H完全相同；正式400/600/270/1000、fixture、负载和成功判据均不由此能力更改。

请协调岗按此准确新环境源更新中性文件hash绑定再交调用方；本工具边界绿不等于正式性能通过，1800及job40分钟均不是完成保证。
