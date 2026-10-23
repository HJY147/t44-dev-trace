# 文档汇总岗位报告｜M3-CONTRACTS-v1

## 任务与当前状态

- Agent-Role: documentation；Prompt-Ref: ROLE-documentation-M3-CONTRACTS-v1；Refs: #9。
- 独立树documentation/分支codex/function-contracts，实际基线074fab7及R001来源5b3bf30。
- 本轮可审MD：关键函数I/O、R001本人观点来源、M3八图/prompt证据同步；不是最终研究成品或验收。
- 本项目先冻结OpenAPI/DDL再完整实现，与用户建议未来亲写def/#todo工作流分清；不倒填人工骨架/调试。
- 封面具体值仅私密本地，日期空；最终DOCX/逐页QA仍未运行。

## 产物与输入输出

- docs/function-contracts.md：FE API、HTTP/Runtime、Business/Workflow、domain、Rows/UoW/迁移、MQ/消费、扫描/升级、部署/管理CLI。
- 每层说明真实签名与输入/输出形式、前后置、错误、事务/副作用和调用方；不伪造原函数类型注解。
- docs/reports/M3-contract-sources.json：24源码哈希/真实函数签名行号，38冻结HTTP操作的request Schema/响应状态。
- ai-development-report.md/学生模板/提交对照同步R001原话及provenance，不再写本人观点完全未提供。
- ai-spec-guide.md加入函数I/O、root已渲染八图及提示词4226事实材料入口。
- M3-collection.md/.json保存9条晚到M2真实答复与本轮对提示词岗回复原文；M2原档不改。
- 本岗prompt实际原文在agents/documentation/prompts/ROLE-documentation-M3-CONTRACTS-v1.md。

## 来源与设计边界

- R001原文hash/provenance一致，归属human reflection；不计人工改码/人工识别幻觉。
- root M3八图CLI12/Chrome真实渲染/独立PNG查看有公开manifest；本岗只读证据，没有本轮重渲染或冒充看图。
- 4226提示词事实包：CONTRACT已核2版，人工12/3/5本轮可证实0；事后ROOT目标文件不计实发版本。
- e01完整审核四项failure仍保留；指定64b4开发CI317/0/0/0、whole Python88.16%不等于新产品审核通过。
- 迁移check_schema在基线只比部分结构/名称，C-P4漏语义明确；新checker待责任岗验证，不宣称关闭。
- 当前六岗有实际回复、消息/调度/指导三岗未回；既有公开报告可引用，未收到的不代写。

## 验证、错误与交接

- 仅源码/AST/JSON/哈希/链接/Schema静态读取，无导入应用/业务请求/pytest/构建/渲染。
- R001旧provenance路径不存在退出1；实际纠正R001-provenance后继续，原错误留WORKLOG。
- 初猜pika_adapter.py不存在退出2，rg定位真实broker.py；不当作应用bug。
- 文档校验、11冻结文件未改、M0/M1/M2原始记录未改及隐私结果见M3-contract-validation.json。
- 正式性能/独立验收最终结论不在本轮读取范围；不联系测试或读取未发布黑盒/内部材料。
- 学生最终研究文字/课程建议、真实人工记录、最终Word逐页QA继续待办。
- 阶段commit/push/草稿PR及GitHub对接记录按真实发布后补；不merge main/发审核success。
