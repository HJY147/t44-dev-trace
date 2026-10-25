数据库 AI 后续设计/工具交接：项目 S + 按 task id 逐点 X（尚未运行 MySQL probe）

原S+batch风险报告和Issue4#6394606519按旧source保留。root后续准入修订设计；BE产品候选c8cea7e/Runtime SHA9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b，本岗已静态核原件，未修改产品。

新设计24ca1db先行，DB工具ee12656513af846c441e20ef858c6aee1126e8dc，probe SHA638a77c91981c5b7217b4ccbbf03634f39364296260e27014b8a6eb37db56fd6。三读图transition project S/writers X；原target+pred set sorted逐个 project+scalar唯一PK/limit1 X，全部完成后原Business重读；非图单target仍一次，D前驱较原batch增加D条锁SELECT。未发现此修订新增结构性反例，但只证明显式task id请求顺序，不夸大成secondary/FK/旧非图路径全域无死锁证明，不据S兼容断言提速。

833新增必需 --expected-task-lock-shape batch|point。真实Runtime内透明观察本UoW原gateway.rows的集合/顺序/scalar/limit1，配合同线程实际cursor SELECT形状SHA/次数；EXPLAIN用该次真实捕获可信参数化语句，不拿旧IN计划冒candidate。6个低层门控case保留反向id不交集、两共同pred、writer、pred最新状态、同版本CAS、P_S精确request/block/table/index边；parallel要求两项目RECORD GRANTED S。

fixture前P_S readiness单列环境/权限错误（如1142），不算锁case失败。最窄表级权限仅SELECT on performance_schema.data_locks、data_lock_waits、threads，授本次fresh实际账号；不需全P_S/PROCESS/UPDATE。官方MySQL8.4表权限与threads模型：https://dev.mysql.com/doc/refman/8.4/en/performance-schema-table-characteristics.html 、https://dev.mysql.com/doc/refman/8.4/en/performance-schema-threads-table.html 。本岗未执行GRANT/DDL/连接MySQL。

同8个工具guard再次8pass0.39s（只join/门禁/排他输出，不是新增MySQL分支通过），新两脚本Ruff和暂存check通过；point-tool-junit.xml、point-lock-report/design-addendum/prompt归档。首个patch按旧换行找不到hunk而原子拒绝，无部分写，核准实际format后分段应用；旧原失败不改。freshCI实际运行由root统一编排，本岗不碰13306/本机旧库/云，不接触独立私有case。正式性能/规模/人工出口均保持开放。
