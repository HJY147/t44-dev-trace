# 实际派工约束

作者/执行者：后端 AI，不是学生本人操作或手写报告。

root本轮实际要求重点：“尽快得到真实CPU/请求阶段profile，定位API入口/契约validate/响应模型序列化/业务调度的成本，保留请求ID、UTC与monotonic起点，阶段inclusive/互斥意义写清。”只读具名839公开报告，不读独立私件；先本地TestClient/SQLite，再由root新工作流的fresh MySQL服务作一小轮真实HTTP+CPU+SQL诊断；root负责CI，不单独触发多工作流。

本岗向DB确认在真实APIRoute同步handle内用observer.request(operationId,request_id=uuid)关联，并与其install(engine)/snapshot对齐；API instrumentation与DB instrument分开职责。拒绝缓存validator的先验修复，以新准确源码上的实测决定下一步。
