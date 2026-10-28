# 通知 Call 接口和 CAS 复用：消息岗准入

实际操作者为 messaging AI；实际提示词 ROLE-messaging-COMPONENT-CALL-20261028-v1。总协调明确授权本岗实现已审 A 设计的通知部分。后端依赖为 `2d947d237328521e46b9766859ca166a4c54f789`，基于准确5d，已提供六项固定组件 `(g, call)` 分派及 `Call.cas(..., record_diff=True)`。

生产范围只有 `backend/t44/messaging/facade.py`。list/mark_read/handle 统一输入当前已认证 Call；不承诺旧平铺 Python 关键字接口，外部 REST/OpenAPI/DDL 不变。Call 不是用户输入决定的方法或表。list 仍按 actor_id/query 和实时成员共享锁筛范围；写仍按 project/path/body/clock。成功输出、资格/归属/收件人/版本错误顺序、版本上界、UPDATE CAS、锁、事务和审计出口保持。

`_update` 必须在 `values(row)` 前显式 `check_version`；其后 `cas(record_diff=False)` 再做同一纯检查，复用原更新算法。False 只抑制版本差异赋值，保持原 before/after 列表，不跳审计。通知没有 updated_at；handle 不自动已读。空证据仍在查询之前拒绝。

开发验证先冻结旧979/806全部 assert AST；仅在测试工具内提供旧调用到真实 Call 的显式适配器，旧测试正文/断言不改，产品不加兼容壳。新增 tmp/780_messaging_component_20261028 边界用例直接调用新接口，覆盖值构造前版本拒绝、CAS失败、错误优先和审计差异不变；然后复跑原消息 SQLite/fake/进程配置与后端782检查。真实 MySQL/Rabbit、全 CI、独立验收、正式性能分别未验证，不能拼接旧通过。

规模沿未改 source_count.py + 固定 cloc2.10 计量。后端19行收益属于上游；本岗只报通知文件的实际净变化，最后再报5d到联合源码变化。先设计提交，再代码和验证；原失败、格式检查失败和不达标出口保留。不得读独立783/792私件或访问云。
