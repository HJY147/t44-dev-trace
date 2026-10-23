# ROLE-deployment-NATIVE-APPLICATION-v1

实际固定部署岗phase2派工；不是建议版、用户亲改代码或提示词演进次数。

## 实际总协调派工原文

固定部署岗phase2准入已root ec3e6b0（尚本地可读root）：records/decisions/native-application-capability-admission.json、native-demo-source-binding.json、native-demo-database-preparation.json；871已预留tmp/deployment/871_native_application.py，新free870。请先读，先本岗设计checkpoint后最小native/application.py controller+871 syntheticguards，不必等待root最后源。Root已新建独占t44_native_demo/只CRUD t44_native_app、19表18业务226cols、3synthetic角色/2projects40tasks60deps100records，禁止reset/drop/reseed；私密 .agent-worktrees/.runtime/native-demo-20261023/{environment,credentials,database}.json 全0600，允许读该显式新环境不用admin；旧环境都保护。准备snapshot .agent-worktrees/.runtime/native-demo-20261023/source/42243eb23aedf0edda7541ad83fd87ec3d17b616（44Py20TSVue）。但当前42243刚专审发现history evidence bool/int误匹配，backend窄修进行；你先做controller和依赖准备，真正应用启动前等root给修后exact candidate/sourcehash，别启动knownold42243为最终demo。前stage1broker都已停；本次需freshbroker，新vhost/cookieuser，保留oldruns，API18088四worker/UI5178，consumer+真实60sscanner（2真实完成scanruns）+正常Pika/outbox/notification+private TTL300 servicecredential受控轮换/回收，全部实际绑定新exact源。要求见准入：不改业务/lock/ruleinterval，不向argv/logpublic泄secret，签发真实CLI scoped两真实项目IDs。staging env PYTHONPATH是初始化0549，必须复制后改到root给final source。自身guard有真实坏输入/owner/secret/source/端口断言即可，不重跑已有phase1守卫除改了相应controller。所有操作有限循环最后stop自己完整app+MQ；保持原preview5173/18080/independent5175/18084/MySQL13306不动。根已关闭自己的developer18089，不需你管。先报告设计/入口风险和准备进度，再commit [skipci] push，原失败真实归档，GitHub Issue7/PR31可续谈精确readback。不要读取任何tmp/independent/未发布资料或正式负载。

## 本次作用与产物

将source与依赖准备、显式final绑定、受控有限应用周期、数据/凭据/拥有权与真实60秒证据分开，避免已知旧源启动或复用旧环境。产物映射deployment/native/application-design.md、未来application.py/871以及本岗phase2证据/日志/模块交接；所有声明按真实执行更新，未运行不记通过。


## 根提供修后精确源的实际后续

修后精确SUT已给：bc5aef9c62393134582affb7a690acb33ac2b833，immutable snapshot .agent-worktrees/.runtime/native-demo-20261023/source/bc5aef9c62393134582affb7a690acb33ac2b833，root receipt records/validation/native-demo-source-bc5a-binding.json。相较旧42243的92个file只history.py变化，44Py/20TSVue同，全旧snapshot保留。设计ad6→产品bcb strictEvidenceRefs+typedJSONidentity，原反例6案+正常legacy7绿；新的整CI/专审差量正在进行。你可把controller bind/requirehashes依赖/guard绑定bc5a；在自己的先设计+guard绿、私密源配置/拥有权预检通过后，根授权此前准入的有限新demo实际API4worker+consumer/scanner/UI生命周期（不需再等人的回答）。如根/审查员随后报告真正新阻塞立即停于安全状态，不声明正式验收；原42243从未启动app这一事实保留。数据库初始化0549可复用（schema/seed字节未变），禁止重seed/migrate/DDL。
