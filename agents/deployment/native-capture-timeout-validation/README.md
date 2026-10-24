# NATIVE-CAPTURE-TIMEOUT-01 窄修证据

审核归档c6883f2绑定原候选5ef1bde/原实际运行实现0a6da88。原审核COMMENT5634837225及原红不改；`reviewer-original-red.json/.log`逐字复制与来源SHA见design-checkpoint.json。新实际派工为ROLE-deployment-NATIVE-CAPTURE-TIMEOUT-v1，先行设计提交7f4845e。

`same-counterexample-before-fix.*`在未改原capture上执行同一公开断言，真实1项失败/exit1；没有新OS进程或真实信号。修后`capture-final-five-boundaries.*`仅执行现有871的CaptureGuards类五项，全部通过：

| 场景 | 实际child rc | timed_out | 结果 |
| --- | --- | --- | --- |
| 正常0 | 0 | false | success=true，正常返回 |
| 普通非零 | 7 | false | success=false，OWNED_COMMAND_FAILED |
| 首次超时、清理后0（原反例） | 0 | true | success=false，OWNED_COMMAND_TIMEOUT |
| 首次超时、清理后非零 | -15 | true | success=false，OWNED_COMMAND_TIMEOUT |
| 清理等待仍超时 | null | true | success=false/stop_unconfirmed=true，COMMAND_STOP_UNCONFIRMED，部分输出摘要保留 |

Popen、身份观察、等待及SIGTERM全部替身；真实OS进程/信号为0，没有构造Application、打开真实凭据、访问服务或重跑cycle/其他守卫。Ruff原classvar提示保留于ruff-initial-classvar.*，补注解后ruff-final.*通过。scope-and-source.json核除capture外application AST相同，旧ApplicationGuards类相同，runtime.py无变更，并记录精确前后SHA。

原run1失败与原0a6 run2 driver0/cycletrue/cleanuptrue历史均保持；新代码只取得上述合成结果，未被完整cycle、独立、性能或云验证。根后续专项复审决定本P2状态，本岗不将修复自检写作审核放行。
