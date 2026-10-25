# F08 最小黑盒差异说明

原始结果仍为 **FAIL**，未重跑、未重判。绑定 source `c8cea7e82805de5283ce67501769fa9a4efc1047`。

涉及 `transitionTask`：`POST /api/v1/projects/{project_id}/tasks/{task_id}/transitions`。记录中的调用者为当前项目有效 developer（角色枚举2，无manager角色），请求 action7（deliver）。实际完整响应为 **409 / ASSESSMENT_BASELINE_MISMATCH**，未发生传输错误。

失败断言的性质是角色拒绝与上线评估基线拒绝的校验优先级。该操作声明 deliver 仅manager可执行，角色不满足应按403 ACTION_FORBIDDEN拒绝；D008仅调整原批准引用失败槽，不能覆盖更早角色、权限或状态检查。依据为：[OpenAPI transitionTask](/Users/yang/Desktop/nothing/软件开发大作业/specs/contracts/openapi.json:11884)、[requirements.md 第55行](/Users/yang/Desktop/nothing/软件开发大作业/specs/requirements.md:55)、[business-rules.md 第59行](/Users/yang/Desktop/nothing/软件开发大作业/specs/business-rules.md:59)，以及[任务书](/Users/yang/Desktop/nothing/软件开发大作业/T44_外包研发留痕_学生版任务书(1).docx)第4节FR-01与第5节安全/合规要求。

证据支持该次拒绝响应的错误码/校验顺序与指定权威契约存在差异。未查看实现，不能归因到具体模块或代码，也不表明发布成功或发生越权写入。F08在该断言停止，保留之前9项已完成后置条件；失败点之后的任务不变和拒绝审计未完成验证，不能由409推定。

完整用例构造、具体资源ID、payload版本、原始body/headers、私有源码和凭据均未公开。原始私有失败与加密证据保留。
