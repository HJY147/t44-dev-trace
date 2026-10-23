# 契约校验单UoW实现限定复审

## 1. 对象与基线

Agent-Role: reviewer；Prompt-Ref: ROLE-reviewer-READ-UOW-IMPLEMENTATION-v1。精确产品 **5dcb73cc10c38deb14fae68d33318b04d538fecf**，对照上轮4c20f32；设计3187bc6的RFC SHA256仍8cdfc9b29bf7ed36022ef54d6d3dac4df8b03f06228cdf22da9c939b827d818a。新独立worktree/分支codex/reviewer-read-uow起点46190e5a9631e0486755682537592d8aed3181e8，64个应用源字节对应5dcb。CI证据直接读取已提交22647b4eef87f7486293c64dc6d0b3d6809b1a53；当时root尚未合该证据节点的路径缺失已转告并获确认，不是产品失败。

## 2. 需求映射

仅validateContractPayload使用单自有UoW，保留每请求真实session/主体active/member/project鉴权、auth先于输入、只读Schema与字段版本、拒绝安全留痕。Frozen14项hash全匹配，原1.1业务/字段/错误/DDL未改；原4c20完整报告保留为历史，不把此次限定审核扩成其他模块新审。

## 3. 变更与责任边界

4c→5dcb的应用diff只有runtime.py，8增1删、净+7：导入now，execute开头只对该operation执行with→authenticate→validate→fresh now过期复核→原dispatch，退出with后原status/wire返回。其他17只读、login/logout/全部写/claim/锁/CAS/outbox/后台进程代码字节不变。两个开发测试文件原内容是新文件的完整prefix，仅追加18例，未删除/弱化既有断言。本岗不改产品、不新建脚本/编号、不接触独立私有内容或联系tester。

## 4. 接口与数据库兼容

内层候选schema_version=1.0.0、envelope.contract_version=1.1.0保持。无新增表、错误码、成员权限或状态边；成功不写task/audit/outbox/idem。真实MySQL三category专项通过请求/响应Schema、四类记录计数与task.version不变断言。Rows记录表序与Engine.connect计数证明成功路径4/5/5 SELECT、各1 acquire；COM_PING/初始化SET/提交/rollback/pool reset不属于该SELECT账本，不能由此宣称确定网络总往返或延迟改善。

## 5. 正确性与失败路径

- authenticate为默认RC普通查询、没有新增session/member S锁；每次新Call重新读数据库。四表各自语句快照，不是单一原子授权快照。已在途读允许完成的语义明确纳入设计；session/member撤销在旧读validate暂停期间真经HTTP提交，然后旧读200、新请求401/403，事件屏障证明先后，不靠sleep猜测。
- 初始缺身份/撤销/过期/非成员/服务身份+非法JSON分别保留401/403优先于输入；valid身份非法壳仍参数错误。fresh now取当前时间而非Call.clock，合法输入跨期拒绝且不dispatch，非法输入仍先报原参数错误；保证点是复核时，不声称发送瞬间永不跨期。
- with在整个try内，Rejected/PersistenceError/通用异常先完成UoW退出，再走原独立rejection。原CommitUncertain对只读仍映射DEPENDENCY_UNAVAILABLE，不伪说确定回滚；审计不可用仍503 AUDIT_UNAVAILABLE。四种注入故障组合明确验证closed0→enter1/closed1及不同Session，拒绝audit可持久或明确503；这是依赖/audit注入，不是真实数据库宕机。
- 已读API先完整接收body再进入Runtime，本地解析/Schema CPU期间连接继续占用，是尚需测量的代价；没有新增客户端网络await或对写路径绕过授权/锁。未来账号停用入口/扩大到其他GET仍须新设计与复审。

## 6. 核验与证据

本岗实际执行仅git/标准库hash、AST与JUnit/coverage解析、GitHub只读API；无产品导入/新业务测试/负载。原件与核验清单见agents/reviewer/evidence/read-uow-5dcb/verification.json。

| 证据 | 真实结论 |
|---|---|
| 专项改前原件 | HTTP11中4失败7通过；MySQL7中5失败2通过。9个失败是新优化/在途语义断言，不是发现9个旧业务缺陷 |
| 专项改后原件 | HTTP11和真实MySQL7均通过，四XML SHA匹配公开summary；逐条读新增断言、前后日志和原始XML，未重复运行 |
| CI run39970988113 | live API四job均success，run head严格5dcb；公开原JUnit **412/0失败/0错误/0跳过**，全43Python/0excluded；行2550/2872=88.7883%，分支611/776=78.7371%，不另设分支80%门槛 |
| CI checkout绑定 | 实GET合成checkout320272ca的tree=afe03f244d72c0faef4df028d7fdf30b9f7974ef，与本地5dcb整tree完全相同，不只凭head标签推定实际代码 |
| 原规模计数 | pinned原口径records/metrics/source-count-read-uow.json的e93dad1应用源与5dcb64文件相同，**5980行/超880**；本岗未重复cloc，未改分母 |

18专项属于412全套的一部分、标记组亦重叠，不能相加。旧394只绑定4c20，不代替本次412；本次CI也**不能覆盖独立v2固定的4c20 UI/hosted SUT**。独立v2未发布内容完全不读。此前正式400并发/600秒三组不通过仍保留，5dcb没有实测延迟收益。

## 7. 十项与门禁

| 项 | 判定 | 范围 |
|---|---|---|
| 身份与版本 | 通过（限定） | 他岗产品、64源码及CI整tree对照 |
| 需求范围 | 通过（限定） | 只读单operation，18例仅追加 |
| 接口 | 通过（限定） | Frozen14与候选/外壳版本未变 |
| 数据库兼容 | 通过（静态+既有专项） | 无DDL/写变更，真实MySQL专项原件已核 |
| 状态机 | 不适用此diff | 无状态机/业务写改动；不重审或放宽原要求 |
| 权限边界 | 通过（限定） | 新请求实时拒绝/在途读语义明确，无缓存 |
| 事务并发 | 通过（限定） | 无新锁，RC时序与with外审计证据一致 |
| 幂等故障 | 通过（限定） | 写/claim不变；注入错误映射与审计明确 |
| 证据真实性 | 通过（限定） | SHA/JUnit/coverage/live job和checkout tree吻合，无重跑虚报 |
| 整体可合并性 | **不通过** | 5980>5100、正式性能/新独立尚未闭环 |

## 8. 结论与复审条件

**5dcb的单UoW限定实现未发现新阻断，可进入协调后的短对照测量；整体产品继续不通过、不发布success/APPROVE、不合并main。** 少4条重复SELECT和一次连接获取已有功能性证据，延迟、400并发与有效代码规模不能据此宣称改善或达标。未来任何实现变化必须绑定新SHA及真实证据另审，不为后续待办占本轮槽位。
