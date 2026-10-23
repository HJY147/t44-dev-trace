Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-COURSEWORK-BUNDLE-v1
Target: 9d6ead5fa3e1494946f2bb8d7ef33c1a97758077
File: scripts/packaging/build_coursework_review.py:92–107, 137–142
Builder SHA256: a1e5c73d040495f7149307f64ec7676cb7bbecfac2f293dbfb44bc5e4057957b

P2 BUNDLE-SOURCE-BINDING-01：verify_source_archive只核内层source_commit字符串及自洽SHA/size/git_blob，main只确认commit存在，没有验证路径/blob/mode映射属于所声明Git tree。因此“源码已复核”可在没有真实Git绑定时成立。

唯一内存ZIP反例直接调用精确未改函数：声明真实9d6，backend/t44/api.py的目标tree blob为1eee200e034cc8a4e52423aa52cc40729995c413，合成内容/manifest自洽blob为60ff7f429c5080a5dddae83ee8d06e5364c837b8，函数仍返回1；预期拒绝断言真实exit1。没有落盘ZIP、构建实际审阅包或读取私密Word/cover/R002/登录/独立资料。

信任边界：可信build_source_review生成器加独立可信的selection SHA可排除此合成输入；本问题针对新builder独立复核准确Git源的承诺，不指控上游或真实已有包遭篡改。root在执行前也提出同一静态疑点，不记学生发现。

[准确9d6报告](https://github.com/HJY147/t44-dev-trace/blob/9f3c7fa/reports/reviews/21-9d6ead5fa3e1494946f2bb8d7ef33c1a97758077.md)
[原红JSON](https://github.com/HJY147/t44-dev-trace/blob/9f3c7fa/agents/reviewer/evidence/coursework-bundle-9d6/source-tree-binding-probe.json)
[原断言失败日志](https://github.com/HJY147/t44-dev-trace/blob/9f3c7fa/agents/reviewer/evidence/coursework-bundle-9d6/source-tree-binding-probe.log)

责任方root已另报先行设计add7363/窄修dda3df8e15b0b5b655909dda37dc79a87f318924；本Issue只记录原9d6失败，修复尚未获本次复审。复审需绑定准确新源、同一内存反例与可信selector完整正向映射。原失败保留，实际审阅包尚未构建，不提供全局验收/性能/规模/人工材料放行。
