# F04 独立验收报告

F04未通过完整验收。原始结果保持PASS13、FAIL6、UNEXECUTED11、38个HTTP操作被观察，`blackbox_full_acceptance=false`。独立核对冻结契约后，6个FAIL分为1项产品契约偏差、4项测试判据/范围错误、1项协调者控制协议失败；不回写原计数或制造全通过。

## 唯一已确认产品偏差

`753-F04-P01`：项目成员请求 `GET /api/v1/projects/1/tasks?owner_id=1%20OR%201%3D1`，实际返回422 `PARAMETER_INVALID`，audit_id75，request_id `16dedb15-a2a9-4cb6-9343-3b2635531348`。冻结OpenAPI的listTasks x-error-cases明确规定ID/枚举/排序选择器中的清晰SQL攻击表达式应返回400 `SECURITY_INPUT_REJECTED`。该请求已被拒绝；本证据不说明SQL执行、数据泄露或注入成功。完整脱敏复现和绑定证据见F04_PRODUCT_FINDINGS.PUBLIC.json。

## 四项测试问题

| 原失败项 | 独立复核 |
| --- | --- |
| 登录 | 响应200且通过冻结Schema，正确字段为access_token；工具额外要求不存在的token字段。 |
| 重复成员 | 工具擅自要求409；冻结addProjectMember未规定此重复必拒。实际201保持原roles[2,3]/version1，不能据此登记产品缺陷。 |
| D008 | 请求assessment_version3与评估实际version2不同；冻结x-error-cases明确应ASSESSMENT_BASELINE_MISMATCH，实际正确。工具错误期待VERSION_CONFLICT。 |
| 拒绝审计 | 工具把全局/未认证/越权拒绝也要求出现在一个项目的审计列表。44个不在该范围的ID不能证明丢失；37个可见引用对应36个不同项目拒绝审计，均outcome2。其他范围的持久化仍未独立验证。 |

这些是QA责任，不要求产品迎合错误断言。修正工具应明确按原冻结产品契约纠偏，保留旧工具、原失败、说明和新版本，不能修改产品契约或倒改F04结果。D008恢复尾部、重复成员后的last-manager等因原组合用例提前失败而未完整执行，不能补判通过。

## 控制失败与未执行

001 mq_stop返回false/ValueError，形成1项原FAIL；002 api_restart原结果是response timeout，属于UNEXECUTED。备份中两份false响应原样保留，未重放，不能宣称完成了MQ故障或API重启可靠性测试。后续允许的1毫秒中性协议精度容差没有改变旧结果。

其余未执行包括：缺真实scan-wait能力的20任务调度/重启验证、未观察到通知的即时检查、DB故障、明文hash-only初始化、秘密日志扫描、audit-only/commit-loss注入、浏览器、实际库表/代码规模及白盒/人工溯源。尚未覆盖全部声明错误分支，AC01保持未核全。未执行和测试工具问题都不转成产品通过。

13个原PASS覆盖初始化、鉴权及服务范围、真实过期service与注销、三类结构校验、人力/转派与容量竞争、依赖、幂等、任务版本/依赖环竞争、完整状态/评审/上线回滚闭环、评审拒绝及回滚返工人力。它们仅代表已执行断言的有限结果，不是所有规格或性能通过。

## 版本与原始证据

产品源356f29983c904e949245aedfad464efc1bf7b63d；功能工具f877292eaf951ebf7609e23d7e010ce50d2d0cb7218a3f6f1a4dbf035037b453；契约6f07cb53a7d9314240ba93ec490325d3c63dca7e4d077021047e216e7b26f478。实际用例记录时间17:50:59.190272Z至17:55:59.800417Z，runner退出观察与之分列。

原功能证据SHA7dfac9b9c19998ce978681c9bdae385d49fca9a6796c17d852b500a903a6fa60，312条记录、274个HTTP交换均完整认证。加密备份147339字节、SHA2d73639713c2370f9f518b8bb6fcc86ce68110df4b8fd99824b419ea165af5a7；收据JSON与密文/10文件/压缩tar摘要一致，解密后全部10文件SHA已逐一核验。核验收据见F04_BACKUP_VERIFICATION.PUBLIC.json，详细分类见F04_REPORT.PUBLIC.json。钥匙、凭据、私有用例和日志未发表。

本轮没有正式400并发性能结论。P04若运行仍仅证明原源356f的对应指标，不能用于宣称之后修复源验收。性能、代码规模、覆盖率、CI和人工留痕分别核查。
