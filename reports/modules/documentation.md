# 文档汇总岗位报告 M4 TESTS AND WORD

Agent-Role documentation；Prompt-Ref ROLE-documentation-M4-TESTS-AND-WORD-v1；Refs #9。

## 当前产物和边界

- 独立codex/review-documents，内容主基线2e0481f，开发CI/容器证据0448fec；后续状态作为续记，不反复追头。
- 新reports/final/test-results-report.md汇编模块/实库/CI/容器/审核/独立v1/正式性能，明确未通过最终验收。
- 335后端/零跳过，43文件2493至2818行88.47%、分支77.73%；前端24/307至333行92.19%，均绑定0448fec。
- 同SHA容器19表count/checksum恢复通过；旧317/88.16等历史分开，不混分母。
- 独立v1只读公开两报告：900结果340/183/328/49，183含歧义不当183bug；38成功路径通过。
- 三批400VU/600秒P95为3035/1908/5506ms失败，吞吐和稳态零失败通过；不外推云容量。
- UI公开补充仅新增授权两文件：原e8测3/1/1，原900不改，不冒称测过b485；无私有截图读取。
- C-P4四类限定关闭，5886超5100仍failure。IAT01已开发修复；后续IAT02至05 55HTTP/SQLite回归不当独立复测。

## 文档与工具

- 需规/概设详设/AI规格说明、AI证据/提交对照同步M4状态；R001原话归属与学生自写边界保留。
- docs/function-contracts.md与M4-contract-sources.json锁准确2e完整SHA，49函数链接不承诺未来源码匹配。
- scripts/docs/export_review_documents.py只处理自有MD、8图资产和私密封面，不搬业务逻辑。
- 四技术Word仅root .submission-private/review-documents，0600文件/0700目录/Git忽略，日期空；学生研究正文不在其中。
- 已读documents技能及创建/渲染说明，loader核实bundled Node/Python与指定LO。
- 首次author前create marker成功一次，expected4/formatdocx；四份已author，并在root明确解除quiet后完成指定bundled LO渲染和全部28原PNG逐页QA。
- 四份作为技术审阅材料完成排版QA，不等于软件最终验收；不调用用户桌面LO，公开记录不含个人封面值/截图。

## 来源记录和待办

- M4-source-manifest.json固定公开来源、原CI归档摘要、marker与运行时；M0至M3原始收件/来源/失败不改。
- 本轮未执行产品测试/业务请求/压测，不联系测试，也不跟随公开报告中的私有证据路径。
- 精确阶段SHA/PR及最终页数/逐页QA结果按真实发布补，不预填通过。
- 最终qa-v4：需规10/设计9/测试6/规格说明3页；全部原封面已看。初始字体/Title蓝线、表格拆行与行距裁图失败均保留并修正，详见M4-word-qa.json/.md。
- 学生研究最终成文/课程建议和真实人工留痕、性能达标、独立复测、规模达标仍待后续。
