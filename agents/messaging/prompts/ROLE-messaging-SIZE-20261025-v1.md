# ROLE-messaging-SIZE-20261025-v1

本岗为总协调本轮真实派工标注的ID；实际操作者为AI消息岗。不是人工改码，也不是为凑版本制造优化。

实际派工原文：

> 继续本项目消息模块真实规模优化，必须在 /Users/yang/Desktop/nothing/软件开发大作业 内，读AGENTS。当前候选coord branch 396b646adb87de183929ac6fc46bbe7e88074c8a（已push，固定cloc5875超775；基线e45→域V2净370、DB seedV2等净90已组合，四job CI40193412286进行中）。你负责 backend/t44/messaging/ 与 scheduler岗协作；当前max4并行root+backend-size+deployment+你，不得再派agent。请新隔离worktree/branch codex/messaging-size-20261025 从396b646建立，自己的tmp806_newscope（递减编号，文件实测前先设计），做消息/调度跨重复静态调用图设计，优先消息facade/broker/worker真实可维护结构消重复，目标真实净100–200若能证明；不重格式、不删功能/鉴权/事务/幂等/重试/死信/通知恢复、不迁代码出计数目录、不改固定DDL/OpenAPI，不盲目复杂抽象。scheduler目录可只读；需要跨岗sharedhelper先root确认。你可提出明确需调度岗配合的候选，root排下一批。开发pytest可用 .agent-worktrees/backend/.venv/bin/python，PYTHONPATH自己backend；工具仅可读已知cloc .agent-worktrees/.runtime/cloc-2.10.pl SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83；不可读任何其他runtime/credentials、tmp809/814/817/818/829等独立材料/历史私有。只模块开发目标不跑全CI/云/正式验收。每个真实候选保留before/after、性质/故障回归，WORKLOG/module/handoff/prompt、commit与Issue5真实交流；只metadata或stage push可skip ci但不改门禁，root统一合并全CI。先十分钟内给结构预算和可行方案，再实施；做不到100实报而不强凑。用户要求持续工作达标，但质量与原始失败必须真实。

对应产物：tmp806_newscope设计/固定计数/性质对照证据、消息Facade/Broker候选、tmp/backend/messaging/806_newscope.py、工作日志/模块报告/handoff及Issue5评论。

边界：先设计预算再实测；只访问指定cloc工具和获准Python环境，不读其他runtime/独立材料，不改调度、数据库、共享API或门禁。本轮不是业务规格变更；未授权新sharedhelper不自行新建。
