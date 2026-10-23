Agent-Role: backend
Prompt-Ref: ROLE-backend-CONTRACT-v2
Refs: #3, #12, #13

已读并保留设计v1不通过报告（被审SHA `717cd65ef73560fde7ff5bca2821c9fe2b20d68a`）。本轮仅修后端C2/C3/C4和C1来源说明，未改原审核/失败证据、数据库文件或产品代码：

- C2：EscalationEvent.recipient_ids取消maxItems，不截断全部经理、未新增人数上限；handled_count覆盖0～4294967295。共享事件Schema使创建及历史嵌套一致，设计例检查101名完整收件人。
- C3：共享UtcTime限制1000～9999年、UTC Z、微秒≤6，FormatChecker校验真实日期；Plan/TaskCreate及只读候选同域再比较起止。扫描只用now−end差值，不构造9999年末+24小时。已通知总协调向下一轮调度岗转交，当前无活跃scheduler实例；不是声称运行过调度。
- C4：清除GET和只读校验幂等错误注解；逐操作response、code枚举、HTTP及x-error-cases触发条件对齐。全局字典/身份等无项目/资源入口去掉不适用项目403/资源404；字典无typed输入的422也移除。新增脚本真正检查上述一致性，而非仅能解析OpenAPI。
- C1：README/backend-design采用持久response_request_id，COMPLETE非空，保存最终实际生成所存结果的请求ID；回放meta.original_request_id取该列，其余当前meta重建，不存旧完整meta/凭据。数据库岗已接到对齐消息，但该列/约束由其另行修订，不能把本轮后端文字当C1整体已通过。

真实设计验证：`.venv/bin/python agents/backend/validate_contract_design_v2.py` 在修复前退出1，90个设计检查失败，日志 `agents/backend/contract-v2-before-fix.log`；修复后退出0，1130项设计检查、38操作、0失败，日志 `agents/backend/contract-v2-validation.log`。含实际FormatChecker的0001/0999负向、1000/9999边界、101收件人及创建/历史嵌套、UINT32计数、逐操作注解/HTTP/条件核对。

这些是规范/Schema及设计一致性验证，没有实际HTTP、MySQL、消息、调度或压测，未宣称冻结、产品通过或reviewer复审通过；须后端+数据库修复的新SHA复审。
