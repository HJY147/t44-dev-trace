Agent-Role: database
Prompt-Ref: ROLE-database-DESIGN-v2
Refs: #4 #13

针对失败审核717cd65的C1，数据库实际已修改三件设计，不改原失败报告：

- `idempotency_requests.response_request_id` 为ASCII VARCHAR(128) NULL。PROCESSING必须NULL；COMPLETE必须非NULL且非空，与状态码/业务快照/完成时刻同事务保存。
- 保存的是“生成该已保存成功或拒绝结果的处理请求ID”。租约接管后由最终完成者当前请求定格，不固定首次认领ID；拒绝结果与独立审计事务一并保存。
- 初次处理meta.replayed=false时original_request_id可NULL；重放为true时从此列取非空original_request_id，当前meta.request_id/server_time重新构建。既不保存整份旧meta/Token，也不依赖成功data含audit_id或反查审计表。

C3已与backend时间域对齐：共享API Schema/真实日期校验先于持久写入，UTC Z、年份1000～9999、小数秒≤6；不静默截断。实际以根.venv的Draft202012Validator＋FormatChecker检查共享UtcTime的9个边界例值，9项均符合预期；这是Schema检查，不是MySQL/HTTP运行。结果在`agents/database/design-v2-time-check.json`。

当前18表226列，其他领域设计未扩展；仍未执行DDL/迁移、未写模型、未做数据库运行验证，也未操作根Git索引。请backend确认该持久来源与README/backend-design一致；修复尚待新SHA复审，不宣称审核通过。
