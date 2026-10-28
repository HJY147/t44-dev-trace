# v4新源/窗口、连接预算与只读诊断设计

输入待root提供：最终整合且完整CI核验的40位source SHA、未来绝对UTC停止时间、后续真实source package/build binding/实际镜像与CA完整SHA。当前fee/2b79仅本地工具fixture候选，不是下一轮已冻结发布源；不填a12或旧窗口。旧factory/派生器/07:30/08:15/10:30 phase和结果一字不改。新代码仅deployment/cloud-reuse/v4/，输出只写全新独占路径。

root最初要求prepare/arm前查询同一专属MySQL，与原prepare要求全新空namespace、arm后infra才创建MySQL的顺序矛盾。root已明确撤回该先后约束：prepare只准备文件/计划、不准入业务；arm只定时保护；infra只MySQL/RabbitMQ；之后probe-budget只读真实专属MySQL；migrate/idle/API/consumer/web/scheduler-token/start/rotate前必须凭该回执重新验证同一CID/实际启动身份/镜像/namespace/数据库及当前@@max_connections。旧资料不回写，不新增无timer保护的bootstrap。stop/status即使预算失败仍可执行。

v4仍使用已审原四模板及完整Git源/依赖REST/DDL/frontend保护，通过原derive逻辑另派新profile；在新generation副本作精确前像patch，扩P workers到7/16/64，P显式--p-pool-size与--p-max-overflow必填，仅P api服务加入两个ENV。F固定4worker，全部其他角色保持原5/10且不得继承P的ENV。新helper SHA链、SOURCE/文件数/build/image/source package/CA/停止窗继续原强校验；不修改旧controller或降低source身份。实际Config.Env只在内存筛两容量键并逐角色比对，只输出容量/缺失默认，绝不输出其余环境。

允许容量组合：P7保原5/10；P16 A5/10或B15/0（总240）、C20/0（总320）；P64仅5/0（总320），64默认5/10即使大max也拒绝。固定保留64连接，分项consumer15+scheduler15+一个运维进程15+四个health探针4+一个持久observer1+余量14。运维migrate/admin/credential-admin必须单进程互斥，observer最多一个；不把原factory的two-operations口径偷换成已测事实。P16 A/B最大304，C与P64最大384；F4默认60+64=124。以上只是预算，必须与真实@@max_connections再比较，384仅配置先验。

最小可审接口（仅未来root操云）：
- 新derive-profile.py derive --repository ABS --source FULL40 --stop-utc ABS_Z --output NEWABS：输出新builder/generation/resource/receiver/mysql-budget与profile SHA。最终源/窗口缺失或过期拒绝；本次不生成发布profile。
- 新generation prepare沿用原全部source/image/namespace参数，增加必填P容量；arm/config/infra保持保护顺序。
- 新generation probe-budget --phase-dir NEW --binding-sha256 FULL64：仅真实MySQL只读查询，独占保存mysql-budget-receipt.PUBLIC.json；缺真实运行身份/错误DB/max不足不落通过回执。
- migrate/idle/scheduler-token/rotate/start：读取固定已核收据，再查当前同一MySQL和预算；同一互斥锁约束单个运维container。既有stop保卷，不以预算失败妨碍清理。
- 独立只读observer：与同phase实际MySQL CID/启动身份绑定，一个持久连接每个周期只SELECT @@max_connections、@@server_uuid、DATABASE、CONNECTION_ID及Connections/Threads_connected/Max_used_connections/Uptime/Threads_running；不reset任何status、不改全局/session参数/持久性/pre_ping/隔离/SQL/鉴权。输出只数值、连接自身1槽、增量与reset/missing标记，health/admin干扰单列为不能由总计精确归因，不能把Connections下降等同业务性能通过。需owned期限/固定FD/独占新文件，连接及错误文本凭据不输出。

本地验证用纯fixture和明确模拟Docker/MySQL结果，真实文件/O_EXCL/hash保护、组合预算/64默认拒绝、ENV不泄露、身份变化/过期/缺回执拒绝、仅计划阶段可无实测、stop不受闸影响、观察SQL只读及自身开销、原四模板SHA未变。不是云/真实MySQL验收；后续actual role ENV、真实server预算、资源采样及旧270/active400/600秒全部独立达标，代码规模不能靠机器解决。
