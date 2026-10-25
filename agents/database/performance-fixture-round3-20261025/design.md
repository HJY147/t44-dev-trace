# R3 显式模板派生的数据准备

root本轮授权唯一新schema/user t44_p829c_20261025和performance-db-round3/application-env.json，仅该本库CRUD；不读其他env/admin/独立资料，不操作旧库/旧会话/旧receipt，不DDL/drop/reset。迁移已由root在全新库完成。

以已验证d8 helper原字节/SHA c6167e799533e493ca9faa85241e1c0acecd92bf4b96c154c7ddc79a6be205df为源模板，机械派生新文件833_performance_fixture_round3.py：数据库字符串1处、env路径片段1处，严格替换计数，不手写复制业务逻辑。新输出目录只通过CLI固定传入agents/database/performance-fixture-round3-20261025，原helper没有内置输出目录故源码此项替换0处/CLI替换1处。逆替换必须逐字恢复原模板，原文件和旧receipt hash不变；新旧hash、计数和精确patch先提交。

原Collector/transform/35FK与不可变指针核验/seed44/anchor2026-10-25T08:03:00+00:00全不变：40/6000/9000/15000（11400reviews+3600decisions），assessments额外3600；P1/I1两组各400及偏斜/0依赖声明沿原。5账号m/d/d2/r/x，x无成员，准备后auth_sessions应0，root另签会话。

先设计与source checkpoint、静态模板逆替换/hash/Ruff；仅指定新env/匹配host127.0.0.1:13306/db/user/0600才可唯一新库执行，全部业务表非空或源不符立即保留拒绝、不擦表重试。原函数内前后schema/count/FK/组状态核验保留。成功先交原receipt/hash/完整实际ID给root并结束释放槽，E/Issue下次封，不为行政占新窗口。
