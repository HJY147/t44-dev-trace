本PR提供T44需求、设计和AI时代软件开发研究三份中文阶段工作稿，便于后续按冻结规格、软件快照和真实测试结果持续补全。三稿明确非最终验收：Q002人的字段/错误码取舍仍pending，C1–C4仅技术设计复审通过，当前没有HTTP/MySQL迁移/完整应用验收结论。

需求稿映射8FR/9AC、角色和成功/拒绝路径；设计稿覆盖两方案、门面DI、状态/版本、成功/拒绝事务、并发图锁、扫描/outbox/fallback伪码及复杂度、真实部署CI；研究稿保留U001/U002用户原创prompt和Issue/commit/PR证据，AI发现/修复与人的决定/亲改严格分开。本人思考、真实人工修改、课程建议和个人信息明确待本人提供。

实际send_message向backend/database收集两条即时原文，已收到PR16/0bb4549c1b6e4fb7247dc58dd8a5fa675161d614与PR17/4ae865b8dc554813c04aacbb3a5033aa2745c799正式基础提交（106领域测试、18项SQLite/mock，不是HTTP/MySQL/独立验收）；前端/部署只读已发布准确SHA报告/交接，不冒充本轮问答。M0收集历史不改，测试只读两份公开初始化资料且未联系测试。

Validation: python3 agents/documentation/validate_report_drafts.py（JSON/来源哈希/链接/FR-AC/历史边界）；gh实际核对PR14/15当前draft/head、Actions39912067161失败及两条设计Review commit_id。未执行产品测试；不发布审核success、不合并main。

Agent-Role: documentation
Prompt-Ref: ROLE-documentation-REPORTS-DRAFT-v1
Refs: #9

按最新要求亲读原《作业提交注意事项.docx》29条非空段落，SHA c688f2a25c8a1c73803e7e958e8c50681a0484ef1f34a679fa8b100ce2d64f32、归一文字与缓存一致。新增submission-map.md映射四组交付和封面待填字段，ai-spec-guide.md为独立阶段说明；测试结果最终稿、最终冻结规格说明和本人意见仍缺，原件不上传，不生成最终DOCX。
