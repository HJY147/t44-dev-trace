# ROLE-documentation-M3-CONTRACTS-v1

status: used；actor: documentation AI；source: /root实际派工，2026-10-23。

## 实际派工原文

ROLE-documentation-M3-CONTRACTS-v1：恢复文档岗。当前集成074fab7accb1e868bac1d379d6460cca2f6fd2e4已push，包含M3 8图、FE b485、BE创建/会话复用3ee（被测64b4 CI317/88.16%）和提示词4226资料；此前排队消息的bundled运行路径继续适用。用户刚提供本人原话，root保存 records/reflections/R001-original.md 与provenance.json（根尚未commit，你可只读根这2个明确路径或等commit）；核心是人把关架构/封装/重要函数I/O、需求歧义、测试要求过程结果决策，建议会开发的人先写def骨架/#todo给AI。请：①只引用/链接用户原文为本人观点，不美化成AI代写研究正文、不倒填其已亲自写骨架/调试；更新研究素材/学生模板/提交对照中“个人意见完全未提供”的过时说法，课程建议等仍未提供。②依据当前真实代码增一份 docs/function-contracts.md，明确各模块及关键函数真实输入/输出形式、前后置、错误、事务/副作用/调用方；至少覆盖FE API、Runtime、Business、domain.decide、Rows/UoW/migrate、MQ worker/consume、Scanner/EscalationFacade、部署CLI，给精确源码链接与冻结Schema关联；先读真实签名，不编方法。把本项目已有OpenAPI/DDL预先冻结与用户建议的未来人工骨架工作流分清。③整合M3图和提示词公开材料到本岗说明，M2历史保留。现在同机契约稳态10:30:19至10:40:19 UTC，随后升级还10分钟，root没宣布结束前禁止本机Word渲染/构建/pytest/业务请求，先做Markdown/源码读取/Git；最终DOCX继续pending，不抢先声称逐页QA。不要读未宣布发布的独立黑盒文件/私有用例或联系测试。独立worktree/明确路径提交，本岗日志/报告/handoff/实际prompt与GitHub交流，阶段commit/push；先完成高价值I/O和R001来源修正后交接。

## 实际路径纠正续条

来源文件已真实提交5b3bf30（root HEAD最新）。明确完整白名单路径是 /Users/yang/Desktop/nothing/软件开发大作业/records/reflections/R001-provenance.json （带R001-前缀），另 /Users/yang/Desktop/nothing/软件开发大作业/records/reflections/R001-original.md。你可直接合入5b3bf30后用自己的相对路径读取；保留你已发生的cat错误，不伪造原来源。原字和换行保留，仅文件尾加newline，此属human reflection，不是code edit/hallucination识别。

## 执行边界

本轮仅源码阅读、AST静态索引、Markdown/JSON/Git；不导入应用、不执行产品函数/请求/测试/构建/渲染。不联系测试、不打开未发布黑盒文件。原provenance.json路径缺失退出1、pika_adapter.py猜测路径不存在退出2保留为读路径错误，后续按实际broker.py和R001-provenance.json继续。
