Agent-Role: reviewer
Prompt-Ref: ROLE-reviewer-COURSEWORK-BUNDLE-v1
Review target: 9d6ead5fa3e1494946f2bb8d7ef33c1a97758077
Builder SHA256: a1e5c73d040495f7149307f64ec7676cb7bbecfac2f293dbfb44bc5e4057957b
Metadata scope: c0a5e89b2442da2a9149e1d37c2a424d52aff7c0 / evidence6c81ee9960ef08dc35fe8146fcdd4ab5cabb39d4 integrated in9d6
Current PRhead f866bd5 is a descendant; this COMMENT retains the original9d6 result, not a review of laterdda3.

A 打包工具专项不通过，P2 BUNDLE-SOURCE-BINDING-01，见[Issue38](https://github.com/HJY147/t44-dev-trace/issues/38)。build_coursework_review.py:92–107只核内层source_commit字符串及自洽SHA/size/git_blob，137–142只确认commit存在，未把成员映射绑定到实际Git tree。唯一内存ZIP反例直接调用精确函数：宣称真实9d6，backend/t44/api.py目标blob1eee200e034cc8a4e52423aa52cc40729995c413，但合成payload/内部manifest自洽blob60ff7f429c5080a5dddae83ee8d06e5364c837b8，函数仍返回1；预期拒绝断言真实exit1。

可信build_source_review上游加独立可信selection SHA可排除此合成输入；这是新builder独立Git绑定承诺不足，不指控上游或真实已有包遭篡改。root也在执行前指出同一静态疑点，不能记学生发现。没有落盘ZIP或构建实际审阅包，没有读取私密Word/cover/R002/登录、公开private refs或独立未发布资料。后续dda3窄修另轮复审，原9d6红不改绿。

A其余有限静态：正向路径拒绝逃逸/逐级symlink，四技术DOCX严格M6三稿+M7测试/非空QA声明，无QA PDF/PNG或R002原文白名单；新ZIP/sidecar/receipt使用0600/O_EXCL，输出leaf0700，外层重开核成员/CRC/SHA。未验证实际四稿/截止/逐页QA/包；已有私有父目录owner/mode无显式同等校验，自由文本provenance/QA/missing安全依赖受审选单，未另立未经反例证实的安全P2或给全文件系统保证。工具尚未实际构建包，不能称包通过。

B metadata wrapper排除的限定专审未见新增实质阻断：模块仅API_SCRIPT变，明确Python可执行名+相邻-m uvicorn t44.api:app排除init wrapper；api_projection/strict supervisor_count==1及其余module AST全同。核14公开owner原件SHA、两wrapper例2红→最终相关4绿XML/rawgzip和可读规范化、旧953的43函数/class节点保持、14冻结hash相符。原SyntaxWarning与最终纠正分开；root先前静态没有冒充本岗专审。没有重跑四项/其他套件、真实/proc/Docker/旧故障/压力/CI；不把合成wrapper解释推定成原stage05/H11原因，原不明原因及正式结果保留。

[八段十项报告](https://github.com/HJY147/t44-dev-trace/blob/9f3c7fa/reports/reviews/21-9d6ead5fa3e1494946f2bb8d7ef33c1a97758077.md)
[原红JSON](https://github.com/HJY147/t44-dev-trace/blob/9f3c7fa/agents/reviewer/evidence/coursework-bundle-9d6/source-tree-binding-probe.json)
[原断言失败日志](https://github.com/HJY147/t44-dev-trace/blob/9f3c7fa/agents/reviewer/evidence/coursework-bundle-9d6/source-tree-binding-probe.log)
[有限静态与原件核对](https://github.com/HJY147/t44-dev-trace/blob/9f3c7fa/agents/reviewer/evidence/coursework-bundle-9d6/static-audit.json)

仅COMMENT，不APPROVE、不发global reviewer/stage成功、不合main；不提供包/全局独立/性能/规模或人工提交物放行。
