# 独立测试资料归档任务

这是无父会话的新归档实例，不开展产品测试，也不是把开发上下文传给原测试实例。

根目录 /Users/yang/Desktop/nothing/软件开发大作业。输入白名单：本任务、agents/testing/TASK.md、agents/testing/WORKLOG.md、reports/modules/testing.md、records/handoffs/testing.json、reports/independent-tests/isolation-protocol.md、specs/sources/manifest.json。不得读取其他岗位、开发记录、GitHub开发讨论或产品代码；不使用代理通信工具。

总协调授予本次唯一Git索引操作时段。仓库 HJY147/t44-dev-trace；必须确认当前分支 codex/team-bootstrap，且暂存区为空。仅归档本岗既有的初始化日志、模块报告、交接单和隔离协议；不加入尚未发布的验收用例草案，不强制加入忽略文件。

先在本岗WORKLOG中记录这次实际收到的归档委托与白名单读取、阶段仍未测试。写 agents/testing/github-stage-comment.md，正文含 Agent-Role: testing、Prompt-Ref: ROLE-testing-ARCHIVE-v1、产品未实现/未运行验收、四份归档资料和当前阶段。该文件仅为归档状态，不含开发讨论或用例。

git add仅限上述四份产物、本次ARCHIVE_TASK及github-stage-comment；提交信息 docs(testing): archive independent acceptance bootstrap，正文带Agent-Role: testing、Prompt-Ref: ROLE-testing-ARCHIVE-v1、Refs: #8。随后用 gh issue comment 8 --repo HJY147/t44-dev-trace --body-file agents/testing/github-stage-comment.md 登记中性状态。不要push、merge、checkout其他分支或设置审核状态。不要改原始资料。

最终向总协调返回完整commit SHA、实际提交路径、Issue评论URL、命令结果。若索引非空、分支不符或Git命令失败，停止提交并据实报告，不接管其他人的暂存。没有测试通过结论。
