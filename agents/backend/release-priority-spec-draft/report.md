# D008 1.2.0规格草稿同步

后端AI；从最新root398c3d3621843aa536755ae106c78a0fd1c60aff新分支codex/backend-release-priority-spec-draft。仅修改后端设计/权威OpenAPI/契约README/运行OpenAPI及本岗记录，不实施Workflow、不改测试/DB/DDL/旧manifest。D008用户决定与RFC R2/891d676限定设计结论是依据，均不构成用户改码或产品通过。

info.version及成功Meta.const均1.2.0；两JSON逐字同，candidate_schema.const仍1.0.0。top及38操作均显式draft-v1.2-pending-freeze，没有提前frozen标记。transitionTask仅原批准引用不匹配失败槽：已解析评估基线过期优先BASELINE，基线有效而批准失效仍APPROVAL；前置身份/归属/taskexpected/请求assessmentversion与引用匹配后的domain次序保持。missing/跨任务/其它action不新覆盖，不扩大全局state/role顺序。README/design新增1.2段并逐字保留完整原1.1文件为历史后缀，R2的4xx完成条件/动态成功meta/错误无outerMeta/commit不明边界明确。

实际执行原995纯设计脚本：OpenAPI规范PASS、1130checks/38ops/0failure，原log与完整真实argv见design-command.json/design-1130.log；脚本自带banner仍是历史.venv路径，实际解释器以command记录为准，没有改脚本。未出现旧版本fixture失败，也未改断言。

结构白名单共45叶值变化：info两字段、成功Meta.const一处、top/38操作草稿状态39处、transition描述与两个x-error-cases条件3处。其余Schema除Meta.const外全等（130），错误enum稳定，31路径/38操作及operationIDs全同，请求/响应结构不变。两副本hash一致；4文件SHA见whitelist-diff.json。初只读probe误用x-status键KeyError1，实际键x-contract-status，原错误单独保留，不是995失败或产品问题。

原v1.1manifest内容未改；当前这四件有意成为新1.2草稿，不能声称它们仍逐字匹配原14hash。旧hash/文件可由原父链恢复，新v1.2manifest仅root建立。根需规/业务/AGENTS待根同步，限定最终规格审核/新freeze/Workflow实施/开发回归/新源CI/独立复验均未完成。本轮没有suite/SUT/HTTP/SQL/服务/负载、没有性能或源码规模新证据；859不重跑，F08原FAIL/未执行尾部/WordZIP保持。提交均skip-ci，完成交接后释放。
