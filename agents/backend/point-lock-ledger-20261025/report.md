# 点锁开发查询账本：单一期望精确迁移

作者/执行者：后端 AI。root 派工后先设计91bf2f4，test-only C **5f55e09a75043343e376ecc7d96cc2ed98862b30**，分支codex/backend-point-lock-ledger-20261025。产品零改变，Runtime仍SHA **9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b**。

## 原因与最小改变

root公开run40171891359/source81250e8（产品字节同c8）的contracts job121104271042唯一真实红：unblock_pending的tasks4对旧3、task_dependencies1未变，1失败178通过。原公开gzip日志逐字副本保留为original-ci-contracts.log.gz，raw/gzip SHA及实际终态行见original-ci-receipt.json；没有更改root原件，也不把该run改称全绿。

点锁后 Runtime 锁 SELECT 为原锁集合K，Business.task和成功audit归属查询固定两次：BLOCK K1→总3，待受理UNBLOCK target+前驱 K2→总4，空依赖START K1→总3。只将原Counter(tasks=3)参数改显式map **3/4/3** 并加解释注释。task_dependencies的原精确 **0/1/2** 不改，Counter仍完全相等；没有>=、宽松上限或删除未消费前驱分支断言。

verification.json将新Counter.tasks值恢复为旧常数后，整个986模块AST完全相同；状态/版本/成功审计、幂等重放、后续START真实DEPENDENCIES_UNSATISFIED、拒绝审计和资源版本不变均原断言。本轮不改产品、契约、独立验收或性能要求。

## 已执行

当前点锁产品/原测试先真实3参数 **1 failed/2 passed**，与公开CI相同；原命令/source及未裁剪红输出完整保留。修改后同3参数加原DEVELOPING-UNBLOCK/REWORK未完成前驱的2目标，准确C **5 passed/0failure/error/skip**。Ruff/format原配置通过，现有TestClient弃用warning保持。未重跑其它全套/56/35或MySQL，未触发CI/云，root另统一完整复测。

同类账本逐项静态核：

| 既有断言 | 为何不迁移 |
|---|---|
| 986本目标依赖边0/1/2 | 精确保留，继续证明未消费的业务分支不增读 |
| 985五类preflight SELECT/DML/control | 原fixture无前驱，K1仍一条task锁；replay/非图不增加集合，旧数不应变化；认证、UoW与提交断言保持 |
| 985 validateContractPayload表序列 | 原只读专门分支，不进locked_scope |
| 985 schedule_changes两次SELECT | 只计历史页fixture+一次enrichment，非任务锁表 |
| persistence988/993/956、seed975 | 直接Gateway/schema/seed SQL，不执行Runtime点锁 |
| 930/955分类Counter | HTTP类别/记录/诊断事件统计，不是此SQL账本 |

root原开发CI日志还保留integration93通过，不能替代新source完整CI；本岗没有凭静态分类修改其它数字。无依赖/有依赖成本仍按K逐项记录，不把任务点锁成本归为无必要业务读。

## 已发表MySQL开发事实的边界

按root允许只读40172242303/extracted下三份公件，引用其6 baseline、6 candidate、7 HTTP案例名称/状态与SHA至published-mysql-reference.json；HTTP source6738c07b150da0df8554ba3b90d52e0cbc101fe6，candidate要求的Runtime SHA与本C相同。是root编排的fresh开发运行，本岗只核发表JSON元数据/案例终态，未重新执行或再审核每条锁记录；6+6+7不等于19个产品验收用例，也不证明性能、全域无死锁或旧502根因。未读829目录或独立私件，未联系测试岗。

## 规模及待办

产品对0615017逐字未变，因此沿准确同字节既有cloc6326、超1226/FAIL，不新测也不把测试变化算产品节省。root用本test-only C统一完整CI、独立source审核及集成决定；旧run红保持，正式性能/独立验收仍另待证。本报告/代码/验证均AI，不记用户手改、手测或手写研究报告。
