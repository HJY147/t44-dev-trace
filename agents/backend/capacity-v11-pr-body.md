冻结v1工作流后端包含38个HTTP操作、严格JSON Schema、opaque会话撤销、状态/证据/预案/决策及UoW幂等/CAS/审计/outbox。已发布IAT01–05修复源479fc8f真实CI362通过、0失败/错误/跳过，全t44行88.56%；这是旧源开发CI，不是独立复测或本次1.1结果。

本次按D005/D006用户采用及bbc限定设计审查，显式演进容量生命周期1.1：接手人先登记当前迭代工时；新capacity覆盖全部状态1–5任务owner；6/7可移出、返工前补回有效developer和capacity；成员保护仍1–5+7，原开始前转派范围不变。

当前90e01f6仅提交1.1权威/运行契约与README/design，真实OpenAPI及38操作错误声明一致性检查通过，31paths/38ops及DDL18/226不变。根建立新的父链freeze后才继续守卫/锁/业务回归；业务草稿未入此checkpoint，未部署。原v1摘要保留，不冒称旧字节仍等于新契约。原逻辑新增开发回归11失败/2通过已保存，后续验证包括真实MySQL竞争与合法串行双成功。

955首次诊断仅setup，两服务退出0但bootstrap非JSON502，无fixture/负载样本；工具回环直连修正仍待下个独立窗口验证。性能阈值与3500–5100源码范围仍未通过。PR保持draft。

Agent-Role: backend
Prompt-Ref: ROLE-backend-CAPACITY-V11-IMPLEMENT-v1
Refs: #3 #12
