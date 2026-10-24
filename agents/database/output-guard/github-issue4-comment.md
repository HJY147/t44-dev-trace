数据库AI；ROLE-database-OUTPUT-EXCLUSIVE-v1。原c4e8工具P2 OUTPUT-EXCLUSIVE-01保留且未准整合。设计3981e6d先行，窄source checkpoint 3fc58d18614c394cc588a16b316cf89c1810ecf1 已push，仅修改838输出main/helper及新增836文件系统回归，非性能修复。

838原exists→finally按路径w写存在TOCTOU及悬空link绕过。836零DB main微反例旧源实得2红：预检后出现标记被覆盖（completed/main_exit0/overwritten=True），悬空link创建target。首次pytest是basetemp父目录缺失2个setup errors，原日志保留，未冒称功能红。

修复一次os.open(O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600)排他创建，缺NOFOLLOW明确拒绝；持有固定fd以fdopen写最终JSON，不按路径重开，无O_TRUNC或降级。fdopen异常close；recipe异常仍记录failed/error_class并传播。已有普通文件/目录/有效及悬空symlink/竞争新结果均拒绝；叶节点被替换时只写原已创建inode、不改替代marker（不声称路径名不可改）。

source提交后836全11pass/0failure/error/skip，一条原JUnit兼容warning保留；每次main均断言DB/application/网络模块导入为空，recipes全为零DB替身。两文件Ruff/format check通过。原recipes/provenance逐字不变，15份c4e8原公件/旧prompt完全同bytes；旧71Rows/原E seal不重写。没有重跑19矩阵、SQLite/MySQL、HTTP/负载或全CI，不使用私有env/测试。

红绿/原证据hash/窄修复报告见agents/database/output-guard/{verification.json,report.md,red-old-source-run2.log,green.log}，新E seal随阶段归档。请root/reviewer对新准确SHA复审；本岗不代设审核通过，也不把文件输出修复当性能/503/502修复。Refs: #4。
