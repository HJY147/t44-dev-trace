# 实际派工（本轮归档标识）

> 审核发现实际P2 OUTPUT-EXCLUSIVE-01，c4e8工具暂不得整合。838第263–264仅Path.exists预检，293–294 finally mkdir+write_text('w')非排他；悬空symlink可绕过、预检后出现的结果被覆盖。审核岗已真实执行main微反例，只将recipes换零DB函数，在预检后放标记：completed且overwritten=true，导入DB/application=[]，无矩阵SQL/HTTP。请新阶段先设计再修O_EXCL+O_NOFOLLOW并持有固定fd写出（不要只再exists）；旧结果/原71Rows证据保持。新回归文件 tmp/836_database_output_guard，覆盖原反例/普通已存/悬空与有效symlink/正常新结果/recipe异常记录等必要边界，不重跑19配方矩阵，不读私有env/测试。自有worktree分支，阶段记录/报告/prompt/commit+Issue4，给窄source checkpoint和E seal供复审，禁止root工作区写入。不把此工具修复称性能修复。审核岗原c4e8报告即将封档，root稍后发精确report SHA。

操作者数据库AI，非学生亲改。

## 总协调实际边界确认

> 已收到窄source3fc58d1，root暂不整合，待你E seal后原审核岗独立复审。836命名保持不再改，837虽未实际使用保留空号。注意全矩阵原件c4e8/71Rows保持，修复只证明输出guard，不复跑矩阵不宣称新工具做过19配方。输出fd身份/路径被替换时的证据边界按报告明示。
