# DIAG-CLEANUP-01 窄修复与回归

后端 AI，基78bb0ac；先设计bc87197、再冻结834_cleanup测试d167a9f，修复源码b079f84553b8aa91a7f18a7f76f5b6319a2cdc07。仅诊断工具，不是产品业务/云性能修复；原E、六份raw及生产、合同/DDL完全不改。

旧原run在fixture创建前或next中失败时无法保障close：本岗针对旧源实际跑同文件两个目标，2失败/8未选。创建时失败虽原异常仍在，但observer.close未调用；next时失败被snapshot的CleanupFailure盖住。命令、JUnit和原stdout分别保留red-command.json/red.xml/red.log；这不是接口或数据库故障。

修复使run先设置requests；observer/stages/fixture在受控try创建，只有install完整返回后标记installed。finally先保部分requests，分别尝试stages.close、fixture.close、snapshot、observer.close；未请求和未安装明确NOT_REQUESTED/NOT_INSTALLED。任何清理错误只记phase/异常类，不存message/凭据。已有主异常沿原raise保持；没有主异常但有清理错误时抛DiagnosticCleanupError，因此原main会写failed而非completed。

同一834_cleanup文件修后10通过/0fail/error/skip，包含fixture创建/迭代失败、partial install、四种成功体后的清理错误、原异常与四清理错误并存、健康成功、无observer。测试实际调用run，但仅用内存合成的操作/fixture/observer，真实API/持久层/FastAPI/SQLAlchemy/PyMySQL导入被禁止；不是实际HTTP或SQL。green-command.json/green.xml/green.log为原件。未重跑任何56样本或35差分矩阵。

机械AST证明：Stages、fixture、observer_from、main逐字语义AST不变；初始化三语句只是移入try，原测量body去掉新增install成功标志后AST全同。记录于verification.json。b079准确driver SHA为 `6f7c1a2d73079082d3e087e16ec5d888a57d60d80a2d47fe00ba0549c104a626`，根的request/workflow需改用此hash，不能继续用旧150c…哈希。两文件Ruff和format均通过；无新生产/CI/DB/外部HTTP/云操作。

边界：每个清理步骤都会被尝试；close本身失败会记录并导致非绿，不宣称关闭一定成功。JSON输出写入/文件系统硬故障不在此P2范围。旧基线和原型描述性成本、源码6316超限、云839失败及未完成验收保持，等待root限定复审和真正MySQL组合诊断。
