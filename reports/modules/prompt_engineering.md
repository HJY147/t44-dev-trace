# 提示词工程岗位 M3 事实材料报告

## 任务与边界

- 岗位：prompt_engineering；实际派工 ROLE-prompt_engineering-M3-EVIDENCE-v1。
- 已读根 AGENTS 与本岗 TASK；本轮只整理已公开来源，不实现或修改产品代码。
- 独立树 `.agent-worktrees/prompt-engineering-m3-evidence`；分支 `codex/prompt-engineering-m3-evidence`。
- 基线 8fb74cdf893d83413338f966156274fe58caf22b，增量来源分别标完整 SHA。
- 性能窗口内无本机测试、构建、渲染、业务请求；不占根索引。

## 当前产物

- `docs/prompting/M3-evidence-checkpoint.md`：需求到设计、真实 prompt 族、9 条 AI/工具事实映射与缺口。
- `docs/prompting/M3-source-inquiries.md`：四岗真实异步问取，backend 已回复，其他未收到，不代填。
- `docs/prompting/M3-source-manifest.json`：30 处已发布 Git 对象/hash、公开仓库/状态/CI/JUnit 回读。
- `docs/prompting/evidence/gha-39937368245.*`、`gha-39938619826.*`：指定 FE/BE 远端元数据及明确脱敏副本。
- `docs/prompting/highlight-candidates.md`：补 U001/U002 的真实 Issue、PR、commit 证据。
- `records/prompts/ROLE-prompt_engineering-M3-EVIDENCE-v1.md`：实际派工脱敏快照，学生具体姓名不公开。
- 本岗 WORKLOG、handoff、GitHub M3 评论正文同步更新；旧原始记录保留。

## 事实与归属

- U001/U002 原创归用户，U003 是公开补充；U001-O1/U002-O1 仍 proposed。
- D001/D004 是实际用户采用决定，不计用户亲改代码或本人识别缺陷。
- CONTRACT-v1→审核失败→CONTRACT-v2 是两版同一设计任务；不足六版。
- FE 集成的实质反馈与编号/身份/数据准备续条分列，不把协调消息凑优化版本。
- ROOT-documentation-M3-DIAGRAMS-v1 明确为事后目标重述，不计实际派工演进。
- C-P1/P2/P4 是审核 AI 复现，C-P3 为原政策统计超限；owner 修复不是学生亲改。
- 学生研究正文及个人收获只能本人写；本岗仅给事实、来源和问题提纲。

## 公开证据与验证范围

- 精确 e01 的 reviewer/stage=failure 已远端回读，保留原失败，不覆盖为新 HEAD 通过。
- FE b485 的 run39937368245、BE64b4 的 run39938619826 四 product job success，原日志均317通过。
- BE 发布 JUnit 已只读解析为317、0失败/错误/跳过；不把它记为本岗执行测试。
- 原日志 SHA-256 和远端链接保留，公开副本删除凭据相关行并注明脱敏，不称逐字原件。
- 资料仅做 JSON/引用/差异格式静态核对，不以产品测试冒本岗验证。
- 未联系测试，未读取未发布黑盒文件或私有用例；尚未收明确发布的独立最终报告。

## 输入输出与交接

- 输入：用户原文、实际派工、已发布 owner/reviewer 资料、公开 Issue/PR/CI。
- 输出：事实 checkpoint、作者边界、演进族和缺口，交总协调及文档岗。
- 未收到的异步回复按状态注明；后续消息作为新补充，不倒填历史问答。
- 本轮没有新增业务接口、冻结规范或规则决定，不改原文/他岗文件/共享 ledger。
- GitHub Issue11 记录真实交流；仅在本岗树显式暂存，阶段 commit/push 后交完整 SHA。

## 未达标与限制

- 单一 prompt 六版尚未核实；人工修改≥12、本人人工识别≥3、人工校正映射≥5的本轮可证实数均0。
- 9 条 AI/工具映射仅为事实素材，不充抵人的经历；数字只指本轮已收证据。
- 产品实现已由各岗推进，本岗实现状态“未实现”仅指未实现产品代码，不表示全项目没有代码。
- 新 SHA 审核、最终规模、正式性能、独立验收及学生成稿分别待证，不宣称总验收。
