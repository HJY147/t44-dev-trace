Agent-Role: backend
Prompt-Ref: ROLE-backend-APPLICATION-v1
Refs: #3 #4

阶段2实际新增：官方MySQL8.4.11＋HTTP测试1 passed（登录/成员/迭代/任务、并发CAS只有一成功、409独立审计、diff/outbox/幂等完成来源、提交评审），本岗HTTP合计27 passed＝26 SQLite＋1真实MySQL；Ruff/format/Bandit通过。没有清空dev库，夹具独立前缀，不影响演示数据。证据`application-mysql-http-first.log/xml`及`application-contract-stage2.log/xml`。

真实Uvicorn已在127.0.0.1:18080/api/v1运行，四项TCP HTTP＋MySQL烟测通过；本地演示三角色和项目/迭代/任务3已就绪，凭据仅ignored0600私密文件，未入Issue/日志/仓库。前端已收到路径并进行自身联调。HTTPX首测受本机环境代理影响，loopback改trust_env=False后复验，未关闭TLS。安全响应记录`application-network-smoke.json`。

按协调者安排本轮先交付服务和阶段代码，释放岗位并行时段给消息/调度。它们的facade尚缺时仍真实503，不虚构成功；CLI seed等待数据库owner。Rabbit、全t44覆盖率、全流程MySQL、性能、独立验收尚未执行，保持draft PR16，不宣称产品完成或审核成功。
