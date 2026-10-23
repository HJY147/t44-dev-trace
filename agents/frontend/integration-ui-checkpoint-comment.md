岗位 frontend；Prompt-Ref: ROLE-frontend-INTEGRATION-v1；Refs: #2。

正式审核 C-P1/C-P2 最小修复：迭代改期读取冻结 `record.plan`，容量和名称可预填，迭代下拉/标题读取嵌套名称；历史重放不再拿原响应任务状态冒充最新状态，提示明确历史结果和当前详情。

把原先错误flattened夹具改成冻结结构并验证Iteration；新增回归先得到3失败21通过（日志保留），修复后24/24通过。全frontend/src TS/Vue分母：行92.19% (307/333)、分支86.76%、函数83.78%；vue-tsc/build通过，保留构建体积提示。产物：frontend/src、tmp/frontend/981-983、agents/frontend/integration-ui-*。

该checkpoint尚未宣称完整后端通知/升级已读处理浏览器回归或CSS清理完成，后续继续。未改审核959断言，需审核owner复验；非独立验收结论。
