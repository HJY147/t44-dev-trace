# 完整产品审核v1：首次缺陷checkpoint

## 1. 对象与基线

Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-PRODUCT-v1。PR21/Issue12，精确被审head `e01f5dcf9d8ef5a88161fcbc87ab142fba74cdef`，冻结1.0.0/D001/D003/D004及原始T44/课堂提交要求。独立分支codex/review-product-v1，不修改owner代码/root索引。本checkpoint不是审核完成或产品放行。

## 2. 需求映射

C-P1对应FR-01/04的冻结Iteration响应及既有计划保留；C-P2对应D001“重放结果是原操作快照，前端再查询最新状态，不误当现在的版本”；C-P3对应有效代码3500–5100行。完整38API、权限/状态/事务/消息/扫描/部署/M2均为本轮范围，尚继续实查。

## 3. 变更与责任边界

本岗只新增报告、审核复现、真实命令输出与本岗日志/交接。前端责任岗修复C-P1/C-P2；root负责整体规模调度。959编号先经root登记；不修改现有用例或弱化断言，不接触私有独立用例/日志，不与独立测试通信。

## 4. 接口与数据兼容

**C-P1 [P2] Iteration客户端读取位置与冻结响应不一致。** `frontend/src/forms.ts:15`从record顶层逐字段建plan；冻结Iteration仅在record.plan存IterationCreate字段。契约形状record打开调整后得到`{expected_version:3,plan:{}}`，原名称/时间/容量/缓冲/延期预案全部丢预填，用户被迫重输。`frontend/src/components/FieldEditor.vue:17`同样用i.name，真实迭代选择无名称。现有`tmp/frontend/981_fixtures.ts:12`把Iteration扁平化，983仅验证表单存在，因而未检出真实形状差异。修复应使用record.plan/i.plan.name，并让夹具受冻结响应校验；不能改契约迁就夹具。

**C-P4 [P2] 已迁移结构检查仅比较约束/索引名称，漏掉语义漂移。** `backend/t44/persistence/migrations.py:57-77`只把index/unique/FK/CHECK取name集合，未比列序、unique、FK列和目标或CHECK表达式；`migrate:127-133`已应用路径依赖它判结构相符。957在隔离Inspector替身保留18表226列类型/default及名称，将索引列/unique、FK目标与CHECK改为不同语义，仍返回passed=true/defects=[]；期望拒绝的断言失败。仅证明检查器错误接受，不声称真实MySQL已漂移。DB责任岗修复检查和新负例，保持冻结DDL不变。原始输出957-schema-probe.log。

## 5. 业务正确性

**C-P2 [P2] 幂等重放历史状态覆盖刷新后的当前状态提示。** `frontend/src/components/OperationForm.vue:37-40`等待saved刷新后又以result.data.task.state拼“任务现为…最新记录已刷新”。959在明确mock重放state2/version2、saved权威刷新state6/version9时，最终仍提示“任务现为开发中（同一操作结果已确认），最新记录已刷新”。这不改变服务端数据，却向操作者错误确认当前状态。应以权威查询结果给当前状态，或仅说明原操作已确认且最新数据另查，不从历史响应作当前状态断言。

## 6. 实际执行与证据

959为真实Vitest5.0.5/happy-dom组件复现，指定目标代码、既有依赖clone后在本岗树执行。命令及临时配置在`agents/reviewer/evidence/product-v1/959-ui-command.json`，stdout/stderr在959-ui-probe.log；2项期望正确行为的断言均失败，未宣称浏览器/真实HTTP/独立验收结果。复现源`tmp/reviewer/959_ui_contract_probe.mjs`。

原统计脚本、政策与固定cloc2.10不变，精确e01运行`source_count.py --require-range`得到5944有效行，退出1；原始source-count.json及命令回执保存本岗证据。

## 7. 问题与十项判定

| 项 | checkpoint判定 |
| --- | --- |
| 1 身份/版本 | 通过：独立树、精确e01、非自审产品 |
| 2 需求/范围 | 不通过：**C-P3有效行5944，超5100上限844** |
| 3 接口兼容 | 不通过：C-P1真实响应形状未正确消费 |
| 4 数据兼容 | 不通过：C-P4兼容检查漏语义漂移 |
| 5 状态机 | 继续审核；C-P2显示状态与权威当前值冲突 |
| 6 权限/秘密 | 继续审核，未作最终通过 |
| 7 事务/并发 | 继续审核，未作最终通过 |
| 8 幂等/故障 | 不通过：C-P2前端误读历史快照 |
| 9 测试真实性 | 复现是真实组件断言；发现原夹具偏离契约，CI绿不替代审核 |
| 10 门禁 | 不放行；性能/独立未完成，完整审核尚未结束 |

## 8. 结论与复审

当前精确e01不能放行。先交责任岗修复上述两项可复现前端问题、Schema检查器漏检并按原政策减量；代码变化后绑定新SHA做差异复审，首次失败证据保留。本checkpoint不发success/APPROVE、不合并。其他检查结果及减量建议另补完整报告，不把尚未核实的风险当缺陷。
