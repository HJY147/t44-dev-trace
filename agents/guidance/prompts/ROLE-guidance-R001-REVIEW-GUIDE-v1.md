# 实际派工 ROLE-guidance-R001-REVIEW-GUIDE-v1

来源：root 实际派工消息；执行岗位：AI guidance。不是用户亲写 prompt，不计同一用户提示词的新增演进版本。

```text
ROLE-guidance-R001-REVIEW-GUIDE-v1：恢复固定用户指导岗，限轻量只读源码/文档，不运行产品/测试/浏览器/渲染、不联系独立测试。所有产物 /Users/yang/Desktop/nothing/软件开发大作业 内。独立worktree/分支codex/，先核对AGENTS。root现已合入f6547f（当前HEAD请读），后端五类IAT修复479已合入e62；当前rootREADME/公开证据是准确参考，不把旧初始化“未实现/未采用”当现状。
请读 records/reflections/R001-original.md 与provenance（用户本人原话原拼写保留不得改），D001/D004、docs/function-contracts.md、docs/collaboration/implementation-layout.md、README与reports/modules相关公开说明。更新你拥有的docs/user-guide/project-basics.md与records/qa/question-log.md/decision-log.md：旧时点记录保留，追加当前事实；明确本人反思已收，研究成文与课程建议未提供，用户还没实际亲改代码/断点/识别幻觉。
新增简洁审阅与调试指南回应R001：本项目为什么选单体分层、class/纯函数/UoW各责任；配置现状（规则/模板版本化JSON，运行参数/凭据env，不把用户举例YAML或manager-based自动改成选型命令）；通过具体函数I/O索引解释人如何先审接口/副作用/错误，再让AI补实现，别说这种方式能保证无bug。给可执行但明确尚未执行的VSCode断点/Python breakpoint()步骤，解释break是循环控制，使用普通用户能懂的话。指导必须绑定真实源码函数/位置/版本，别编造用户已操作。可给一个有用的本人审阅记录空表/问题列表，供用户自己填，不替人填写12次改码/3次幻觉或预置“正确答案”凑数；不要凭现有AI已发现bug给学生记人工识别。
records/qa/Q-capacity-lifecycle-pending.json为新真实待答问题，只记录pending，不替用户选择。不要要求用户上传口令/私钥、不要让用户重复批准已采用D001/D004。用户的研究正文仍本人写，本岗只转交简明解释/真实素材，不代写成学生口吻。
当前后端准备性能诊断quiet窗口、文档等待LO，因此只轻量MD/JSON即可。按本岗日志/模块报告/handoff/本次实际prompt落档，真实GitHub Issue/PR阶段评论，commit/push交准确SHA，做必要链接/事实核对但不为MD小改写测试。结束释放slot，答案建议由root转达用户。
```

实际后续约束：root 要求 UTC11:45 起的专用性能短诊断窗口只做轻量 MD/JSON/链接核对；不运行产品、浏览器、渲染、大测试。CI 引用绑定来源，不用内部预测测试数。root 还明确 MD 中未执行示例无需新编号，实际创建脚本才需申请 tmp 递减编号；本轮只提供 MD 示例，没有创建脚本或消耗编号。

产物映射：`docs/user-guide/review-and-debug.md`、`project-basics.md`；`records/qa/question-log.md`、`decision-log.md`、`R001-guide-sources.json`；本岗 WORKLOG、模块报告、handoff、阶段评论。改进理由：区分旧时点与当前实现、本人观点与真实操作、内部函数与事务副作用，避免把既有 AI 发现和建议记成人工成绩。
