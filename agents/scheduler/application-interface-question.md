Agent-Role: scheduler
Prompt-Ref: ROLE-scheduler-APPLICATION-v1
Refs: #6

已读取12f7141中的services/common.Call、Runtime.execute与Business.finalize，不沿旧口头接口推测。本岗扫描计划构造Call(operation="createEscalation", request_id=UUID, token=读取0600文件, path={project_id,task_id}, body={expected_version,schedule_version,rule_version,scan_run_id}, key=稳定run/task/预期版本摘要)，以Runtime.execute(call,validate)走现有服务认证/idem/成功审计和原子快照；validate仅按冻结EscalationRequest/路径/幂等键验证。升级门面只在传入g写入，不自行commit；audit_id留给Business.finalize。

请后端确认该真实调用方式；Runtime已在API复验服务scope，扫描进程不会另造JWT。另已见当前cli.py有service-token --name/--project-id/--token-file命令，拟直接使用其0600凭据，不重复实现签发。请确认当前命令可作为部署初始化支持。DB扫描页跨项目，调度只处理已认证服务会话project_ids并在每次execute重新鉴权；不会让服务身份调用人类只读端点。
