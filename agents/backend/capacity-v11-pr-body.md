完整工作流后端包含38个HTTP操作、严格JSON Schema、opaque会话撤销、状态/证据/预案/决策及UoW幂等/CAS/审计/outbox。旧IAT01–05修复源479fc8f真实CI362通过、0失败/错误/跳过；该结果不代替本次1.1源。

按D005/D006用户采用、bbc设计审查、189dc4a正式1.1父链冻结后，实现容量生命周期：接手人必须先登记当前迭代工时；新capacity覆盖全部状态1–5任务owner；6/7可移出、返工前补回有效developer与capacity。成员保护仍1–5+7，开始前转派范围不变。assignment新增项目锁，创建/迭代变更/返工同序保护；成功审计/outbox/幂等快照与业务原子，拒绝独立审计、旧成功重放及原错误优先级保持。不改冻结14文件/18表226列。

冻结前合同/夹具修复单独提交，真实草稿时序保留。冻结后定向21项HTTP/SQLite与7项MySQL8.4/t44_test通过，后者含三类动作各两种真实项目锁先后及合法转派后移除旧owner双成功。版本上限错误优先级追加用例先1失败后修复1通过，最后统一源等待全量CI。终态采用明确合成fixture，不冒充完整实际交付历史。严格本地Ruff/Bandit/格式通过；root授权只合并975既有两个with，原上下文顺序/断言保持。原失败及源码hash在agents/backend/capacity-v11-*。

当前未部署新业务；精确新SHA全量CI、独立复测/正式性能/3500–5100源码范围尚待。955回环直连仍待后续独占窗口验证，当前不运行负载。PR保持draft。

Agent-Role: backend
Prompt-Ref: ROLE-backend-CAPACITY-V11-IMPLEMENT-v1
Refs: #3 #12
