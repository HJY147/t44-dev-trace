Agent-Role: messaging
Prompt-Ref: ROLE-messaging-SIZE-20261025-v1
Refs: #5

2026-10-25 结构规模checkpoint已提交并推送：c4b3f114a5525c0fe0fd031d2b3603070a2be892，分支codex/messaging-size-20261025，基于396b646adb87de183929ac6fc46bbe7e88074c8a。仅stage push使用[skip ci]，不改门禁；root统一完整CI。

先写tmp806_newscope设计/静态调用图再首次计数；固定cloc2.10工具SHA与原classify不变，已提交快照application5875→5862，真实净13（Facade95→85、Broker129→126）；消息合计357→344，其余application逐文件均不变。没有压格式、迁生产代码、删功能/鉴权/锁/事务/CAS/幂等/重试/DLQ/恢复。未达到100–200，主应用仍超762，不声称达标。

去重是共用active成员/项目范围与已有page，以及四种broker网络错误的脱敏清理单点。明确保留connect/publish/get/heartbeat错误区分、False NACK边界，ValueError子类仍进DLQ。Worker/main没有为数字强拆helper。

既有开发17项在基线/候选均通过；新增806性质/故障22项在未修改基线backend包也通过；当前总39通过、23 integration不执行。Ruff通过。首次pytest无配置0收集exit5及新用例4个C408的原始日志均保留，仅修命令/测试字面量，不降门禁。未读其他runtime/凭据、独立材料，未跑真实组件/全CI/云/正式验收，历史通过不外推。

root已确认跨岗候选本轮只设计交接：调度event投影复用model；ScanStore.start与调度_run统一同gateway原语/默认字段；BE拥有的outbox信封纯值原语。都须在原有UoW内使用，不能新开事务；预算互有交叉，不能相加当已实现收益。

证据：agents/messaging/tmp806_newscope/{DESIGN.md,RESULT.md,before.json,after.json,before-properties.log,after-properties.log}；代码/测试/日志/模块报告/handoff/prompt均由AI消息岗实际操作，不冒人工亲改。
