# OUTPUT-EXCLUSIVE-01：排他输出窄修复设计

数据库AI，ROLE-database-OUTPUT-EXCLUSIVE-v1；独立codex/database-output-guard，基原c4e8c696411975ee6964ef3b2254c8f3937ecb32。原P2是Path.exists与finally按路径w写之间TOCTOU：悬空symlink不被exists发现，预检后出现文件会被覆盖。总协调已公布零DB微反例；不读取审核/测试私有脚本/env，不改根工作区。原19配方/71Rows结果与原E seal按c4e8字节保护，不重跑矩阵。

先设计提交，再在分配tmp/836_database_output_guard中写零DB回归。红阶段：只替换838.recipes为零DB函数，provenance完成后放原结果标记，证明旧main完成且覆盖；目标新断言须红并保留标记变化。正常已存文件/目录、有效与悬空symlink、正常新输出、recipe异常记失败并传播、显式run/import边界一并验证。以目录内真实临时文件和内联模拟配方验证文件系统，不加载DB/application。

窄修复：删除exists预检的保护假象，保留run/源字节检查；完成只读provenance后，父目录创建一次，os.open输出叶节点使用O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW、mode0600，O_NOFOLLOW不可用则明确拒绝；已有任意文件/symlink均排他拒绝，不跟随。不做exists→open序列，不用截断flag，不失败后退回w。

成功独占创建后立即将此固定fd交os.fdopen并持有至finally/close，仅向该fd写最终JSON，不再按路径重开；recipe异常仍向同fd记录failed/error_class后原异常传播。即使输出路径在recipe内改名/被替换，写入仍落原已创建inode，不覆盖新路径标记，回归保留该fd语义（不声称路径名对同用户外部修改保持不变）。os.fdopen初始化失败要close原fd，正常/异常路径均关闭。文件创建/写失败保持原OS错误或CLI明确拒绝，不隐瞒。

必要验证限836零DB回归、838/836源Ruff/format与导入门禁；工具源码先提交才能通过原commit字节守卫。禁止真实recipes、SQLite矩阵、MySQL/HTTP/负载/新CI验证；这只是诊断工具输出安全修复，不是性能修复。保存旧源红→窄source checkpoint→同断言绿、原证据hash、Issue4 COMMENT精确GET及新的阶段E seal，交root/reviewer复审而非自称审核通过。
