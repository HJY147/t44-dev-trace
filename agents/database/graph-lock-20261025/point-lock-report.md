# 逐点任务锁工具修订

数据库 AI。设计24ca1db先行，初始工具源ee12656513af846c441e20ef858c6aee1126e8dc，最终工具源da166fea52abc25089bbd7001ae50bc686c6a180（probe SHAbf9bbedd1dd09196c99ca986a3072a3a506b5b9ffda38f48fc1e5dcd11af37a4）；无生产/DDL/Rows/API/池变更。静态读取BE c8cea7e真实 Runtime SHA9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b，与root准入方向相同。本岗未执行MySQL、HTTP或云，不代宣布候选准入/测试通过。

- 项目门三读图action S，其余writers X，原 target+pred set sorted逐个 scalar id+project/limit1 FOR UPDATE。每条至多一任务行，显式多任务X请求顺序由语句先后保证；原Business必须等全部锁完后再重读/决策。D前驱变成D+1锁SELECT，较原batch多D，不以静态S兼容推断总体更快。
- 本轮审查未发现这个修订新增结构性反例。仍只证明显式任务id请求顺序，不声称secondary/clustered/FK/其他旧非图路径都有全局全序；共享pred仍串行、部分锁已获后异常应由原UoW整体回滚。原S+batch风险说明保持旧source，不改写成它已解决。
- 833新增必需 `--expected-task-lock-shape batch|point`。真实 Runtime.locked_scope 内临时观察当前UoW的原gateway.rows，始终调用原方法、finally恢复；点模式断言selector全为scalar且limit1、ascending unique且集合相等，batch模式断言原一条集合，实际cursorSELECT事件数与呼叫数一致。不输出绑定id。
- SQLAlchemy事件只采同worker上下文里真实tasks FOR UPDATE SELECT的形状SHA；可信原语句与绑定仅留内存供EXPLAIN。每种实际shape最多一次、总上限8，记录真实plan和source说明；不再生成旧IN查询给candidate充证据。6个低层门控case仍保留两共用pred、反向编号不交集、精确request/block connection/table边和同时两project RECORD GRANTED S。
- fixture前先实际查询P_S三表的 LIMIT0 投影作为readiness。1142等异常类/数字码记在performance_schema_readiness和active_phase，不写成锁case失败。root只需给实际fresh诊断账号 SELECT on data_locks/data_lock_waits/threads；不需要P_S全库、PROCESS、UPDATE。依据见设计勘误中的官方MySQL8.4链接，本岗没有执行GRANT。

8个原工具guard更新新必需参数后再次8pass/0fail/0error，0.39s；root明确LIMIT0 readiness后3dc8655再同8pass0.39s，point-tool-final-junit.xml单列。原7pass/1fail及后续各轮原件保留；这些是同8工具检查，非累加的新用例。它们只覆盖join/拒绝/排他输出，不验证新增真实MySQL观察分支；这些分支待root freshCI实跑。新两脚本Ruff、staged diff-check通过。

首次多段patch因实际format后的explain函数换行不同而拒绝；git diff核无部分写，读准原件后分两段应用。不将编辑器拒绝当产品红。工具source checkpoint已先发root/BE，不等文档完成才给技术接口。root明确baseline/candidate为两个独立fresh jobs/独立MySQL service，均精确t44_diagnostics，不扩大本工具allowlist；另HTTP job的t44_gate_http不是本工具目标。

两DBjob推荐命令仅由root执行（CI=true、URL和T44_DATABASE均精确t44_diagnostics，已由root迁移/授三表SELECT），输出父目录随本stage已存在：

```sh
PYTHONPATH=backend python tmp/833_database_performance/833_mysql_lock_probe.py --allow-fresh-mysql-ci --expected-reader-lock update --expected-task-lock-shape batch --expected-runtime-sha256 8802416ee003a464a8433eed80890a1c2069550ff4717ca5e07a10cf2b840b48 --output agents/database/graph-lock-20261025/mysql-lock-baseline.json
PYTHONPATH=backend python tmp/833_database_performance/833_mysql_lock_probe.py --allow-fresh-mysql-ci --expected-reader-lock share --expected-task-lock-shape point --expected-runtime-sha256 9e0d770e4d5a646b406e1b1a3e328a7e369219d8821dbfcc008303547fe6825b --output agents/database/graph-lock-20261025/mysql-lock-candidate.json
```

阶段Issue4评论6394684218已实际POST并单ID全文读回一致，见point-lock-github-readback/verification；最后LIMIT0四行修正的完整source另做后续评论回执，不回写原公开文本。

实际提示词 ROLE-database-MYSQL-POINT-20261025-v1，见point-lock-prompt.md。后续MySQL/HTTP结果与真实source由root单独归档，不把本地guard冒充并发通过，旧云/规模/人工报告出口仍开放。

LIMIT0之后首次format check因一行字符串拼接返回1，原诊断摘录保存在point-lock-verification.json。formatter只改该行，最终da166fe AST机械比较与已测3dc8655完全相同，最终check/format check均0；没有额外重跑工具8项。

最终完整source与hash后续已实际发表[Issue4评论6394701321](https://github.com/HJY147/t44-dev-trace/issues/4#issuecomment-6394701321)，单ID GET完整body与本地final-comment精确相同，point-lock-final-readback/verification保留原件。
