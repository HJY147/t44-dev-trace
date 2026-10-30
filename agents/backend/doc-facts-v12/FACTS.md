# 后端v1.2技术事实包（用于需规/设计撰写）

所有backend/t44路径行号取exactsource90b提取树；SHA见SOURCE_SHA.PUBLIC.json。冻结入口records/spec-freezes/v1.2.json，规格源fec7a4e4877cc1dd3fceb8cd9f785db0f216b20d，父链1.1保留。产品source不改，两个性能候选只属未实现设计。独立测试/性能结论不能由源码推导。

## 七状态九动作与画图限制

稳定编码（OpenAPI枚举）：1 pending（需规称待受理）、2 developing、3 blocked、4 pending_review、5 pending_release、6 delivered、7 rolled_back；角色1 manager、2 developer、3 reviewer。domain/models.py18–28从冻结契约生成编码，不依赖Enum迭代次序。

state_machine.py15–23定义边：start 1→2；block {1,2,4,5}→3；unblock 3→blocked_from_state（1/2/4/5）；submit_review 2→4；approve_review 4→5；reject_review 4→2；deliver 5→6；rollback 6→7；rework 7→2。阻塞前位置是数据字段，不能画为统一回开发中。没有3直接交付/7直接交付/6直接开发边。

state_machine.py45–53/73–95阶段授权：start按开发阶段，需developer且owner本人；开发阶段block/unblock同样developer+owner；评审阶段reviewer或manager；其他阶段manager。approve_review另外不许owner自审；通过评审记录必须最新id/version、周期/制品吻合、reviewer不是owner、证据完整。拒审也必须有匹配的不通过评审记录，不只是点按钮。

D005/D006：tasks.py9–25、projects.py98–120、workflow.py118–120；新建/允许转派任务负责人须项目有效developer且在当前迭代capacity登记。转派仅state1或blocked_from_state1；不能在开发中直接转派。迭代人力改动必须保留状态1–5负责人；6/7可移出工时。projects.py45–71成员/开发角色使用保护仍包含1–5及7；移出工时不等于移除成员。7返工需先恢复developer及迭代工时、新计划、依赖全部已交付。

D008：workflow.py63–84仅在原批准id/version引用不吻合分支，先保留state5与manager守卫；若评估delivery_cycle/schedule_version也旧，报ASSESSMENT_BASELINE_MISMATCH，否则RELEASE_APPROVAL_REQUIRED。不能画成全局“先评估后权限”。已存在批准引用匹配则原domain顺序不变；更新评估后仍要独立评审和经理决定。domain/state_machine.py108–124还要求已通过的评估、创建人与复核人不同及review_evidence非空。回滚须原交付绑定的评估/预案版本；返工重置审核引用并递增delivery_cycle/review_cycle/schedule_version（153–177）。

## 主要函数与I/O、副作用

|函数|输入→输出|边界/副作用|
|---|---|---|
|domain.state_machine.decide(context: Transition)→Decision|可信任务/请求/角色/证据/依赖状态/评审/评估→values及record_type|纯函数；无DB、无网络、拒绝抛DomainViolation|
|services.workflow.Workflow.transitionTask(self,g,c)|事务gateway+Call→task/decision|读证明→版本与纯状态机→CAS，记录decision，更新计划/引用；审计/outbox/幂等完成由Runtime统一提交|
|Runtime.execute(self,call,validate,source='unknown')|请求上下文与校验器→(status,body,replay,original_request_id)|业务主事务、失败审计事务、CommitUncertain分类；不是所有失败都能声称未写|
|Runtime.prepare(self,call,validate)|Call→重放行或None|鉴权/校验后原独立claim事务；GET不claim|
|Runtime._claim(self,g,call)|作用域/键/请求SHA→row或None|唯一scope、新租约、重复hash比较、已完成重放、过期owner fencing|
|Scanner.run(self,run_id=None)|可选UUID→scan_run行|原规则快照、cutoff、持久cursor逐任务推进，可恢复|
|DeliveryWorker.cycle(self)|store/publisher/consumer→计数dict|租约领取→网络publish→confirm；消费成功DB提交后ACK|

