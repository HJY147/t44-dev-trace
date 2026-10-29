# 实际提示词和操作者

ID: ROLE-database-MYSQL-GRAPH-20261025-v1。操作者为数据库 AI；不是用户本人写报告或用户亲自改码。

本次 root 实际指令：读取已公开 fresh MySQL baseline run40169575755，按真实同次请求分解 SQL、消费、codec、会话提交与获取的 inclusive/thread CPU；只称 Linux MySQL 诊断，勿追认旧云根因。与 BE 审查 START/UNBLOCK/REWORK 的项目 X→S 候选，保留其他 `_PROJECT_LOCK` X 和 session→idem→project→members→ordered target+pred X；先设计证明义务和真实 MySQL 小型并发开发测试，不改生产 Runtime、不碰 13306/旧云/独立私有 cases。

实际细化：用 request_id 精确 join，排除 warmup/profile；把 observer 安装晚导致 physical-connect 未观察和 post-dispose pool 快照明确标注。对共享项目锁不止比较 S/X 兼容，还检查图 writer、门前认证、门后 members 稳定性、REWORK capacity、FK 隐式锁及 optimizer 取锁顺序。并发驱动使用数据库 wait 边和 Event 明确测量门，不把 sleep/静态文本当安全证明。BE 负责真实 HTTP 业务 races，本岗负责低层锁探针，root 编排 fresh CI。

改进理由：把“调锁可能更快”变为范围受限且可否证的候选；将顺序请求成本定位和并发正确性分开。原失败、未知和有限样本局限保留，未伪造 prompt 迭代版本。
