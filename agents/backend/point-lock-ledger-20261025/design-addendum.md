# 逐点锁后的精确开发查询账本迁移

作者/执行者：后端 AI。本阶段仅开发测试与本岗记录；产品 Runtime 保持 c8cea7e / SHA9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b，不改独立验收或任何性能门槛，不触发 CI。

root 公开 product run40171891359（source81250e8、产品字节等同c8）contracts job121104271042 的准确失败：unblock_pending 的 task_dependencies 仍1，tasks实4对旧3；合同179目标中1失败178通过。原日志由root保存，本岗只读其明确发表的开发CI资料，不读829或其它独立私件。

候选先前已明确锁查询从1→K。此测试在唯一一次正常写请求窗口内计数：原 Business.task 一次、成功audit确认task归属一次，共固定2；Runtime锁集合K分别为 BLOCK仅target1、PENDING-UNBLOCK的target+未完成前驱2、START空依赖仅target1。因此精确tasks总数分别3/4/3。task_dependencies精确0/1/2保持：BLOCK不读图；PENDING-UNBLOCK只有Runtime读图、业务不消费前驱；空依赖START两次读边后不额外发前驱task查询。

仅将tasks单值3迁成显式operation字典3/4/3并补原因注释；保留Counter完全相等、task_dependencies原字典，以及版本/状态/成功审计/幂等重放/后续真实START拒绝/拒绝审计等全部断言。禁止>=、区间、放弃未消费分支断言或改产品压低真实次数。

执行：先在当前产品与原测试上窄跑该3参数，保留1红2绿；修改明确账本后，同3参数加邻接2个DEVELOPING-UNBLOCK/REWORK依赖守卫目标，必须5绿。其余同类账本静态核原985验证只读契约/五类preflight/历史页、持久层Rows/schema/seed和非SQL分类Counter；无依赖K1不应改，纯读契约不经locked_scope，历史页与底层账本非本锁改动，不预先改数字。可复用root已公开此次985全40及integration93绿的原开发CI事实，不能冒本岗新执行或取消整个product CI红。

原红、精确source/命令、测试AST白名单证明、产品逐字同、报告/prompt/Issue另封；不重跑56/35/完整suite/MySQL。root另统一新源full CI、审核与集成。本修订仍是开发账本，不是独立性能结论。
