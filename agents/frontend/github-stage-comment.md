Agent-Role: frontend
Prompt-Ref: ROLE-frontend-M0-COMMIT-v1
Refs: #2

实际初始化产物：
- `agents/frontend/WORKLOG.md`：真实执行与文档岗询问/回答记录。
- `reports/modules/frontend.md`：页面责任、后端/消息输入输出和 403/409 展示边界草案。
- `records/handoffs/frontend.json`：状态、未验证项、问题及提示词关联。
- `agents/frontend/github-stage-comment.md`、`agents/frontend/github-backend-interface-question.md`：本次真实评论正文。

当前为初始化文档阶段：业务代码未实现，未建立前端项目；前端自测、联调、独立验收均未运行。本轮只做本岗文档和 JSON 校验及阶段 Git 提交，不表示产品功能或门禁通过。

全部页面与接口仍未冻结、尚无双方确认：需要后端确认项目鉴权、状态/版本/幂等键和 403/409 错误语义；需要消息岗确认通知查询、已读/处理、去重与降级字段。状态机及权限由后端权威校验，前端不直接决定状态、连接 RabbitMQ 或负责延期升级。

初始化提示词为 ROLE-frontend-BOOTSTRAP-v1，关联 `agents/frontend/TASK.md`；本次阶段提交提示词为 ROLE-frontend-M0-COMMIT-v1。实际 AI 岗位为 frontend；未发生用户亲自改码或接口审定。
