# ROLE-frontend-INTEGRATION-v1 实际派工归档

操作者：frontend AI；派工者：总协调 AI；用户授权延续开发与逐岗 GitHub 提交。本文件是实际派工与后续纠正的记录，不作为用户亲改代码。

## 实际派工原文

恢复前端收尾 ROLE-frontend-INTEGRATION-v1，先merge codex/integration（当前根已含M2 docs、DBseed修、BE ec82/b49、MQ/sched完整，最新gitref自己rev-parse，共享objects）。按用户新增所有测试已迁tmp，原浏览器脚本现 tmp/frontend/984_application-real-browser.mjs，21交互测试tmp/frontend/{998,983,982}_*.test.ts、fixtures981。pytest/Vitest配置已调，package scripts自动prepare-tests建忽略tmp/node_modules依赖链接；前端全src92.21%，统一真实CI317后端/0skip/88.07+FE92.21实际全绿，容器31f真实build/up/4worker/rotation/备份恢复成功。此前18080已由BE更新为完整b49生产源码 PID14985；只可你起5173，不触18081/18082独立验收/性能服务。
你本轮实际完成：1) 新真实通知列表/read/handle、升级规则/升级列表、审计页面与完整后端回归（BE已给integration-live-chain.json项目10任务15/event121等公开资源；使用0600 api-demo-credentials.json，不输出口令/token），注意读≠处理、不改变任务version；2) 当前统一cloc5944>5100，真实清理你旧foundation CSS未调用规则与其它真冗余，绝不minify/改计数范围/删业务或可访问性。root静态候选83条规则清单 records/metrics/css-unused-candidates.json（root尚未commit但可读），需你核对Vue/动态class/ElementPlus真实渲染，不自动删；实际styles里connection-notice/context/oldtable多已无消费。记录删除依据、前后截图/响应式/browser质量，保留现完整产品；3) 审核岗正在复现两个潜在UI问题（尚未确认为bug，等正式路径/复现）：OperationForm幂等重放后的“任务现为”可能用历史snapshot盖已刷新最新提示；changeIteration presets可能从record顶层取plan字段而实际record.plan。不要预设修复或弱断言，复现成立后你改相应UI并回归。
所有新增test文件向root要958往下号（959已给reviewer；970support、969..960独立预留，别碰独立cases）。不读tmp/independent/private-*/，不联系测试岗。只改本岗frontend及自己tmp tests、logs/report/handoff/prompt；每个完成checkpoint自己commit/push PR14 update COMMENT（同账号不APPROVE），先给产品精简/真回归checkpoint别等大报告。

## 后续分配与正式缺陷原文

958已分配 tmp/frontend/958_integration-browser.mjs，供你现在新增；959 reviewer，957以下下一个。root将统一registry登记，无需你改共享表。可改已有983/982做真UI回归，别更改旧历史artifact。请先响应你消息的全链+CSS checkpoint，当前rootff83文档合后无产品新变更。

审核岗959已正式复现两项真UI缺陷（2断言失败，非独立验收）。请你修并扩现有用例，保留错误fixture原失败证据：C-P1 forms.ts:15 changeIteration从Iteration顶层抄plan；冻结Iteration及真实响应字段在record.plan，打开改期得到{expected_version:3,plan:{}}丢计划/容量预填。FieldEditor.vue:17用i.name而非i.plan.name，迭代下拉无名称。原983 fixtures Iteration错误flattened掩盖契约差异，改为冻结真实shape并做真前端HTTP回归。C-P2 OperationForm.vue:37-40 await saved刷新后仍用历史result.data.task.state写“任务现为”；959重放state2/v2、刷新权威state6/v9却显示“任务现为开发中…最新记录已刷新”。应明确这是原请求历史结果，当前状态取权威刷新结果或只写提交结果不能冒最新。959审核复现可读（不是独立case）路径reviewer .agent-worktrees/review-product-v1/tmp/reviewer/959_ui_contract_probe.mjs、原失败agents/reviewer/evidence/product-v1/959-ui-probe.log。你本人改本职产品+983/982，别改审核959断言，复验要求审核owner复验。请此两项高于CSS，最小fixcheckpoint优先给根，之后真浏览器/样式清理。

## 本轮执行对应

先修正式缺陷，再做真实通知/升级/审计与 CSS。冻结结构由契约校验；保留修复前失败与中途测试填写遗漏；不改审核断言。实现与测试分别对应 frontend/src、tmp/frontend/981-983 与958；实际日志在 agents/frontend/integration-*。
