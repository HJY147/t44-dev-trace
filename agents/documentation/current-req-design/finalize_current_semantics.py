from pathlib import Path
import re
R=Path(__file__).resolve().parents[3];p=R/'reports/final/design-report.md';s=p.read_text();a=s.index('## 9 包、进程');b=s.index('## 25 存储对象',a)
new='''## 9 当前包结构与组合入口

当前生产包为backend/t44。api.py将同步FastAPI路由、结构校验、Runtime和业务门面连接起来；__main__组合运行角色及凭据provider。domain/models.py与state_machine.py存放稳定编码及纯状态判断；services内项目、任务、评审和Workflow使用注入gateway完成业务，persistence提供Rows与UoW，scheduling和messaging执行扫描/投递进程。它们是同一业务实现的责任分层，不建立各自不一致的状态解释。

数据库连接与会话生命周期由组合根及持久层管理；领域层不构造engine、HTTP客户端或MQ连接。Runtime.execute接收Call与校验器，返回status、body、replay和original_request_id供HTTP层包装；这个四元组不是对外Envelope，重放业务结果也不要求整个HTTP字节与旧响应完全相同。当前meta的request_id、server_time与replayed仍按当前响应生成。

Call携带operation、request_id、token、path/query/body、幂等key、主体及项目上下文等。token只在受控调用链内使用，不进入公开示例。配置、密钥和数据操作必须有明确本项目作用域；初始化账号存合法Argon2id摘要，不能将普通明文口令送到持久层冒充摘要。

## 10 七态九动作及主体细化

| 动作 | 原态与结果 | 主要当前证据 |
|---|---|---|
| start | 1到2 | developer且owner本人、工时与全部前驱已交付 |
| block | 1/2/4/5到3 | 原阶段授权、原因、责任环节及blocked_from_state |
| unblock | 3到来源1/2/4/5 | 对应原阶段权限、解除依据、必要依赖与人力 |
| submit_review | 2到4 | owner、当前artifact revision与提交证据 |
| approve_review | 4到5 | 本轮通过评审、禁止owner自审、模板与证据完整 |
| reject_review | 4到2 | 本轮不通过评审及理由、评审周期推进 |
| deliver | 5到6 | 经理、当前评估和独立批准及发布依据 |
| rollback | 6到7 | 经理、交付绑定预案/版本及回滚依据 |
| rework | 7到2 | 新计划、有效developer与当前工时、前驱满足、新周期 |

BLOCK/UNBLOCK在开发阶段要求developer且本人owner，评审阶段允许reviewer或manager，其余阶段为manager。相同账户可以具有多个项目角色，但角色存在不消除owner限制或独立性要求。评估创建人与复核人必须不同；D008仅在DELIVER原批准引用失配分支内作基线错误的有限顺序选择。

## 11 会话与输入安全设计

当前会话为高熵不透明Token；数据库只保存摘要、session_id、过期、撤销及scope，不保存可恢复Token原文。Runtime在操作中按当前主体和项目成员关系复验；登出撤销、过期、服务scope不符或跨项目读取不能因前端仍显示按钮而被接受。service主体按项目白名单和操作scope执行，不能借服务身份代替经理发布/回滚。

所有查询通过表/列白名单和参数化条件进入gateway。参数化阻止SQL拼接，但不代替归属和角色验证；合法类型的另项目任务ID仍须拒绝。Schema的required、枚举、长度和UtcTime与领域检查承担不同职责。UTC DATETIME(6)保留微秒，日期比较不靠容易越界的planned_end加24小时运算；非法精度和无效日期不能静默截断。

## 12 事务与幂等故障分支

请求先经历当前身份和输入校验。对于需幂等的写操作，Runtime.prepare在独立claim事务中共享锁会话、锁定唯一scope，必要时SAVEPOINT插入新租约，然后提交。GET不创建claim。相同scope同hash且COMPLETE时返回已完成业务快照；不同hash拒绝，活动租约拒绝IN_PROGRESS，过期接管更换owner_token并由围栏保护旧owner。

主事务按会话、claim owner、必要项目图锁、有序成员与有序任务锁次序运行。任务版本检查与CAS后，成功业务、audit、outbox及幂等完成快照同一次主事务提交。拒绝先回滚业务，再在独立事务写失败audit；只有仍有claim所有权且满足当前状态等条件时才能完成可重放错误，不能把全部4xx/5xx统称COMPLETE。CommitUncertain返回503并保留已提交可能性，同一scope调查/重放优于另造key重发。

成功结果保存实际完成请求的response_request_id，重放original_request_id由其溯源；重新接管后的完成者可以不同于最早认领者。审计中的理由和前后值保持原文，旧记录投影响应不能回写历史。数据库提交与MQ publish不构成分布式原子事务，可靠性由outbox、租约、重投及幂等消费共同建立。

## 13 扫描和消息伪代码与成本

```text
tick:
  顺序恢复同rule_hash且心跳陈旧的旧scan（最多100）
  再创建新run，固定cutoff与高水位
  循环按last_task_id作keyset分页
    每个候选读取当前token provider并通过Runtime执行业务
    结果已确定才保存checkpoint
  空页时完成，保留原started_at用于恢复来源
```

C个候选、页大小P至少产生ceil(C/P)+1页查询与C次checkpoint，并包含每候选业务事务。keyset减少offset跳过，不表示索引扫描行恒等于C；索引不覆盖state/planned_end/id时实际扫描行可能更多。恢复旧UUID不重置started_at，每次token provider调用可读取当前凭据文件；heartbeat增长只证明进度，不能替代完整成功。

```text
publisher: 短事务claim outbox与租约 → 事务外publish → broker confirm后持久confirm
consumer: 校验消息 → 数据库权威事件/锁outbox → 幂等写通知并提交 → ACK
失败: DB未提交则NACK/requeue；非法消息reject；MQ不可用按事件类型fallback或retry
```

单轮batch B的发布/消费循环是O(B)，R个收件人通知写入另有O(R)。网络、索引、锁、重投和日志持久化影响真实耗时。丢失ACK允许重投，数据库(event_id,recipient_id)唯一约束防重复业务通知，不声称网络传输exactly-once。已读和已处理字段不会被重复消费覆盖。

## 14 依赖图与锁定成本

新增K个前驱时，当前算法构建项目邻接表，对每个新增前驱各自重置visited并作迭代DFS，遇目标即拒绝。项目N节点、E边，最坏Python遍历O(K(N+E))，内存O(N+E)；完整项目边读取还产生O(E)结果传输，不能用一次共享visited的O(N+E)描述现行实现。

任务转换对D个前驱作O(D)状态检查，取行和有序锁定含O(DlogD)排序及D次数据库往返。CAS虽作用一行，仍有索引、锁、日志和提交成本。待优化的重复查找与同事务已锁行复用尚未实施，不能在设计图中画成已消除所有往返；任何优化仍须保留最新权限、版本、依赖和错误次序。

'''
s=s[:a]+new+s[b:];s=s.replace('但profile仍actual_loaded=false、root_approved=false，不能写成已部署。','该构建阶段profile曾为actual_loaded=false、root_approved=false；后续p13现场已另核原七容器身份，两个时点不能混为一个状态。');s=s.replace('本次尚未实际备份或恢复。','本阶段未据此声称应用数据隔离恢复演练通过。');p.write_text(s)
