Agent-Role: backend
Prompt-Ref: ROLE-backend-DEPENDENCY-QUERY-CANDIDATE-v1（本岗归档标识，实际派工原文见 agents/backend/DEPENDENCY-QUERY-CANDIDATE-dispatch.md）

Draft PR42 固定产品候选 C=b66fa36a317145afec350d7f61ca374959b2eaf7；先行RFC ed2737d，唯一应用修改74a：Workflow依赖边查询增加已验证project_id。tasks全局PK+冻结复合FK+Call.task项目核对证明合法数据读集相同；不改索引/DDL/冻结/身份/guard/锁序/CAS/audit/outbox/幂等/ACK不明。旧pool默认5+10保持，不包含db87。

DB公开证据5948cf80及Issue4回应6377715017已全文GET：其原夹具EXPLAIN估9216→1且仍filesort，仅优化器估算，非测量收益/正式根因。本岗没有重跑SQL。原986相同18目标旧/候选各18pass，为SQLite真实TestClient/RowsGateway开发回归，不是外部MySQL或延迟对照；原18测试字节未改。

原74a product40047094732整体failure保留：full510/0fail/error/skip、markers162/93/19及FE89通过；static在基底部署开发文件864 UP022/871 B007真实失败。部署owner17e7ac5两处样式修复经root授权cherry-pick，本岗未改owner文件或重跑旧CI。C已触发新product40047832510、Docker40047836840，目前pending，不能称准确源完整通过。旧Docker40047211444实际checkout d74cfc8（父728c4e8+74a）由官方checkout/gitlog证实，169相关运行roots文件与74a相同；不拿API head充checkout。

实际固定cloc C=6307，范围exit1/超1207仍失败。14冻结hash一致。后续证据单独分支codex/backend-dependency-query-evidence，不再推动PR42的C。请求DB/root后续只按预先dde39门槛及准确源专审决定，不自动集成或宣称性能/验收通过。本阶段作者/改码者为后端AI，样式修复者为部署AI；无学生亲改，无独立资料访问/新服务/外部DB/负载。
