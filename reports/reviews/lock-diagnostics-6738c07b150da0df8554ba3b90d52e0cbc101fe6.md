# Setup 修订窄审：准入第二轮 fresh 开发验证

## 1. 对象

固定AI reviewer，精确`6738c07b150da0df8554ba3b90d52e0cbc101fe6`，相对812修订6文件；实际worktree HEAD同且干净。本岗不执行MySQL、HTTP、setup、SUT、CI或既有测试，不读或联系任何独立测试。生产C仍为c8cea7e，Runtime9e0d770e；生产两锁源码结论保持，非合并许可。

## 2. 原红与修订目标

root转述原run40171891410三job在迁移成功后REVOKE报1141，所有锁/HTTP/业务case0。本岗未独立读日志或观察SHOW GRANTS，记录为准备脚本失败，不当产品case失败。原812/nonce01及失败保留，不回写。新修订消除对镜像自动创建的t44 grant表示的依赖，不修改产品或降低业务断言。

## 3. 真实差量

6文件仅workflow移除MYSQL_USER/MYSQL_PASSWORD、setup、request/validator同步固定02，以及纠错说明/8项JUnit。产品、DB probe、HTTP驱动、986和原时限/库隔离没有差量。admission除nonce01→02外整AST相同；request除nonce外相同，不接受任意nonce。当前实际文件逐字同HEAD。

## 4. 权限与安全边界

每个独立fresh service由一次性root完成精确命名库迁移，随后查询mysql.user，若任何host已有User=t44即拒绝，不删除、撤权或覆盖它。然后一次CREATE USER，public disposable密码参数绑定；仅本库CRUD与data_locks/data_lock_waits/threads三表SELECT，没有REVOKE、DROP、PROCESS或全局授权。库名仍来自严格mode/环境allowlist。

schema级GRANT对两个固定库名的每个下划线添加一个反斜杠转义。MySQL8.4文档要求这样避免库名下划线被作授权通配符，修订构造方向相符。[MySQL 8.4 GRANT规范](https://dev.mysql.com/doc/refman/8.4/en/grant.html)。这不是本岗观察过实际SHOW GRANTS或应用有效权限的声明。

## 5. 执行相容性

前审的3独立service、固定镜像、loopback/3306/两专用schema、76文件/精确ade5或c8c、两个工具hash、DB120/150秒、HTTP180秒与5秒强杀宽限、job10分钟、fail-fast=false和失败artifact保留均不变。当前root权限/CREATE USER/CRUD/P_S的实际可用性仍须第二次freshCI证实；任何失败按环境/实际phase留痕，不以更宽授权掩盖。

## 6. 实际核验

只执行Git/实际字节、AST/JSON/XML核对；8项新JUnit机械复算8/0fail/error/skip，不重跑，不冒真实grant测试。机械原件`agents/reviewer/evidence/shared-project-point-c8c/workflow-6738c07-audit.json`。root另转述普通product CI40171891359在旧986 unblock_pending查询账本预期3/实际4处失败；本岗未独立读该日志，不能称full CI绿，也不据转述擅自改账本/产品。这不改变有限fresh锁/HTTP工作流的输入。

## 7. 十项判定

| 项 | 判定 | 依据 |
|---|---|---|
| 1 身份 | 通过 | 精确6738/6文件actual=Git |
| 2 范围 | 通过 | 仅准备脚本/固定nonce与记录，生产/断言不变 |
| 3 准入输入 | 通过 | 02 request与validator同步，原限制保持 |
| 4 库隔离 | 静态通过 | 三独立fresh service/原本库约束 |
| 5 产品业务 | 本轮不重复判定 | c8c原两锁有限源码审保持 |
| 6 权限 | 静态无新增阻断，实际待证 | fresh-only新用户、转义库CRUD+3表SELECT |
| 7 时间并发 | 静态保持 | 限时/独立job无改动 |
| 8 故障留痕 | 通过限定范围 | 原01红run保持，准备失败不冒case失败 |
| 9 测试真实性 | 通过限定范围 | 8项仅复算，0本岗DB/HTTP/CI；run只root转述 |
| 10 执行/合并 | 准入一次开发执行，不准合并 | 实际权限/锁结果和full CI/规模未通过 |

## 8. 结论

未见本修订新增实质执行阻断；精确6738可推送执行一次第二轮fresh开发工作流，固定request02。已先给root技术结论再封行政。真实权限、低层锁、HTTP与产物仍待CI；静态准入不替代实际成功。新源/环境变化另审，不发APPROVE、main/global、全量CI、正式性能、规模、产品或合并通过。
