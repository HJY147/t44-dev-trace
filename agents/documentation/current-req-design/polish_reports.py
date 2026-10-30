from pathlib import Path
import re
R=Path(__file__).resolve().parents[3]; p=R/'reports/final/requirements-report.md';s=p.read_text();generic='图中展示该需求的主体、输入约束和可观察结果。箭头表达业务依赖或责任流向，不授予额外角色权限；每个成功结果仍须结合正文中的拒绝条件和持久证据判断。'
notes=[
'图1将调用输入、业务准入与可定位证据分开。冻结契约规定报文形状，项目归属与角色决定能否执行，成功结果还须有对应请求ID；因此结构合法的跨项目请求仍应被拒绝。',
'图2从四类核心对象进入字段与约束评审，再到准确库的迁移与实际目录核对。字段字典、建表语句与真实库表各有证据，不能用模型类存在替代已正确建库，也不能用一次迁移返回码覆盖partial事实。',
'图3强调批准是带适用版本和独立主体的证据。评审范围、代码revision及交付/评审周期共同决定批准是否仍可使用；新提交不应沿用已失效批准，缺证据条目不能标通过。',
'图4把人力引用、依赖满足与计划差异列为不同约束。当前成员身份有效不代表当前迭代有工时，登记工时不代表前驱已交付；开始、解除到开发及返工都需满足其对应当前条件。',
'图5中的回滚是由经理作出的业务决定，保留影响和依据，不是删除任务数据。返工进入新周期后，旧风险评估和评审不能直接作为新发布依据；更新基线仍需独立批准。',
'图6画出主交付链与拒审/返工出口。阻塞仅能来自1、2、4、5四种状态；blocked_from_state保存确切来源，解除时恢复该来源，而非一律回到开发中。行为权限还随原责任状态变化。',
'图7区分可靠受理、MQ投递、通知持久化与用户处理。重复投递可以发生，要求的是数据库业务效果幂等；用户点击已读不会替经理解除阻塞，也不自动推进任务状态。',
'图8表明验收应反向追踪到需求和准确源码。开发CI、独立AC和最终提交材料分层核对，任一层的绿灯不能代替另一层；学生本人留痕和观点仍需真实证据。']
for note in notes:s=s.replace(generic,note,1)
s=s.replace('旧正式失败与H2不确定结论保持；尚无有效正式性能结论，未通过最终性能验收','当前p13独立NP，四P95约1011–1096ms且内部raw/后置完整性不足；未通过最终性能验收')
s=s.replace('尚无有效正式性能结论，未通过最终性能验收。本轮','当前p13独立NP，未通过最终性能验收。本轮')
p.write_text(s)
p=R/'reports/final/design-report.md';s=p.read_text();start=s.index('## 15 分层与组合根设计视图');end=s.index('## 25 存储对象',start);s=s[:start]+s[end:]
items=[
('## 1 设计依据和架构','sdd1','分层与组合根','API是组合根而非领域判定器：路由把HTTP输入转为Call，经冻结contracts验证后调用注入的Runtime。Runtime安排鉴权、幂等、锁和UoW；Business与domain返回业务结果或Decision，不自行建立连接或commit。Rows只接受活动UoW的gateway，避免业务层旁路事务。前端将服务器错误反馈给用户，不拥有最终状态写权限。'),
('## 1 设计依据和架构','sdd2','运行组件与职责边界','浏览器仅访问API；API、scheduler和consumer虽分进程运行，仍共享单体领域与持久化规则。scheduler通过注入门面可靠受理升级，consumer使用数据库权威事件创建通知。RabbitMQ承载事件投递而非业务最终状态；服务启动配置、数据库连接工厂和token provider由组合层注入，不在纯状态机中创建。图中数据库是状态与证据权威，组件间协作不能把broker确认当数据库提交。'),
('## 2 数据模型与存储','sdd3','核心实体与版本关联','项目到任务是一对多，task_dependencies以task和depends_on_task两个外键引用同一tasks域，并限制同项目、非自身和无环。任务关联多条不可变reviews、release_assessments和decisions，任务上当前批准/评估引用还带版本与周期，不能只按最新时间猜有效结果。task.version、schedule_version、delivery_cycle和review_cycle对应不同失效原因，决定与审计保留历史而不覆盖旧记录。完整基数与约束以18表DDL及字段索引为准，本图只展示六类核心联系。'),
('## 3','sdd4','状态与拒绝闭环','domain状态判断产生允许/拒绝Decision，Runtime在已经核实的角色、任务版本与证据上下文中执行CAS。BLOCK只接受1/2/4/5并保存blocked_from_state；UNBLOCK回确切原态。开发态由developer且本人owner操作，评审态允许reviewer或manager，其余责任态由manager；不能笼统说经理可解除所有开发阻塞。回滚7到返工2需新周期、人力和依赖重新有效。非法动作与并发失败不得遗留半次业务写。'),
('## 3','sdd5','成功事务与拒绝审计','幂等claim先在独立事务创建或取得租约并提交；随后主事务重新核owner、权限和锁范围，业务变更、成功audit、outbox及幂等COMPLETE结果共同提交。拒绝路径先回滚业务再由独立事务留下拒绝审计；不能画成所有拒绝都与成功主事务一起提交。提交结果不确定时503不保证未写，调用者须保留同一幂等scope调查或重放，不能改key盲目再执行。'),
('## 3','sdd6','幂等scope与租约围栏','业务幂等唯一scope由actor_kind、actor_id、operation_id和key组成，另比较请求hash。相同scope同参数可复用已完成快照，异参冲突必须拒绝；租约续取和owner fencing防止旧执行者在新owner取得控制后提交。材料生成的nonce只绑定运输材料，不是业务幂等key。当前实现仍为先锁读再插入的原路径；唯一约束优先插入只是未采用候选，不在本图宣称已实现。'),
('## 6 前端交互与会话','sdd7','鉴权与会话生命周期','服务端读取真实会话摘要、scope、expiry和revoked，并在项目有效成员范围内核具体操作权限。前端clearSession增加上下文序号并卸载shell和浮层；fetch成功、JSON解析之后以及失败catch都检查token/context。旧响应不得写入新身份的字典、项目或通知，也不能触发新会话表单刷新。退出失败保留当前身份，已发出的写请求可能仍在服务端完成。'),
('## 4','sdd8','依赖排期与有序锁','锁次序为session、幂等scope、必要项目锁、按user_id有序成员、按主键有序任务与关联对象。项目锁模式依操作选择share或update，不是每次transition都FOR UPDATE。start/unblock/rework涉及依赖图范围，取得任务锁后重新检查版本、前驱与当前人力，CAS与计划差异、审计、outbox同主事务提交。前驱逐项读取产生O(D)数据库往返与O(DlogD)排序，不可笼统称常数成本。'),
('## 5 消息与扫描算法','sdd9','扫描恢复与MQ降级','Scanner.tick先顺序恢复同rule_hash且心跳陈旧的既有scan，再创建新run；恢复保留原started_at，固定cutoff/高水位和持久last_task_id。每候选重新调用token provider，结果确定才checkpoint，单靠heartbeat不能证明完整扫描成功。outbox在短事务claim，事务外publish；consumer验证三字段消息并核数据库事件，DB持久通知后ACK。丢ACK允许重投，靠唯一键及锁消除重复业务效果，不能标为传输exactly-once。'),
('## 7 部署备份与恢复','sdd10','部署备份与证据边界','运行必须绑定实际源码、镜像/config及资源，而不是只记录构建标签。应用数据备份与独立测试密封证据是两条链：前者保护配置/数据库/消息卷，后者保护原始测量与身份回执。p13已完成密封下载且75文件hash通过，内部raw prefix仍比footer短，因此两种完整性结论不可混用。本轮两VM已由用户确认关闭；新稿不设置自动关机，测试和证据回收后由用户手动停机。')]
for heading,fig,title,text in items:
 pos=s.find(heading)
 if pos<0:pos=s.find('## 8 设计验证')
 e=s.find('\n',pos)
 block=f'\n\n![{title}](../../docs/reports/diagrams/CURRENT-20261031/{fig}.png)\n\n{text}\n'
 s=s[:e]+block+s[e:]
s=s.replace('当前连接采用UTC、严格SQL模式及READ COMMITTED','当前连接采用UTC、严格SQL模式及READ COMMITTED')
s=s.replace('本次尚未实际备份或恢复。','历史此项的未验证范围按当时记录保留；当前新增p13测试证据密封不替代应用数据恢复演练。')
s=s.replace('当前设计使用非root镜像','镜像构建时点与后续现场部署时点分别登记；当前设计使用非root镜像')
s=s.replace('尚无有效正式性能结论，未通过最终性能验收','当前p13已实际运行但独立NP，未通过最终性能验收')
p.write_text(s)
print('Removed generic duplicated FR text, integrated18 figures with topic-specific explanations and current NP status.')
