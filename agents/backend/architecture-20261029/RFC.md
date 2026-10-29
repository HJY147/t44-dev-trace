# R29 后续架构提案：先证据定位，再独立重构

操作者 backend AI；本轮仅离线源分析，原f7产品、正在运行SUT和独立QA文件均未改变/访问。依据仅是root发布的开发短测 `records/cloud/f7-r29-window-20261029/short-summary.PUBLIC.json` 和被测产品源；没有接触本轮独立660秒结果。本文**没有一个已证明能减798行的方案**，不能把下面目标预算写成已减行数。

## 当前事实与定位顺序

开发400-client短burst完成8000请求，0failed/aborted，四类P95为GET456.95、contract343.23、transition617.35、escalation635.95ms。约5.26秒的burst观测吞吐约1521请求/秒，并不是持续600秒的验收吞吐；P95均未达到270。40-client这四类P95为131.04/54.46/86.26/79.93ms；1-client约52.01/51.99/67.98/63.98ms。它说明并发尾延迟上升，**不能区分Python、SQL、socket、proxy或负载端争用**。没有仅凭汇总选择加CPU/加池/改事务。

原`790_http.Client`已经逐请求记录`wall_ns`、`caller_thread_cpu_ns`、`server_timing`、`request_id`，每客户端也有连接次数/建连耗时。API的Server-Timing从同步handler起算，故不包含进入handler之前的ASGI工作线程排队；nginx已有request_time/upstream_time日志。下一步无需加云包装、无需再付费制造相同证据：停机后在原开发证据上按同request_id对齐，分别统计首请求/复用请求、各类/各cohort的wall、app dur、caller CPU、剩余时间及队列峰值。

不得逐项P95相减冒充P95分解；须逐请求先计算差值再分位。Server-Timing不能证明SQL时间；caller CPU不能证明整个负载端CPU。若缺少原字段，结论保留unknown。

## 后端热路径的可执行结构提案（先交数据库岗接口复核）

`identity.authenticate`当前依次读取session、user或service、membership、project（人类项目请求通常4个DB round trips；服务项目请求通常3个，依据代码分支，不是实测SQL账本）。普通GET由prepare和main各调用一次；写请求由prepare、claim共享会话锁、main locked_scope再次验证。独立事务、共享会话锁、主事务撤权重验及members/task锁序都是安全语义，不得为了速度删除。

提案A：保持这三个阶段与错误优先不变，数据库岗提供一个**预检查只读身份快照**函数，把未加锁的session/主体/membership/project事实通过严格限定的outer join一次读取。必须保留缺session、revoked、expired、inactive subject、service scope、member、project的既定错误顺序；不能把SQL里过滤条件直接吞掉造成不同错误。共享/更新会话锁阶段仍先锁session再读取其余事实，禁止把原会话锁扩成无关用户/项目的锁，禁止在nullable outer join上猜锁范围。函数不缓存token，也不跨事务复用授权快照。

拟接口：`g.identity_snapshot(token_hash: bytes, project_id: int|None) -> Snapshot|None`，Snapshot含原完整session、原subject、membership和project的独立命名字段，完整null保留；SQL查询、绑定/allowlist、安全错误、session返回映射由数据库岗负责。后端只负责顺序判断和Call赋值。新代码须全部计入原application范围。该方案**可能净增约40–80行**，目标是实质减少往返而非规模达标；在没有真实SQL账本前不实现，不占云调参。

提案B：把成功HTTP响应的序列化/Envelope生成/校验编译为每个已冻结Operation的只读计划，只在启动时编译schema路径。运行时仍保留业务data提交前校验和完整Envelope输出校验，仍输出原错误/Server-Timing/0/null。不能用“相同功能”删除一个检查层，不能重新把公开validator改成共享可变对象。现有56行contract适配已经从OpenAPI生成Operation；前一微缓存仅约0.02ms收益，不作为本轮方向。

## 规模闭合的现实边界

本轮重读同一严格计数器（committed .py/.ts/.vue/.css/.html，原三个应用根，不改范围）。公开复计5898/65件、超798。当前服务1399、持久1672、前端1099、调度642、消息326、领域275、API244、CLI147、契约56、设置38。架构已经采用OpenAPI派生路由/模型/字典、DDL派生Core metadata、共用Call/CAS/page/Rows、schema驱动递归前端，不能把已实现的抽象再次预扣为新收益。

要得到真实≥798，必须完成一个新全量实现并把新增抽象一起计入。例如给出后端/领域/API联合替代上限1350（现1918，需减568），加数据库/调度/前端净减至少230。**这只是必要预算约束，不是现实收益证明**；当前源边界中各proof/审计/撤权/故障分支并不重复，不能称这个目标已经可实现。

本轮可核候选的范围如下：

|工作包|可以实际做的事|当前可证明净减|
|---|---|---:|
|身份/授权往返合并|A的跨岗接口与同SQL语义差分|0；很可能净增|
|响应计划|保留两层验证的纯函数/编译路径试验|0；未实现|
|domain/workflow合并|先列错误优先和proof读取矩阵，禁止移除pure API|0；没有大块重复|
|migration统一描述|同MySQL目录快照/规范化器统一，而非放宽校验|0；跨岗待提案|
|frontend公用取消/刷新/重放状态|保持UI/89测试/visual要求，owner重构|0；不能承诺数百行|
|scheduler/MQ共用租约执行器|保留各自数据库扫描/MQ confirm/失败/截止语义|0；不得为代码规模强合并|

没有证据支持“只要换一个manager/class/framework就能减800”。单纯把policy写到JSON/YAML/SQL或excluded包只是转移逻辑；把多行压成一行、删UI细节/审计/造数/校验或改796断言也不采用。若严格上限坚持不变，当前工作仍必须列为未达标；需要一次更长的离线产品重构阶段，不能靠剩余云时间现场猜。这里不请求用户放宽要求、不称任务已经完成。

## 等价验证与交付拆分

1. Root保留当前f7已运行证据和SHA，原SUT不动。先从开发raw提取既有时间字段，确认瓶颈层。
2. 数据库岗审A接口/SQL锁范围；后端写纯Snapshot→原Call决策差分（所有错误优先、service/human、None/0、过期/撤销/不活跃/跨项目）。没有字段/锁序等价证据不合并。
3. 针对A保持原796功能基线；额外运行985真实MySQL撤权/锁顺序/失效租约/审计故障，以及Rows所有SQL注入/表达式拒绝。旧认证阶段不能换成缓存，native MySQL证明不能被SQLite替代。
4. 每个规模包先给完整正常格式替代，固定cloc实际测新+旧删除总净值，再实现owner目录；每包回归通过后才汇总。未交付新运行替代时净减=0，不能预支800。
5. 最终统一新SHA全796、前端89、覆盖/契约/静态和严格LOC，同SHA实际完整400-active/60+600秒。任一层失败保留；不用“重构设计通过”代替实现或性能通过。

本岗没有足够证据交出一个真实≥798的闭合方案，故本轮不改生产、不过早让其他owner投入多模块重写，也不污染正在进行的独立测试。
