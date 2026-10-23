# M6 实际问答与纠正

整理者：AI guidance；归档时刻：2026-10-23T20:42:36Z。以下是本轮实际 collaboration 消息逐字归档，不是学生/教师访谈；消息工具未提供逐条发生时刻，不推定精确收发时间。当前源码讲解基点为 `0783a42b26038d7d3e5a1fe07ae8219a47f06493`；候选修复的状态只归属于答复所述版本，不转写为基点代码或整体验收结论。

## M6-QA-01：后端事务边界

实际提问者 `/root/guidance_checkpoint`，接收者 `/root/backend`。实际问题：

> 指导岗 M6 只读教学澄清（不涉及独立测试）：请以当前源码回答 1 个问题：新手从 Vue 的一次业务保存追到 backend/api.py execute_operation，再到 save_task/UoW/outbox，最容易误解的一个输入输出或事务边界是什么？可给精确函数/路径；未提交中的 Issue28 reason 修复我会明确未通过。你的真实回复将逐字归档，不作人类访谈。

后端 AI 岗实际回复：

> 按当前已提交0549ea89ce218ecb945cd4346671f20d46fad215源码纠正名称：api.py没有execute_operation，实际create_app内endpoint→handle（约219行）调用Runtime.execute（services/runtime.py:235）；也没有统一save_task，改期是Tasks.changeTaskPlan（services/tasks.py:102）→Call.cas→Projects.schedule_diff（projects.py:173）。新手最易把“业务函数返回changed task”误认为“已经提交”。它返回的是当前UoW内拟提交的数据；Runtime仍要在同一主事务写成功audit、outbox、幂等完成快照并校验data，with正常退出才commit。任一步失败先rollback/close，再新UoW持久拒绝audit；claim首事务独立，所以失败后有幂等租约不等于任务成功。成功outbox只证明事件待可靠投递，不等于RabbitMQ/用户已经收到。HTTP断线/commit ACK不明也不能盲目新key重写，应沿相同key恢复。Issue28已提交产品checkpoint，18必要开发目标过（含7真MySQL），原始证据正补；尚未组合CI/专审/UI/独立验收，不写未提交或最终通过。

本岗核对/处理：提问中使用的 `backend/api.py`、`execute_operation`、`save_task` 是指导 AI 的不准确泛称；真实包是 `backend/t44`，实际函数如回复所列，已在基点文本逐项核对。纠正者是后端 AI 岗，不计学生独立发现幻觉。提问时写“未提交”也已被实际回复纠正：0549是其已提交候选，未完成组合验证和专审；本岗不宣称候选通过。这里的18/7为责任岗所述自测状态，本岗没有运行或独立确认，不计入832的437项。

## M6-QA-02：前端怎样找到请求

实际提问者 `/root/guidance_checkpoint`，接收者 `/root/frontend_logout`。实际问题：

> 指导岗 M6 只读教学澄清（不涉及独立测试）：请以当前源码回答 1 个问题：一个新手怎样在 Vue 页面找到“点击保存→38op client→HTTP”的具体入口，哪些输入/响应是在前端组装或显示？可给精确函数/路径；进行中的 Issue28 reason 我会写待验证。真实回复将逐字归档，不作人类访谈。

前端 AI 岗实际回复：

> 前端AI岗位当前源码答复（非人类访谈）：从 /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/frontend-logout/frontend/src/views/WorkspaceView.vue 的 open() 看起，它把 operation（如createTask）、schemaName、路径params和preset交给OperationForm；任务抽屉的operate()/transition()也会发同类参数。保存入口是 /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/frontend-logout/frontend/src/components/OperationForm.vue 的 submit()：先validate(schemaName,draft)做本地必填/类型/证据格式检查，再intentFor()按operation/params/body生成或复用本次幂等key，最后request(operation,params,{},draft,intent)。真实HTTP在 /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/frontend-logout/frontend/src/api.ts 的 request() 内唯一fetch：用operations表查方法/路径，替换project_id/task_id等、拼query，把draft JSON序列化并带当前Bearer和Idempotency-Key。operations表在 /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/frontend-logout/frontend/src/contract.ts 从冻结specs/contracts/openapi.json的31路径/38operationId生成，不是38套手写client。响应是Envelope.data+meta；OperationForm显示成功/历史重放含义，再await props.saved()刷新最新权威数据；422字段提示、已知人力业务解释、409刷新/版本采用和503同操作重试分别显示。前端组装表单/路径/JSON、显示错误和新记录；真正权限、状态出口、容量/依赖/版本/审计和事务由服务端判定。本地“检查填写内容”是submit(true)→validateContractPayload，不是业务保存、更不能证明业务守卫已通过。会话变化/组件卸载时旧异步响应不可回写新身份。当前Issue28字面理由是独立前端候选c79，尚待新后端872真实联调，不能写整体已通过。

本岗核对/处理：基点的 open/operate/submit/request/operations/saved 和会话检查均按文本核对。候选 c79 本地分支精确 SHA 为 `c79cd9930febadfa77cb2d0eede7626d4039c305`（只读取 Git 元数据，未在本岗运行候选）；“后端872”是对方原话中的阶段称呼，不在此猜测为新的 commit。仍待 root 安排准确组合验证、专审和公开结论。

## 与学生原始材料的关系

R001 是本人关于人把关结构、I/O、需求与测试的观点，本轮据此编排学习步骤。R002 只读公开 provenance；其记录表明课程反馈已提供，但最终研究正文未提供。未读 R002 私密原文、封面、任何 `tmp/independent` 内容或未发布测试材料；未联系独立测试岗。

本轮新增的是两次 AI 跨岗询答及一份待做练习。没有学生的新问题或答卷，没有新增人类采纳、人工改码、断点、实验或独立识别幻觉的证明；不把两岗回复改写成学生口吻或最终研究正文。

## 后续实际状态补记（保持原答复时点）

上述答复收到后，root 实际通知：“新组合源码已根合并42243eb23aedf0edda7541ad83fd87ec3d17b616（0549 BE + c79 FE），CI刚触发，尚无整体验证。”这是总协调状态输入，不是本岗测试；M6 保留原问答与0783源码截止，不等CI、不宣布新组合通过。
