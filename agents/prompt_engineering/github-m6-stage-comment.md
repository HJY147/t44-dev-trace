Agent-Role: prompt_engineering / AI
Prompt-Ref: ROLE-prompt_engineering-M6-CHECKPOINT-v1
Refs: #11

M6 实质资料检查点：独立树 codex/prompt-m6-checkpoint，基线7763402；不改根索引/生产/冻结/他岗资料，不代写学生研究正文。

- 已核 U001/U002 原文、优化建议稿和实际组织/Issue/PR/commit效果与局限，建议稿仍 proposed。
- 原任务书只要求“提示词演进≥6个版本”，不要求全由学生输入或单族六版；本轮显式纠正M4/M5过严口径，保留旧文。三条真实反馈链共6条实际版本：CONTRACT-v1/v2；LOGOUT→SESSION-R1；A初准入→真实caller遗漏纠偏。每条有实际文本/上下文/阶段产物与执行反馈，审计编号不是补造历史版本名。
- 保留39绿后895的1红2绿、A25绿后旧988/974的2红与7绿1CAS隔离红、UI002的9红4原绿及原类型/驱动错误；后续修复与PR26/29/30精确限定专审分别记录。
- 832组合437BE/65FE与全生产分母、同源Linux4worker19表恢复是开发CI/演练；独立v2八阶段仍旧4c、整体未完成，v1正式P95失败不抹除。cloc832=6124超限；晚到DB3b7/24839=6186另源另记。
- M5七类MD/三图独立阶段提交与M4 Word/已合PR24分开。精确冻结SHA为189dc4a，继承素材189dc14笔误首次检查失败及修正保留。
- 六岗实际send_message请求工具均无错误但空回执，收到BE/DB/native三岗实回，另三岗截至成稿未收到，不伪造访谈。未联系测试岗；只读明确发布的16件v2文件与v1最终MD/JSON，不跟私有路径。
- R001本人反思、R002课程建议provenance已核；人工12修改/3幻觉识别/5人工校正映射仍无完成证据，本轮可确认0，不用AI工作充抵。native只已核依赖能力和两次cookie探针原失败，broker等能力仍pending。

交付 docs/prompting/M6-process-checkpoint.md、M6-prompt-version-map.json、106源hash manifest、实际问取与GitHub只读回执、本岗日志/report/handoff。仅必要文档/hash/JSON/XML/6条Git祖先核对，无产品测试或整套CI；纯文档提交使用[skip ci]。提交/推送SHA与本评论readback在真实完成后另补。
