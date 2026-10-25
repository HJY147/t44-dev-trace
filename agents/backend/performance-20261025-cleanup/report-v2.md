# 当前准入源：DIAG-CLEANUP-01 与构造失败状态

本轮最终source为 `124785d89e568dd5dddeb56ef9216ed2ccd1883d`，834 driver SHA `e0a49e630957268195adc6d6f1cd924bf6481b533f7c3c276b3e832b21aeba49`。报告report.md和E d4fc4ea保留初版b079/10绿的真实截止，不能用其旧driver hash准入当前工具；原78bb的全部CPU raw/E没有变化。

初版已关闭真实fixture清理问题：requests先存，只有install返回后snapshot，任何stage/fixture/snapshot清理异常不跳过observer.close；主异常原raise，清理错误分phase/类名保存；成功体有清理错就失败。初版同文件10绿、旧源2红保持原件。

封档自检再发现：observer_from在返回实例前失败时，初版按无实例误标NOT_REQUESTED。实际可为已请求而构造失败。本岗新冻结一个零DB目标2d405465，针对初版实际1红（预期NOT_INSTALLED但得到NOT_REQUESTED）；124785d只保留请求意图requested标志，把无实例构造失败与未请求分开，不再试图关闭根本未返回的对象。

最终同一文件11通过/0fail/error/skip，旧10与新11是相邻版本，不相加成21。命令/JUnit/stdout见loader-red-*和green-v2-*。仍全为内存假操作/fixture/observer调用真实run，真实DB/app库被阻止，未跑HTTP/SQL/服务/云。原56剖析和35引用差分不重跑。

verification-v2.json机械证明原Stages、fixture、observer_from、main AST不变；原测量body只多install成功标志，原初始化移入try。现有生产、合同、DDL和原CPU证据目录逐字保持。限定两文件Ruff/format通过。清理close本身失败仍会记录并使整体非绿，不能承诺所有关闭成功；文件系统硬写失败不在此P2范围。当前交root限定复审和新request/workflow hash同步，不是生产性能达标。
