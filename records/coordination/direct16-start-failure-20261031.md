# DirectP16 实际启动失败，未发压

用户提供LOAD8.149.131.140、APP47.96.183.226后运行既定after_boot单入口。Mac日志目录为主项目.submission-private/directp16-20261031T090210Z。入口退出DIRECT_RUN_FAILED_NO_RETRY。APP INIT FAILED_STOP_CHAIN phase=readiness，benchmark_started=false，credentials_may_have_been_issued=false；没有调用bootstrap、没有调用LOAD launch，无400客户端压测。

仅取回该失败的诊断：数据库SELECT1成功，TLS原CA握手成功；OPTIONS /api/v1/projects真实返回405、Allow:POST、body Method Not Allowed，程序错误地要求Allow含GET，28秒后将已可用应用误判成notready。该路径同时注册POST和GET，模拟接口只返回GET掩盖了真实路由次序问题。不是产品延迟测量结果。

用户问是否停机，总协调已明确建议立即停两台并停止远程调用；不再占用服务器做现场调试。用户是否已经真正关机不再远程查询，保其操作权。已撤销READY防误启动，所有修复只能本地完成、不得伪报旧包通过。没有新压测/自动重试/自动VM关机。
