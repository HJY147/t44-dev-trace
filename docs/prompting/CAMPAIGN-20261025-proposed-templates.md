# 本轮新提炼的可学习prompt模板

作者：AI提示词工程岗；状态：proposed / NOT_EXECUTED。三个模板均在本轮事后提炼，不是旧真实prompt、未发送给任何岗位、未作为测试输入；新增已使用演进版本数0。事实依据见同目录CAMPAIGN-20261025-process-appendix.md，本文不应发送给独立测试岗继承开发上下文。

## T1：冻结中性输入后单次执行

```text
仅使用清单中冻结的需求、接口、工具和中性运行资料，逐项记录source SHA、freeze hash、grant hash、native runtime、CA、资源和截止时间。先核准入与身份，再执行一次授权phase；不继承开发讨论、旧得分或预期结果。严格保留原case/oracle/阈值；不得自动重试或延长时间。分开计实际请求、完整响应、完整postconditions、完整case与正式负载组；退出0只表示进程状态。缺输入或证据不完整如实NOT_PROVEN，发布允许摘要，不公开私有案例、凭据或原始正文。
```

提炼理由：v5的201没有完整正文，v6的退出0没有完整case，freeze或短组件绿不能取代完整结果。局限：这是拟议工作规范，不证明一次执行已经按它完成；实际新测试实例仍由总协调fork_turns="none"创建。

## T2：修复执行工具时保留业务边界

```text
先固定原失败状态与公开错误，区分产品、准备环境、transport和schema工具问题。只在允许公开的通用输入上构造最小复现，禁止读取私有业务oracle或偷改案例。新候选另建freeze，并用相同generic输入/schema/expected核修复；记录修复前后原始结果。复审精确source与差量，再申请新的phase grant和全新无历史执行operator；旧grant、旧期限和旧结果保持，不把工具绿写成产品绿。
```

提炼理由：union type列表错误属于checker兼容性；公开89项只支持限定工具证据。局限：未执行；本轮未自行复现、改工具或读取private schema，不能预断所有JSON Schema或业务响应通过。

## T3：让时间起点和资源namespace成为接口

```text
将请求phase起点绑定实际supervisor launch receipt，不使用晚启动provider的时刻。fresh provision目标必须在controller已批准父路径之内，以本次supervisor nonce/request nonce创建，不覆盖旧目录。精确核source/native/runtime/phase/资源/nonce/UTC与monotonic截止；每个有副作用阶段用剩余预算裁剪timeout，先stage、复查截止后排他发布。失败保存partial事实，未知已提交副作用不冒回滚。旧环境按owned身份正常收尾，保护共享服务，登记真实generator PID与缺失采样，不把身份登记当600秒覆盖。
```

提炼理由：v6曾错误采用provider起点和批准前缀外fresh目录，后续v7新provider另审；F/P须分阶段及正常资源收尾。局限：未执行；接口/静态路径正确不保证真实controller、OS调度和完整业务成功，须另取各阶段实际结果。
