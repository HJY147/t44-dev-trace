# ROLE-deployment-NATIVE-CAPTURE-TIMEOUT-v1

固定部署岗已发表P2的实际窄修任务；不是用户亲自改码、独立验收或同一提示词的凑数演进版本。

## 总协调实际派工原文

现在槽位已释放，继续既有deployment岗位，仅窄修已发表P2超时。审核最终 c6883f2bd4e860737f4aede4002f4499d2a7e479，报告 reports/reviews/34-5ef1bde95e511c14dcff7b5fa0af2449de83836c.md、公开反例 agents/reviewer/evidence/native-application-189a4e2/capture-timeout-exit-zero-probe.json/.log 可读，PR34 COMMENT5634837225精确5ef原失败保留。先补现有design/RFC再产品capture：超时必须receipt记录timed_out=true并失败，即使SIGTERM后childrc0也失败；同时保留actual child returncode。不跑完整cycle/服务/63中性/无关守卫；只同一反例原断言绿+正常0/普通非零/超时后0与非零等必要合成影响边界，实际源hash/退出码/原red保留。你原0a6真实cycle成功不倒填新代码已cycle验证。完成真实prompt/日志/报告/handoff+commit push，PR34当前head/body准确更新及Issue7实际读回，封档结束给我复审窄变更。暂不增加serve或额外功能，资源中性元数据root自己处理中。

## 作用与产物

先补application-design.md的超时事实/实际退出码/清理未确认勘误，随后仅改application.py capture和现有871受影响合成边界。公开原红/SHA、同例红绿、五项合成结果、实际源hash、GitHub精确回读与三份角色记录单独归档；不读实际凭据、不重启任何服务、不把历史cycle成功写成新修复已实跑。
