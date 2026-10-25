# 消息去重候选 c4b3f114 限定代码审核

## 1. 对象与基线

审核者为 AI reviewer，实际提示词 `ROLE-reviewer-ROUND9-v1`；自有分支
`codex/review-size-round9`，主基线 `043fc464`。
被审产品准确 SHA `c4b3f114a5525c0fe0fd031d2b3603070a2be892`，最终证据
`2c1dd10e2867c9ffa8de33bfbf48993a864c5a86`。相对当前主基线，应用只有
`backend/t44/messaging/broker.py` 与 `facade.py` 两个文件变化。未接触独立用例、
PRIVATE 日志/密钥、云账号或运行环境；本岗没有编写被审产品。

## 2. 需求映射

消息传输仍保留连接/发布/接收/心跳的各类无凭据错误，消费仍在 DB 提交后 ACK，
毒消息死信拒绝，持久失败 NACK 重投。通知列表仍限定当前有效项目资格与 recipient，
read/handled 两状态分开、分页和计数独立；写操作仍经成员 share 锁、notification
update 锁、资源归属、本人收件人和版本 CAS。没有需求、接口、DDL 或门禁变更。

## 3. 差异与责任

Broker 用一个私有 contextmanager 统一网络异常后的关闭和脱敏；connect 独有的
ValueError 仍单列。False-NACK 仍原码、不额外关闭；非网络 ValueError 仍原样传播。
`StatementRejected` 和 `UnicodeError` 均为 ValueError 子类，因此删去 except 中
冗余名字没有取消死信行为。

Facade 将三条同形有效成员查询收口，复用已存在 common.page。额外的次排序 id
在唯一主键 id 降序下不改变结果；显式单项目成员查询增加稳定排序时最多一条有效
成员记录。项目未找到仍先于成员资格错误，成员锁序、CAS 和事务 owner 未改变。
内部 project_id=0 不在冻结 HTTP 正整数输入域；本审查不宣称任意非法内部调用等价。

## 4. 接口与数据库兼容

公开签名、wire 形状、API/DB 文件和表约束不变；没有迁移、数据修补、事务新增、
commit 移动或主机端口操作。RowsGateway 仍生成参数化 SQL，原 membership share
和 notification update 锁保持。Worker、CLI、确认/重试/降级恢复完全未改。

## 5. 正确性与边界

逐条核对了原异常层级、_operation 嵌套、close 清理失败、False-NACK、应用异常、
消费 DLQ/NACK、分页、独立计数和项目资格优先。未发现本差异引入的实质阻塞。
这不是已证明真实 RabbitMQ/MySQL 竞争、吞吐量、网络故障恢复或正式验收。

## 6. 实际执行

从准确已提交候选 git archive 产品及消息开发测试到本岗 `tmp/802_review_size_round9`。
使用既有 Python3.12.10/pytest9.1.1 运行；首先预加载归档包并核对实际 broker/facade
路径和 SHA，再执行 39 个模块/SQLite/故障性质开发测试：**39 通过，23 integration
未选择**。详见 messaging-bound.log/xml。首次运行缺少实际导入绑定，保留 messaging.log/xml，
不将该次作为候选证据、也不与后次叠加计数。未运行完整 CI、真实 MySQL/RabbitMQ、
Docker、云性能或独立验收。已有 Starlette/httpx 警告保留。

使用固定 classifier 与 cloc2.10 官方 hash，完整已提交应用归档 **5875→5862，净13**；
65 文件；其余应用字节不变。证据 messaging-count.json。初次仅归档 backend 得
4776→4763，明确保留为 backend-only 而非主指标；补齐同一版本 frontend1099 后
才核对上述主数。另一次无过滤目录扫描含 JSON/SQL/README，保留为 not-main，
没有拿32089当主指标。没有改计数脚本、排除根、格式或文件扩展名。

## 7. 十项与门禁

| 项 | 判定及范围 |
| --- | --- |
| 1 身份/版本 | 通过；AI reviewer 审其他 owner，准确产品 SHA |
| 2 需求/范围 | 通过；仅两个消息产品文件，无需求或测试降标 |
| 3 接口 | 限定通过；公开签名/输出和消息分类保持 |
| 4 数据库 | 限定通过；无 DDL/事务 owner 变更，真库未运行 |
| 5 状态机 | 不适用；任务迁移产品字节未变 |
| 6 权限/边界 | 限定通过；项目/recipient/share 锁保持 |
| 7 事务/并发 | 静态未见新阻塞；真实多进程竞争未复跑 |
| 8 幂等/故障 | 模块故障性质通过；真实 MQ 未运行 |
| 9 证据真实性 | 通过；实际 import/hash/39 与未选23分开 |
| 10 全门禁 | 未验证；新合并准确 SHA 的全 CI 待 root 执行 |

## 8. 结论及复审

**限定代码审查未见阻塞，建议进入 root 的集成验证。** 新准确合并源须跑完整既定 CI，
再决定发布；不发 reviewer/stage success，不自我 APPROVE、不合并、不改主干。
即便根整合该候选，代码规模仍超762行；正式性能和独立验收也不由此通过。

本岗同时静态审核 API wire 候选2914c7d，准确归档/预加载后12边界测试通过，
不重复开发155/1759的结果。其两表达式复用未见新阻塞，但净0行、整体速度收益
NOT_PROVEN，因此不作为本次规模优化推荐，交 root 单独选择。