Call定义common.py97–140，含operation/request_id/token/path/query/body/key、actor/project/membership/idem及clock；不得在文档示例写真实token。HTTP envelope并非Runtime裸四元组；成功重放仍可有动态请求Meta，不能画为整个HTTP逐字节回放。

## 请求时序/锁图

runtime.py45–52/140–195：当前身份及输入校验→独立claim事务[再次共享锁session→唯一scope FOR UPDATE→不存在则savepoint INSERT→GET→commit]。已COMPLETE检查同键同摘要后返回已完成业务结果，不重做业务写和成功audit；活动租约拒绝IN_PROGRESS；过期owner必须在锁后替换owner_token。

主事务runtime.py197–242：共享session锁（logout为update）→本claim row FOR UPDATE/owner fence→必要项目图锁（结构写update，start/unblock/rework share）→按user_id锁成员→依赖信息→任务id排序、逐唯一PK FOR UPDATE。不要将它画成全表锁或把多个PK改画成“并行锁”。随后Workflow做CAS→audit→outbox（非createEscalation业务项目写）→claim COMPLETE，同一事务提交；DB与MQ不在一个分布式原子事务内。

失败路径runtime.py85–117：独立失败audit，只有仍有claim所有权且status1等条件时才可完成错误重放；5xx/owner丢失/提交不明边界不能统称COMPLETE。CommitUncertain在299–301返回503，已提交可能性仍存在。

## Scanner与MQ

scheduling/scanner.py102–160：tick取同rule_hash、status1、heartbeat过120秒的恢复run（最多100），顺序run旧UUID，再创建新run。持久扫描是顺序keyset，不是每tick并行处理全库；run恢复保留started_at和规则快照。page读state1–5、id>cursor及规则推导planned_end截止；每候选在scope内通过原Runtime和幂等键执行，再checkpoint；空页才完成。token_provider每_scope及每_execute调用，__main__.py71–73的lambda实际读取私密token文件，不能称启动缓存凭据。

persistence/delivery.py22起：短事务claim含租约和SKIP LOCKED；messaging/worker.py33–81网络publish不持DB事务，persistent消息+publisher confirms后数据库confirm。broker.py121–148：验证消息→store.consume提交→ACK；丢ACK可重投，数据库去重防重复通知；DB故障NACK/requeue，格式/事件非法reject不重入。MQ不可用时升级事件走数据库fallback、普通事件retry（worker.py55–68），不能画成所有消息都丢弃或都同步HTTP失败。

## 可用伪代码及复杂度限定

依赖防环(tasks.py28–46)：构建项目邻接表；对K个新增predecessor各自新visited做迭代DFS，遇target拒绝。项目N节点/E边，最坏Python遍历O(K(N+E))，内存O(N+E)；不是一次共享visited的O(N+E)。DB读完整项目边额外O(E)结果传输，任务索引和查询计划另算。

转换校验：枚举/固定guard近似常数项；D个前驱要求all delivered的内存检查O(D)，取D行/排序锁O(D log D)加D次数据库往返，索引查找通常树高相关且受锁等待影响，不能称整个转换O(1)。CAS一行仍有索引查找、锁、日志和提交时延。

scan：C个候选、页大小P，至少ceil(C/P)+1页查询、C次checkpoint，scope内任务各有Runtime事务；总体工作随C和候选业务成本增长。keyset避免offset随页加深重复跳过，但若索引不覆盖state/planned_end/id，扫描行数可大于C；不能承诺总O(C) IO或每tick固定耗时。

MQ batch B：单轮至多B发布、B消费，计数循环O(B)，收件人R的通知写入另有O(R)；租约、unique索引、磁盘/网络/重试影响耗时，exactly-once业务效果来自DB约束和事务去重，不是MQ传输exactly-once。
