新增显式有界 native serve/owned stop：新prepare的专属run在180..14400秒内保持API/consumer/UI，到期或SIGINT/SIGTERM在安全检查点进入精确拥有权清理；TTL300剩120秒时仅排空/轮换scanner并确认旧撤销、新持久tick/锁。stop只请求指纹匹配runner PID停止，请求不等于已清理。固定应用bc5aef9c62393134582affb7a690acb33ac2b833及92文件/既有hash锁依赖/t44_native_demo，不迁移/reset/reseed，不改业务/锁/规则。

运行工具代码仍为 **62ac2f327e7523ffed69a2bd9f98c87ba2372931**，application SHA256 **08461886f631e070b206d1533be8be320a90eeea27a0f813795d970f7d9a1e25**，runtime SHA256 a251989f589943bf513fa506015a7bba356fbb167a525a7fd79a29306689fa6b未改。新复验证据提交 **10182b79906d60379e1ece6b37d0c8b9727f7b0a** 仅文档/脱敏证据/实际外部运维driver副本；目录整理提交 **13cd3d515c06b0408b5048c852a95a8f1b3ba9b2** 将三份验证脚本公共副本逐字节移至 tmp/deployment/864_native_serve_driver.py、863_native_serve_post_attempt1.py、862_native_serve_post.py；路径/SHA mapping另档，当时私密执行路径/argv/失败/原始hash不改，无运行重做。随后GitHub回执尾commit另列。原设计daaccb7/工具4ef、原失败封档f159、停机选择设计c191/窄修62ac均保持。

原4ef唯一360（app_20261023_230429_cc2f5b）仍是actual exit1、summary=false、cleanup=false：旧verify_stopped纳入still-live serve runner自己，局部就绪/扫描/轮换与外部最终wait/absence不能倒填整体成功。原stdout exact gzip与全部原失败证据不改。先设计后窄修仅检查四真实角色全部generation与API workers/tracker；同guard原942真红→新084的3必要合成方法绿，8角色代/5APIchildren任一残留仍拒绝，Ruff通过，capture/runtime/其他函数AST不变。精确62ac专审a7bad288仅限定关闭SERVE-CLEANUP-SCOPE-01、无另确认新增P1/P2，根1e9a081整合后另准入一次新fresh360，未准入4h。

**新的唯一360实际复验已完成：exit0、summary/cycle/cleanup均true，当前自有服务全停。** 新app_20261023_233238_345882/全新manifest-cookie-vhost，serve起点23:32:39.043824Z、deadline23:38:39.043824Z，duration_elapsed请求23:38:39.044609Z、summary结束23:38:41.688950Z，外部driver wait23:38:42.502726Z确认runner真实exit0。独立prepare不包含在controller360秒；截止触发清理，finished时间如实晚于deadline。

新运行局部能力与清理证据：ready23:33:48.542961Z、首两新completed扫描60.324684秒、额外TTL300轮换1次/旧撤销/新tick与锁；API/consumer/UI各启动1次、scanner3代、4APIworkers。3个本轮双项目scope服务凭据及ready会话全部撤销。controller wait_scans验证4条与同UTC数据库实际8条completed分开，全部冻结rulehash匹配；现有2项目40任务。旧16confirmed/26通知仅复核，新outbox=0，不称本轮新publish。12个登记应用generation/APIchildren/runner后置全absent，Rabbit/EPMDgone，新5端口closed，92源逐SHA不变。

本次外部read-only driver在freshprepare前→serve前→外部wait后分别记录9端口（5173/18080/5175/18084/5176/18089/13306/5177/18086）的listener PID/UID/start/PGID/commandSHA与地址，三个时点逐项相同；没有读取独立应用数据。这是本次三时点补充观察，不是全时连续监控，也不回写原仅7端口的snapshot。后置证据提取attempt1因rule_hash bytes不能直接JSON真实exit1，原source/failure保留；仅转hex后native只读提取exit0，没有controller修改或服务重跑。

证据入口 `agents/deployment/native-bounded-demo-validation/README.md`，新结果 `serve-retest-capability.json` / exact `serve-retest-summary.raw.json.gz` / 私密原件SHA `serve-retest-original-index.json`；实际prompt `agents/deployment/prompts/ROLE-deployment-NATIVE-BOUNDED-DEMO-v1.md`。60public/226private非秘密outputs对旧失败+新复验19literal匹配0，三份实际输出对4真实账户literal匹配0；dump/秘密不上传。窗口已释放，后续仅离线归档，不继续服务/HTTP/SQL。

旧PR31/34、phase2原run1失败/0a6 run2成功及cd3限定capture关闭不改。无独立/性能/云、资源unknown回填或整体放行结论；**用户最多4h演示仍需根另准入**，本PR保持draft。

Agent-Role: deployment
Prompt-Ref: ROLE-deployment-NATIVE-BOUNDED-DEMO-v1
Refs #7
