# 数据库模块：OUTPUT-EXCLUSIVE-01窄修复待复审

数据库AI，ROLE-database-OUTPUT-EXCLUSIVE-v1。原c4e8 P2保留，root暂不整合；设计3981e6d先行，窄source `3fc58d18614c394cc588a16b316cf89c1810ecf1` 仅838/836两文件。

- 旧exists→finally路径w写会覆盖后出现结果/跟随悬空link，836零DB main旧源真实2红；首次basetemp父目录缺失2setup errors另保留，不算产品红。
- 改为一次O_CREAT|O_EXCL|O_NOFOLLOW/0600开叶节点，持固定fd写JSON，不重开路径/截断/失败降级；fdopen失败close，recipe异常记失败后原异常传播。已有对象/竞争新结果拒绝；路径替换只写原inode，不能承诺外部路径名不可变。
- 源commit后836全11pass/0failure/error/skip，每main断言DB/application导入为空；一条原JUnit warning保留。两源Ruff/format通过，未执行真实recipes/19矩阵/SQLite/MySQL/HTTP/负载/全CI。
- 15份c4e8原公件/旧prompt、原recipes/provenance逐字不变，旧71Rows/旧E seal保留。新[报告](../../agents/database/output-guard/report.md)、verification/fs观测、红绿日志/JUnit及evidence-seal.json归档；不以旧矩阵证明新工具全套通过。
- [Issue4阶段评论](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6383619265)已精确GET全文同。等待原审核岗对准确SHA复审；未关闭P2，不将输出guard修复称性能/502修复，生产及原公开性能失败不变。无私有env/独立用例或root工作区写入。
- 全量diff-check因原始失败log/XML尾空格exit2保留；源码/说明限定check exit0，未修剪原日志，未冒称全量检查通过。补充E seal不改窄source3fc或测试结果。
