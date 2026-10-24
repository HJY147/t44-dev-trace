# OUTPUT-EXCLUSIVE-01窄修复回执（待复审）

数据库AI，ROLE-database-OUTPUT-EXCLUSIVE-v1。原c4e8 P2失败保留，仍不得凭原工具声明准入；只用总协调公开描述独立重建文件系统反例，未读取审核/测试私有脚本/env或联系独立实例。设计3981e6d先提交，窄source checkpoint `3fc58d18614c394cc588a16b316cf89c1810ecf1`（仅838与836两个文件）。

## 原缺陷与真实红

旧838先Path.exists，再provenance/recipe，finally按路径w写；存在TOCTOU，悬空symlink也会绕过exists。836只把recipes换零DB函数，其他main/源字节/provenance检查真实执行。provenance完成后在输出路径放原结果标记：旧main打印completed，JUnit main_exit=0、overwritten=True；悬空link旧main也完成并创建target。两目标旧源真实2failed/0errors，原日志red-old-source-run2.log/xml保留。

首次命令因pytest --basetemp的父目录没创建，在两个fixture setup阶段失败；这是2个环境setup errors（red-old-source.log/red-junit.xml），不能算缺陷红。创建本岗目录后才取得上述2个行为红。

## 修复边界

- 移除exists伪保护；保留显式run/工具已提交/13源字节provenance检查。检查完成后一次os.open，flags=O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW，mode0600；已有普通文件、目录、有效/悬空link及竞争新文件均拒绝，无截断flag/无跟随/无失败降级。O_NOFOLLOW不可用时明确拒绝。
- 保留os.open返回的固定fd，以os.fdopen接管；recipe正常或异常的最终JSON只经这个fd写出，不再write_text或按路径重开。fdopen初始化失败显式close原fd，正常/异常with关闭；recipe异常写failed/error_class后原异常传播。
- 测试在recipe内把已预留inode改名，再把原叶节点换成marker，结果marker未改且JSON写入原inode；证明不重开新路径。仅保证此输出叶节点的排他创建和fd绑定，不声称目录/路径名或同用户主动改写的原inode不可变，不承诺路径被外部改名后仍保持可达。
- 原recipes/provenance函数逐字不变；不变更SQLite/MySQL语义、SQL配方或业务代码，不把输出修复称性能修复。

## 11个窄绿与未运行

source先commit/push后，836完整11passed/0failed/0errors/0skip，一条原record_property/xunit2兼容警告保留。覆盖原race、普通已存/目录/悬空/有效link、正常新结果0600/flags/noTRUNC/关闭、recipe异常记录传播、叶节点替换后固定fd、fdopen异常close、无NOFOLLOW拒绝和显式run。每次main的导入跟踪均断言DB/application网络模块为空；没有运行真实recipes。

命令：既有backend/.venv/bin/python -m pytest -c backend/pyproject.toml tmp/836_database_output_guard/836_output_guard.py --basetemp agents/database/output-guard/.runtime/green --junitxml=agents/database/output-guard/green-junit.xml -q。Ruff与format --check仅838/836通过；未运行原19配方/71Rows矩阵、SQLite/MySQL、HTTP/负载或全CI。

verification.json逐文件核原c4e8的15份perf-public-c公件/旧prompt字节完全相同，旧E seal、offline-run1.json/log及71Rows原证据不回写。原旧E seal的toolSHA仍指历史d758，当前修复另有新E seal，不能让旧矩阵冒充新工具完整重跑通过。

当前输出工具P2由本岗窄回归支持修复，最终审核仍由root/reviewer对准确SHA复审；原性能失败与根因未知、无新云窗口等结论不变。公开审核c4e8报告的精确commit尚待协调发送，本岗没有寻找/读取其私有材料。

Issue4实际阶段评论已发表并精确GET全文逐字一致：https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6383619265，github-readback.json保留完整响应。root明确暂不整合、等本E seal再由原审核岗独立复审，836名称保持、837空号不占用。filesystem-observations.json保存红/绿标记及symlink/固定inode的零DB观测；仅本阶段pytest临时目录在提取观测后清理，日志/JUnit/源和原71证据均保留。
