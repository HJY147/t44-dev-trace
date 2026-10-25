# 实际后续提示词

ID ROLE-database-MYSQL-POINT-20261025-v1；操作者数据库 AI。

root 实际指令：已准入 BE 修订设计候选，三个 transition 读图 project S，writers X；原 target/pred ids 改 sorted unique 后逐个 project+scalar唯一PK点 X，非图本就单task一次；原Business重读不变。审新增反例，设计勘误后更新833探针 baseline X/batch 与 candidate S/point 的真实形状、EXPLAIN、交叉/共享前驱 P_S边；只同8工具guard，不在本机跑MySQL、不碰13306，明确最窄P_S表级SELECT权限，生产Runtime归BE。

本岗实际细化：先读并核 BE c8cea7e Runtime SHA9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b，再提交24ca1db设计勘误；只证明显式任务id请求顺序，不夸大FK内部资源全序。用临时本UoW gateway观察和同线程SQL事件检查真实shape/顺序/数量，EXPLAIN实际捕获语句，不重复推断。先单列P_S readiness，官方8.4确认只三表SELECT，不索取全局PROCESS。旧设计/结论/失败按旧source保留，新stage另封条；AI工作不写成用户亲改。
