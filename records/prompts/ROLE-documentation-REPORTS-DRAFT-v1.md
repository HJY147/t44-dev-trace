# 文档报告阶段实际派工

Agent-Role: documentation
Prompt-Ref: ROLE-documentation-REPORTS-DRAFT-v1
实际发送者：总协调AI；实际执行者：文档岗AI。此为实际岗位派工，不冒称用户原创prompt演进版本。

```text
ROLE-documentation-REPORTS-DRAFT-v1：继续专门文档岗位，在独立树 `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/documentation` branch codex/reports-draft，base5d0c087f63812b0e00c7284afeafe4ec6a00c110。用户要求完整需求/设计/AI时代研究报告；现在可先完成真实阶段工作稿，不能写成软件已交付。Q002字段错误人的取舍仍pending；C1–C4技术复审通过且报告已在本树，尚未冻结/迁移/HTTP测试。前端基础已PR14/final f261cbf0ea94537ed9f0a1600770c93ee8109237，部署CI PR15/final72e3275202273a60af3acc37b7a319f10eea99a7；根每岗实际handoff还在对应worktree，可明确只读它们已发布报告/交接/评论。核心backend和database正在做独立基础，你可直接send_message实际问取产物/接口/验证边界并记录原文；无并发槽位请勿再followup唤醒空闲角色。frontend/deploy已发布资料可引用为已发布来源，不冒充本轮亲自问答；未收到回答标待补。M0实际问取原记录不改历史。
产物：reports/final/requirements-report.md、design-report.md、ai-development-report.md 三份中文阶段工作稿，以及docs/reports/M1-collection记录和本岗日志/模块报告/handoff/prompt。需求报告映射8FR/9AC、角色与成功/失败路径、量化目标、当前已采用/待采用/待测；设计报告两方案对比、门面DI/状态机/数据库与版本/成功拒绝事务/并发和依赖图锁/扫描outbox降级伪码复杂度/部署与真实CI；研究报告先写事实支持的过程、两段用户原创prompt亮点及实际Issue/commit/PR证据、真实AI错误与AI纠正（明确不是用户亲改或人类独立识别），个人思考/真实人工改动/课程建议未有来源处留明确待用户撰写，不伪造学生口吻或经历。覆盖率/400并发10分钟/有效LOC/6版prompt/12人工对照/3人工识别幻觉/5人工校正映射均按真实状态，不把计划当完成；不要为了计数重分类AI改动。三份报告都要清晰‘工作稿、非最终验收’，不重复几千行日志，引用原始证据即可。
原始T44/submission/homework源文本只读根 `/Users/yang/Desktop/nothing/软件开发大作业/specs/sources/`，不提交；T29其他人题目不移植。测试仅允许本树 reports/modules/testing.md 与 records/handoffs/testing.json 两份公开冻结初始化资料，不联系测试、不读agents/testing、private plan或独立内部用例。封面姓名学号未提供，不猜；Markdown工作稿无需先做Word导出，最终软件/用户资料齐再按documents技能渲染Word/PDF。
只修改本岗报告/收集资料/过程记录/prompt，独立索引显式commit footer Agent-Role documentation、Prompt-Ref ROLE-documentation-REPORTS-DRAFT-v1、Refs #9；可push分支建base codex/team-bootstrap草稿PR并attach，不merge main不发审核success。先产可用工作稿并真实核对JSON/链接，完成回SHA、来源边界、真实问取与未完成项。
```

## 本次范围与改进理由

由M0组织汇总转为三类正式报告的阶段工作稿，明确证据级别和人的判断缺口。实际产物关联三份reports/final工作稿、docs/reports/M1-*、本岗WORKLOG/模块报告/handoff。原始作业提取文本只读根目录，M0实际收集记录不改写。用户原创U001/U002另有原文，不把本派工或并行岗位计成同一prompt六次演进。

## 后续真实派工补充

总协调实际消息（原文）：

```text
用户新发明确要求再读《作业提交注意事项.docx》。根协调已从原DOCX完整提取复核（非只缓存），SHA256 c688f2a25c8a1c73803e7e958e8c50681a0484ef1f34a679fa8b100ce2d64f32；与specs/sources/submission-notes.txt主要文字相同。请在你本轮收尾前亲自读root原件/缓存并加一份紧凑reports/final/submission-map.md：四组提交→最终代码、测试结果文档、需求报告、设计报告、AI可执行规格相关文件+专门介绍说明、“AI时代如何进行软件开发”研究分析报告。分析报告必须覆盖影响思考/分阶段质量手段/协作与真实踩坑/T44第12条/亮点/课程建议。你的三稿要映射这些并显式缺口：测试最终稿未完成、规格说明独立文档待形成、个人意见未提供。附封面模板课程名及专业班级学号姓名指导教师日期待填；不猜姓名。不要为了本次补阅读重写大量治理文档，不生成最终DOCX，不上传原件。继续commit/PR收尾。
```

```text
补充：为了直接落实这次老师提交说明，可加reports/final/ai-spec-guide.md阶段说明稿（约50–80行即可）：逐项介绍AGENTS/implementation-layout/requirements/business-rules/OpenAPI/field dictionary+DDL/persistence contract/规则配置未来路径的用途、给AI的正确读取顺序、谁可改/如何review+冻结+同步测试、未冻结不联调、验收证据位置。不要仅留缺口；现有可确认部分先说明清楚。仍标阶段稿，不编造规则配置已存在。不需新DOCX或额外治理流程。与submission-map同本次报告draft PR交付，完成后及时停止新增润色。
```

后条实际派工将前条“独立说明待形成”推进为本轮应交独立阶段稿；最终完整冻结说明仍需后续证据，当前三稿与提交对照已按最新事实更新。
