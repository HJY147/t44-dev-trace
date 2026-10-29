# M6 技术文档设计检查点

本阶段由固定文档岗位 AI /root/documentation_checkpoint 整理技术资料，不撰写学生最终研究正文。文档分支从 ceed2d8126405c86016fa05c892249c045534754 建立；应用内容固定 bc5aef9c62393134582affb7a690acb33ac2b833，44 个 Python 与20个 TS/Vue 生产文件。冻结1.1的14个文件严格只读。

## 输入与当前判断

准确同源组合CI为510后端全通过、44全源行2638/2957，前端89全通过、20全源行364/390；同源Docker是小规模synthetic集成。cloc有效源6307仍超5100，正式性能仍原三组P95失败，不能称最终验收通过。42243组合504绿之后HTTP专审真实发现HISTORY-EVIDENCE-01，先ad6勘误、bcb窄修，再bc5同反例限定关闭；原红不改。

## 输出结构和先后

1. 更新七份当前Markdown，明确SRS范围/角色/FR/输入输出/异常/NFR/AC，概设与详设、函数I/O、模块及跨模块测试、需求到设计到实现和审核修订的真实先后。旧M5/M4文件及source manifest保持原样，当前七稿旧字节用历史索引绑定ceed，避免混用版本。
2. 新建M6来源清单和64文件源码/函数静态索引、需求测试追踪；独立仅读已公开v2八阶段16报告、v3冻结收据及runtime binding，不跟随私密链接，不联系tester。
3. 先设计三张Mermaid源：会话卸载与迟到响应边界、历史理由本页保守投影与新写同事务、真实质量门禁反馈。用pinned本地Mermaid工具和独立临时profile渲染，逐图原尺寸看PNG；旧8+M5三图只核hash复用，不重渲染。
4. MD/图检查点commit [skip ci]并push，公开Issue9和新的draftPR准确head/readback；PR24是已合并M4，不把M6说成同PR已合入。
5. 四份技术Word：需规、概设详设、测试结果、AI可执行规格；不含学生研究正文。按documents技能和已有模板，私密cover-info只在导出时使用，日期空。先原样归档旧M4四DOCX/manifest/render PDF及QA，mode0600/hash保留；M6写新子目录。宽图横向页或保证字号，实际每页PNG查看；只在源内容有实际变化时重导对应稿，不重复marker。

## 范围与资源

不改生产、14冻结、其他岗、root registry/ledger。不跑产品全测、业务HTTP或负载。R001只按公开原话及provenance，R002只公开provenance；不读私密学生反馈/任意runtime credentials。当前报告明确六条实际AI提示词版本横跨三反馈链符合数量证据，旧单族六版总量判断过严；不改历史，也不把六条AI派工计学生输入或人工12/3/5。

root后续明确：本机现无正式负载，授权这三图有限Chrome渲染；MD/图checkpoint后可直接M6四Word导出/LO全页QA，无需再次等待。未来若root宣布本机正式窗口则暂停。独立v3未发表结果只记待发表，不追其内部过程。
