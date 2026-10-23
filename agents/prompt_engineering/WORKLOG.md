# 提示词工程岗位工作日志

## 2026-10-23 初始化

- 实际派工：`ROLE-prompt_engineering-BOOTSTRAP-v1`；依据 `agents/prompt_engineering/TASK.md`。
- 实际操作者：AI 提示词工程岗；决策范围为当前授权的记录结构和忠实优化，不代表用户审定业务规则。
- 读取：根 `AGENTS.md`、团队规范、报告模板及任务书/提交注意/作业要求三个提取文本。
- 读取并保留 `records/prompts/U001-original.md`；未改动原文和共享 `ledger.jsonl`。
- 首先创建 `U001-optimized.md`、`U001-changes.md`，向总协调报告其建议稿状态和范围边界。
- 创建实际派工正文快照，区分实际岗位派工与 U001 未使用优化稿。
- 创建 `docs/prompting/prompt-recording.md`，约定台账、真实演进、上下文映射、人工改码、幻觉及规则变更记录。
- 本轮没有业务编码，没有联系独立测试岗，没有独立测试或产品验收。

### 实际命令与结果

| 命令或操作 | 真实结果 |
| --- | --- |
| `pwd && rg --files -g 'AGENTS.md' -g 'TASK.md' -g '*U001*' -g '*instruction*' -g '*prompt*' .` | 确认任务根目录和现有岗位/原文文件。 |
| `cat AGENTS.md`；`cat agents/prompt_engineering/TASK.md` | 读取责任边界和本轮范围。 |
| `cat records/prompts/U001-original.md && rg --files agents/prompt_engineering records standards docs`（实际追加 `head -120`） | 读取原文；探索性查找提示 `standards` 目录不存在，其余文件列表有效，未据此创建额外目录。 |
| `cat docs/collaboration/team.md && cat docs/collaboration/report-template.md` | 确认交接字段与测试独立性规则。 |
| `cat specs/sources/T44-taskbook.txt && cat specs/sources/submission-notes.txt && cat specs/sources/homework-requirements.txt` | 核对至少六版、十二条人工修改、三条幻觉、五处映射及提交物要求。 |
| `ls -la records/handoffs reports/modules agents/prompt_engineering docs/prompting records/prompts && cat records/prompts/ledger.jsonl` | 确认自己的资料尚未建立，共享台账只有 U001 原文登记。 |
| `apply_patch` | 创建本岗资料；只写获准路径。 |
| `date -Iseconds && shasum -a 256 records/prompts/U001-original.md` | 时间 `2026-10-23T11:41:24+08:00`；原文摘要 `12d669f69c1bf3948745fe17e2fb32ccb637c984df0d168a056f4579473abafa`。 |
| `python3` 内联文档静态校验脚本 | 14 项检查全部通过，模块报告为 50 行；证据为 `records/prompts/prompt_engineering-bootstrap-validation.json`。 |

### 当前记录与后续事项

- 自查已核对文件存在、UTF-8 非空、交接 JSON 必需字段与引用、建议稿状态、报告行数及原文摘要；不把静态资料检查算作模块测试或独立验收。
- 需总协调登记本轮实际提示词与产物引用；本岗未修改共享台账。
- 后续真实开发时再收集上下文映射、人工改码和幻觉证据；当前均未达到最终数量要求。

## 2026-10-23 GitHub 要求追加整理

- 实际派工：`ROLE-prompt_engineering-GITHUB-v1`；读取 U002/U003 原文、更新后的根规范、团队规范与 `docs/collaboration/github-workflow.md`。
- 创建 U002-O1 优化建议稿与修改说明，明确公开开源来自 U003；未将建议稿标为已使用。
- 创建 `docs/prompting/highlight-candidates.md`，将 U001/U002 列为用户原创候选，列明 Issue/PR/commit 等证据要求及不能提前声称的效果。
- 保存本轮实际派工正文；更新本岗报告和交接。未写产品代码，未修改原文或共享台账，未联系独立测试。
- `shasum -a 256 records/prompts/U002-original.md records/prompts/U003-original.md`：原文摘要分别为 `54db3212d69faa2c75201f4fc88dbcd8b0bfd0245eb69f8f5c18da3094bb0c55`、`9af1aba831ac54641e3219e0b0f835cd9aaddfac46add05d5cb75a65e4f74721`。
- `git rev-parse --show-toplevel`：确认工作根为 `/Users/yang/Desktop/nothing/软件开发大作业`；未操作共享 Git 索引。
- 总协调已确认本轮先完成资料并交接，不操作 Git 索引；后续再指派本岗 Issue、分支与独占提交时段。本岗不替其他岗提交。
- `python3` 内联静态校验：15 项通过，模块报告 53 行，U002/U003 摘要未变；证据 `records/prompts/prompt_engineering-github-validation.json`。未执行产品测试或 Git 提交。

## 2026-10-23 M0 文档问取与阶段提交

- 实际问取/派工：文档岗发送 `ROLE-prompt_engineering-M0-COMMIT-v1`；已明确分配 Issue #11、`codex/team-bootstrap` 及本岗独占 Git 索引时段。上述历史未分配/不操作记录保留，现由本次授权进入阶段提交。
- 文档岗询问：真实产物、实现与执行状态、对接缺项、日志及 prompt 位置；要求记录问答、发表阶段评论、仅提交本岗文件并返回 SHA。
- 本岗实际回答：已产出 U001/U002 优化与修改说明、真实派工、记录规范、亮点候选和两轮静态证据；产品未实现，模块/集成/独立测试未运行，U001-O1/U002-O1 为 proposed，真实 ROLE 派工为 used。后续待真实 Issue/PR/commit、审核、效果和最终留痕证据，不需开发岗接口提问。
- 回答同时提供本岗 WORKLOG、`records/prompts/` 与模块报告位置。文档岗的收集记录引用 `docs/reports/collection-log.md`、`collection-events.json`，本岗不修改。
- `git branch --show-current && git diff --cached --name-only && git status --short`：分支确认为 `codex/team-bootstrap`，初始暂存区为空；其他岗位未暂存文件保持原状。
- 创建本次实际派工快照和 `agents/prompt_engineering/github-stage-comment.md`；不新增研究设计，不联系测试，不改共享 ledger 或用户原文。
- `gh issue comment 11 --repo HJY147/t44-dev-trace --body-file agents/prompt_engineering/github-stage-comment.md`：成功发表评论 https://github.com/HJY147/t44-dev-trace/issues/11#issuecomment-6358401077。
- 已显式 `git add --` 本岗交接列明的 15 个文件；`git diff --cached --name-only` 与清单完全一致，`git diff --cached --check` 通过。未加入用户原文、共享 ledger 或其他岗文件。
- 本条记录随 M0 提交归档；完整提交 SHA 由提交返回后交文档岗记录，不在提交内预填自身 SHA。未授权 push、checkout、merge 或审核通过。
