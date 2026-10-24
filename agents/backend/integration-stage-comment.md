Agent-Role: backend
Prompt-Ref: ROLE-backend-INTEGRATION-v1
Refs: #3 #4

完整组件已接入：API默认组装真实NotificationFacade/EscalationFacade，全部38操作通过53次真实TCP18080＋MySQL8.4.11调用及逐响应Schema验证（integration-38-http.json）。完整开发/评审/交付/回滚/返工、成员/迭代/排期/依赖/预案/审计/通知等有真实成功；内部升级HTTP返回已持久事件202，首次创建由真实scanner CLI验证，不把重放冒充新建。

真实进程链：scanner产生升级→Pika连接关闭端口真实失败→messaging CLI自动fallback→HTTP收件人读/处理→同事件晚到consume创建0、通知操作不挤占task.version。另实际CLI初始化只存Argon2id、撤销全部/单会话、撤销后同键重放先401、错库迁移拒绝。凭据未入仓库/Issue/日志。18080已安全更新本岗服务，独立18081未触碰。

初次全套312通过2失败3跳过，真实失败是seed读旧规则字段，由DB e06修；第二次314通过0失败3本机Rabbit未配置跳过。全t44行2391/2724=87.78%（含分支85.36%），没有omit。实际去重合并Schema解析/列表样板/重复上下文与SQL默认初始化，守卫保留；整体源码规模仍超限，不以少量去重声称达标。Ruff/Bandit通过，最初误报和原失败保留。

用户要求测试机械迁移tmp/999递减后，本岗已暂停所有测试文件编辑等待根SHA；以上验证保留旧命令/真实范围。当前仍不宣称Rabbit成功投递、CI全绿、最终规模、性能或独立验收通过；PR16保持draft，不self-approve。
