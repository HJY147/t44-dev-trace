# 用户指导岗位报告｜M6 初学者检查点

## 任务与截止

- 实际派工ROLE-guidance-M6-v1，原文在本岗prompts；作者/操作者为AI guidance。
- 独立分支codex/guidance-m6，worktree .agent-worktrees/guidance-m6，源码基点0783a42b26038d7d3e5a1fe07ae8219a47f06493。
- R001只作为学生本人观点；R002只读公开provenance。未写最终学生研究正文。
- 本轮只读代码/公开材料与写本岗MD/JSON；未改产品、测试、冻结规范或共享ledger。

## 实际产物

- docs/guidance/M6-learner-guide.md：简明中文入口、真实函数I/O与边界、5项待做练习和本人空表。
- docs/guidance/M6-actual-qa.md：与backend/frontend各1次真实AI询答，逐字回复和纠错，不称人类访谈。
- docs/guidance/M6-source-manifest.json：45来源文件SHA、40函数位置、源码/验证截止及访问边界。
- docs/guidance/M6-issue10-readback.json：已核对本岗Issue10、真实新评论与逐字readback。
- docs/guidance/M6-document-checks.json：仅文档结构/链接/来源核对，不是产品测试。
- records/qa/question-log.md追加QA-010，保留历史pending并指明D005/D006后续已真实采用。
- 本岗WORKLOG/report/handoff、实际prompt和m6-stage-comment.md同步；历史记录不伪改为当前状态。

## 输入输出与教学纠正

- 输入：R001观点、真实源码/冻结契约、公开准确832验证及root后续组合状态。
- 输出：给初学者的阅读路线、输入输出/副作用解释、未做练习、真实询答与来源清单。
- 真实HTTP入口是create_app.endpoint.handle→Runtime.execute，不存在execute_operation或统一save_task。
- 改期是Tasks.changeTaskPlan→Call.cas→Projects.schedule_diff；业务返回仍在主UoW内，audit/outbox/幂等快照一起提交。
- MQ网络在DB事务外；type1一般业务事件不建用户提醒，type2升级事件才落通知；scanner为另一入口共用Runtime。
- 前端本地填写检查不是业务守卫；版本冲突、幂等重试、契约版本各有用途。
- 本岗入口泛称由后端AI纠正，不计学生独立识别或亲改；没有本人新增操作证据。

## 状态与执行边界

- 源码说明固定0783；完整绿色仅8323692的437BE/65FE与准确Docker合成演练。
- root后报Issue28组合42243eb已合入0549/c79并触发CI；本轮只记时点，不等或预判新组合通过。
- DB3b7生产源码6186超5100，后续pending须另统计；原正式P95三组失败、v2整体未完、v3冻结0执行保留。
- 两岗候选自测/状态属于回复方自述，本岗未运行候选或增加测试通过数。
- 已执行git/rg/cat/nl/sed、文本JSON/hash、apply_patch、GitHub连接器；未产品导入/运行/测试/负载/浏览器/渲染。
- 初始不存在候选路径探查返回2后按真实目录更正；未据此声称文件存在。
- 未访问私密R002原文/封面/tmp/independent内容/未发布测试；未联系独立测试。

## GitHub与交接

- Issue10阶段评论：https://github.com/HJY147/t44-dev-trace/issues/10#issuecomment-6374412075。
- 发后精确readback id/body/url/login一致；不发布reviewer成功状态，不合并。
- 文稿核对后仅显式提交本岗路径，[skip ci]并push自身分支；准确SHA交root。
- 本轮Prompt为岗位派工ID，不增加用户六版演进数量；指南交root转达，练习等待本人真实行动。
- 后续整体CI/审核/验收、性能/规模与文档汇总由责任岗/root按准确版本更新，本岗不代下结论。
