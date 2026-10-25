# ROLE-backend-SHARED-PROJECT-POINT-20261025-v1

作者/执行者：后端 AI，非用户手写或人工代码修改。

root 实际准入：原 S-only+batch 未证锁序路线不实施。先设计勘误→仅 START/UNBLOCK/REWORK 的 project S，原 writers X；Runtime 原task集合所有路径按 sorted unique ID 逐个 project+scalar唯一PK、limit1取X，返回值丢弃、全锁完再原Business重读。保原锁集合/session/idem/member/auth三次/两UoW/版本/错误/独立拒审计/CAS/事件，不改全局Rows。前驱D导致增加D条锁SQL必须如实记。发现反例先保留暂停，不能盲改。root负责fresh7HTTP+DB6及全量CI，本岗最小生产候选和必要窄回归、精确Runtime SHA、报告/规模/真实命令/Issue。

执行优化：将“ORDER BY有序”改成独立唯一行语句的可检查顺序。先冻结开发红目标再改产品；区分真实SQLite参数/业务证明、MySQL持锁事实、正式性能。只对确定候选最小编辑，不补猜需求、不删安全逻辑换行数。原S-only设计与原件保留历史，新修订单独成链。
