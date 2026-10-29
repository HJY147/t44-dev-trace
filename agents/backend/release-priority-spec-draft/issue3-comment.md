Agent-Role: backend
Prompt-Ref: ROLE-backend-RELEASE-PRIORITY-SPEC-DRAFT-v1（AI本岗归档标识，实际派工原文另存）

基root398c3d3新分支codex/backend-release-priority-spec-draft，按D008/RFC R2及限定设计审查891d676，仅同步四件1.2.0草稿：specs/backend-design.md、specs/contracts/{openapi.json,README.md}、backend/t44/contracts/openapi.json。未改Workflow/测试/DB/DDL/旧freeze，未执行suite/SUT/CI/服务/负载，未冻结不实施。

info与成功Meta.const同1.2.0，两OpenAPI逐字相同，candidate_schema1.0.0保留。top/38ops均draft-v1.2-pending-freeze。仅transitionTask原批准引用失败槽D008基线优先，不覆盖身份/归属/任务及请求评估版本前置，不扩大全局state/role、missing/跨任务评估或其它action。R2明确只有ownedclaim/status1/owner相同/<500且独立audit+COMPLETE事务提交的4xx在缓存保证内；保存业务值和原audit_id，不保证HTTP全字节，成功meta动态，错误没有outerMeta。

实际原995：OpenAPI规范PASS、1130check/38ops/0failure。白名单45叶值：2info+1Meta.const+39草稿状态注解+transition说明/两条件3项；31/38/130、错误enum、全部其它Schema及输入输出结构保持，旧1.1两份说明原文完整作为历史后缀保留。各SHA/差异/真实argv与原日志在agents/backend/release-priority-spec-draft/{whitelist-diff.json,design-command.json,design-1130.log,report.md}；初只读探针x-status键误写KeyError单独保留，原995未失败、不降断言。

当前四文件有意显式新草稿，不宣称仍匹配旧14hash；原v1.1manifest不回填，F08失败/未执行尾部及旧WordZIP不改。根另同步需规/业务/AGENTS并负责新freeze，最终规格审查/实现/新源验证/独立复验仍待。用户选规则非用户亲改码；本稿和执行者均后端AI。
