# 实际派工摘录

root发现执行前审核P2 DIAG-CLEANUP-01，实际要求：“先存requests；未install snapshot明确NOT_INSTALLED；无论snapshot/fixtureclose是否失败都保证observer.close；初始异常保持主异常，清理异常单独记录，成功时清理失败不能冒绿。”

限定只修诊断清理、tmp/834窄回归；不重跑56样本或35矩阵、不改生产、不改旧E/raw。后端AI先设计、保存反例、修复和回归，优先给source checkpoint；该阶段不是学生手测或产品性能通过。
