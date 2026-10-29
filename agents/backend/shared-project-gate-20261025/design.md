# 有限共享项目门候选：设计先行

作者、设计执行者：后端 AI。阶段基线 d60b229c19eb5de979f5886ad6bc46ad68bf3d5c；产品 Runtime SHA-256 为 8802416ee003a464a8433eed80890a1c2069550ff4717ca5e07a10cf2b840b48，与公开 CI 40169575755 / 81c909ad753aee7179ee0c464349a07273092fc0 的 source_files 相同。本阶段不能以设计代替真实 MySQL 或独立验收。

## 诊断依据和候选范围

仅阅读 root 指定公开 mysql-before.json；不访问独立 829 或旧私有材料。该数据为 Linux / Python 3.12.15 / MySQL 顺序 TestClient，4 warmup、48 measured、4 单独 cProfile，共 56。各路径仅 12 个普通测量，不能用作 400 客户端、600 秒、270ms 门槛或旧云 502 原因。

响应 schema 校验限 parent_id=0 的 API span；所有 schema span 的总和还包括请求校验。API 和 DB 计时层次均 inclusive、彼此重叠，不相加。Runtime exclusive 包含实际 SQL 的执行成本，并不是纯 Python 业务成本。cProfile 自带开销，不能把 profile-only 的 TLS write CPU 当普通样本耗时或并发瓶颈。

只评估 Runtime.locked_scope 的一个 lock 参数：graph_lock 条件成立时，_PROJECT_LOCK 中操作仍 update；其余只可能是 transitionTask START、UNBLOCK、REWORK，改 share。所有原条件、读图、成员锁、目标/前驱任务 X 锁和执行顺序保持。所有其它 action 不新增项目门；UNBLOCK 从 PENDING 恢复也继续原先的图锁和前驱锁，避免混入第二项优化。

## 输入、输出和错误契约

- 输入不变：已由原 Runtime.prepare 验证并 claim 的 Call，真实 actor/session、项目、幂等 owner token、action/expected_version/证据等原契约；以及当前主 UoW 的原 Gateway。没有新 API、配置或缓存。
- 输出不变：locked_scope 成功仍返回 None，副作用仍仅原锁与 Call actor/project/membership 刷新；Business 返回的 Task/Decision、版本、审计、outbox、幂等保存和 API envelope 全保持。
- 错误不变：原 session/token、幂等 owner、项目归属/成员、task/version、领域状态/依赖/证据/角色/REWORK capacity 顺序。无新捕获、重试或错误映射。存储失败、COMMIT ACK 不明及拒绝独立审计走原分支。
- 不触碰三个认证点、两主流程 UoW、拒绝事务、SQL 参数/数量、CAS、DDL、契约或冻结；不以减少认证/审计/校验来提升速度。

## 锁顺序与证明义务

认证 prepare 先按原流程读取，主事务锁序保持 session S → 已有 idem X → project S 或 X → 全 project_members 按 user_id S → 原依赖边普通读 → target 与所有前驱的 tasks X（原 sorted ids、ORDER BY id）→ 原 children/audit/outbox/idem 写。MySQL 配置仍 READ COMMITTED，门后全 members 的锁定及 active/role 再检查不得删。

| 竞争 | 候选保持依据 | 必需实证 |
|---|---|---|
| 不同 START/UNBLOCK/REWORK | project S 可兼容；只有任务/前驱集合互不相交才应并行 | 两物理连接门后都到达且未提前释放；不能仅凭线程启动判并行 |
| dependency/create/member/iteration/assignment writer | _PROJECT_LOCK project X 与任何 reader S 排斥；reader 不升级项目锁 | 真实 writer 未获门时不能读/写图；等待关系或受控门事实 |
| 前驱 ROLLBACK | ROLLBACK 仍锁其 target X；reader 仍锁前驱 X，等后 RC 读应见新状态 | reader 后到拒 DEPENDENCIES_UNSATISFIED；reader 先到可先线性化成功，不能宣称永久禁止未来回滚 |
| capacity / owner 变更 vs REWORK | 原 writer 项目 X；REWORK 项目 S 和 members S 保护 owner/capacity 读直到提交 | writer 先提交后 reader 看到新安排并按原码拒绝；reader 先获门时 writer 等待 |
| project member 撤权 | writer X；门后成员锁定重查，不信门前普通读取 | 持 project X 的撤权先提交后 reader 拒 PROJECT_ACCESS_DENIED/ACTION_FORBIDDEN 原优先；无业务成功副作用 |
| 同 target 同版本 | target X 与原 CAS；不同幂等 key | 恰一成功，一 VERSION_CONFLICT；成功审计/outbox/idem 和拒绝独立审计真实核对 |

SQL ORDER BY 与 sorted ids 不单独证明 InnoDB 实际取行锁顺序。项目 X 原先遮住的任务集合交叉争用现在可出现；DB 岗负责实际 EXPLAIN、锁清单、共享前驱、反向 id 交叉集合并发测试。若出现新死锁、非业务 5xx、意外升级或不能验证的锁序，不准入生产候选；不得用自动重试掩盖。已有无环图不等于任意锁集合无交叉。

FK 对 project/task 的隐式 S 必须与显式 S/已持 task X 兼容；不得忽略 audit/outbox/decisions 等实际成功写路径。如果后续代码出现 project X 升级，本候选需重新设计，不可自动扩大 S 范围。

## 分工与执行准入

1. 本岗先归档这轮公开数据的 SHA、准确环境、分层 CPU/墙时及限制；提交设计、真实 prompt。
2. DB 岗只改自身 tmp/833 驱动，真实生产 locked_scope、真实 authenticate、独立连接、session/idem/门/成员/任务顺序；审 EXPLAIN、S/S、S/X、交叉前驱锁，不写 Runtime。
3. 本岗新增 tmp/834 的 HTTP 开发并发驱动，使用 root fresh CI 的独立命名库和合成账号，不读旧云/env/token。HTTP pause 仅诊断进程临时封装 Business.dispatch（已获锁后）或 Runtime.prepare 返回（claim 后、主门前）；不替换鉴权、事务、状态机、错误和 CAS。
4. 稳定事件屏障、限时 join、真实响应/版本/审计/幂等/事件核对；超时按失败保留，不靠 sleep 成功。原 SQL 账本、领域/合同邻接回归另以必要范围运行，不能把低层锁测试称 HTTP 全验收。
5. 将设计和 DB 结论交 root/限定审核明确准入后，才修改一处生产 lock 参数。root 负责 fresh CI 组合的一次实际 MySQL 运行；本岗不运行未知本地 MySQL，不触发另一个 workflow，不开云。

## 规模与未达标边界

当前公开产品规模 6316（上限 5100，超 1216）仍失败；本阶段未运行 cloc。诊断、测试、报告新行不能冒作产品精简。拟生产表达式预计可能因排版增加行数，必须以原固定 cloc/同文件集合实际测量，不报预估为实得。现有 global ref 原型不优先合入，也不借其 SQLite 大列表改善宣称本候选收益。

当前状态：设计草案，生产未改，真实并发测试未运行，root/审核准入 PENDING。原 78bb/E/raw 和清理阶段证据均保留。
