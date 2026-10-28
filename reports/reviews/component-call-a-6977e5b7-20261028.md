# 组件 Call / 通知 CAS 实际重构限定审核

## 1. 对象与基线

AI reviewer；`ROLE-reviewer-COMPONENT-A-20261028-v1`。准确联合产品为 `6977e5b7331e4c6cf64b719b6f161a082558ef25`，基线 `5d5e0a15e3b15e2f509c4ae71a927bbc35579be7`；上游backend产品 `2d947d237328521e46b9766859ca166a4c54f789`。本岗从6977建新独立worktree，只修改审核记录，不改产品、开发测试、规范或门槛，不读独立783/792私件、不联系测试岗、不访问云。上轮v4/桥报告不改、不重复执行。

后端最终资料 `8c5208bb`、消息最终资料 `50e2e33d` 已只读其本scope报告；本报告仍绑定6977产品，不将后发材料提交当作新产品或已运行CI。跨owner/root明确准入内部签名迁移，先设计后实现的记录见两岗component-call设计及后端architecture-scale A方案；不是学生逐行亲自改码。

## 2. 需求映射

这次消除六个组件入口的重复参数搬运，并复用已经存在的版本条件更新。通知list/mark_read/handle的内部Python输入由平铺参数改为同一 `(g, Call)`，旧Python签名不再承诺。REST/OpenAPI、DDL、状态机、用户业务决策、计数范围、种子CLI及迁移均保持。原需求门槛未改，局部重构不产生性能或独立验收批准。

## 3. 实际差分与责任

对5d逐路径核，产品差分仅 `services/application.py`、`services/common.py`、`messaging/facade.py`。Business固定六项operation→组件/方法表处于原collections分支之后、普通getattr之前，缺owner仍在访问body/path前拒503 DEPENDENCY_UNAVAILABLE；有owner只传同一个g/c对象，无新增转换、UoW或权限旁路。Runtime两个业务入口仍调用Business.dispatch，API装配真实NotificationFacade；没有发现生产调用旧六个适配器的方法。升级门面原本就是(g,c)，原Runtime/API/scheduler源码不变。

`Call.cas` 新keyword-only `record_diff=True`，仅把旧before/after赋值放在条件中。移除新kwarg并展开此if后，整个原cas AST逐字结构相同；check_version完整AST也相同。False保留已有列表内容与身份，不清空它们，不控制Runtime.audit/outbox/提交，所有其他生产cas调用保留默认True。详见 [产品AST证据](../../agents/reviewer/evidence/component-a-20261028/product-AST-delta.json)。

## 4. 通知语义和数据库兼容

list仍从Call.actor_id/query取输入，原_projects实时资格、项目存在/成员共享锁、read/handled过滤、分页total与全范围计数的代码未改。通知写保留项目资格→通知FOR UPDATE→项目归属→recipient→显式check_version→values(row)→原cas条件UPDATE的顺序。第二次纯check_version位于cas内部，不把惰性值构造提前，也不额外查库或释放锁。

原通知UPDATE版本值为expected+1，新为row.version+1；在已验证二者相等的受信整数输入下相同，where仍匹配真实同id/expected版本。原Rows.get提供同请求id的行，Notification表无updated_at字段，因此复用cas不新增时间列。current_state在通知行仍None；最大版本、过期版本和SQL CAS=0仍相同VERSION_CONFLICT。没有修改Rows、SQL、事务、schema、outbox、broker、consumer及Runtime审计。

mark_read仍保留已有read_at，handle仍不改变read_at，空evidence仍先于任何scope查询拒绝。通知传record_diff=False保原before/after，但成功Runtime.audit仍写audit_events。原API/DDL/接口文件及持久源未改；原生MySQL并发只一次生效尚未在本岗复测。

## 5. 原测试及调用方迁移

旧979/806只有模块导入绑定到tmp/780的test-only旧调用适配器；所有顶层函数/类AST（含原参数化、raises、Mock断言调用）完全相同，显式Assert AST分别25与11、总36，逐序相同、删除0。适配器只在tmp中构造真实Call后调用真实生产门面，产品无兼容壳；新增780七项直接使用新门面，不能单靠旧调用适配掩盖错误。证据见 [原测试AST](../../agents/reviewer/evidence/component-a-20261028/old-test-AST-comparison.json)。

## 6. 实际执行与规模

本岗在准确6977执行新780/782及旧979/806，显式排除integration：**47通过、15未选、0failure/error/skip、实际exit0**。包含假gateway、SQLite及进程内ASGI TestClient；不是双机网络、native MySQL或RabbitMQ。保留原有一条httpx/Starlette弃用warning，不为此改依赖。实际argv、原log/XML在 [执行回执](../../agents/reviewer/evidence/component-a-20261028/target-tests-execution.json) 及同目录，未把未选目标当跳过通过。

独立复跑未改source_count.py与固定cloc2.10，6977为65应用文件 **5898行**，`--require-range`实际exit1/within_range=false，仍超5100上限798。基线5d5935、上游5916及通知85→67与owner原件相符；本轮实量净37（backend19+messaging18），不是git物理diff含空白行的净43。没有改分类、迁业务到排除目录或压行。计量见 [准确源码规模](../../agents/reviewer/evidence/component-a-20261028/source-count-execution.json)。

owner报告的backend14边界、联合60/164及其先前旧签名500属于开发证据；本岗没有把这些执行次数重复相加为自己的47或独立验收总数。backend旧通知接口缺口在消息owner的164中报告转绿，准确联合新源仍须根完整CI确认。本岗未运行完整覆盖率、原生MySQL/RabbitMQ、前端、云、正式600秒或独立黑盒验收。

一次只读猜测 `tmp/backend/conftest.py` 不存在，随后读实际 messaging/conftest.py；一次初读owner最终报告路径未命中，随后按Git路径定位REPORT.md。都是读取定位错误，不是产品测试失败，也不制造新业务缺陷。

## 7. 十项核对

| 检查 | 本scope判定 |
| --- | --- |
| 审核身份/准确版本 | 通过，独立新worktree审其他岗6977 |
| 需求/范围 | 通过，三产品文件/原需求及计量口径不改 |
| 接口 | 内部签名明确迁移，外部REST/契约无变 |
| 数据库 | 条件UPDATE/锁/DDL无变；native并发未验证 |
| 状态机 | 产品状态机未改，局部行为目标通过 |
| 权限 | 原资格/归属/收件人次序保留；无新用户选择方法通道 |
| 事务/并发 | 原UoW/outbox不改；真实MySQL仍待 |
| 幂等/故障 | 原Runtime/幂等及审计路径不改；完整回归待 |
| 证据 | 47本岗与owner套件分开，36断言和原测试定义保持 |
| 全部门禁 | 未验证，整体LOC仍失败，非发布通过 |

## 8. 结论

**未发现新的限定代码阻断，可作为根整合候选。** 合包后必须让完整CI显式收集780/782，按新准确SHA执行全套覆盖率、真实MySQL等原门禁，再按新源另行独立及云验证；5d的CI/云成绩不自动重绑到6977。规模5898仍失败，不将净37宣传为达到5100。审核不等于实际合并、发布、独立或正式性能通过，不发APPROVE。
