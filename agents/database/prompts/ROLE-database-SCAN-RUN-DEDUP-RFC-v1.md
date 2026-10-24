# ROLE-database-SCAN-RUN-DEDUP-RFC-v1

来源：总协调实际发给本实例的派工与后续纠正。操作者为 AI，不是用户亲自写代码；下文是实际消息原文，没有把本岗归纳版冒充原文。

## 初始派工原文

你承接固定数据库岗的下一阶段，先设计/RFC不改生产，在 /Users/yang/Desktop/nothing/软件开发大作业 独立codex/ worktree从当前集成HEAD。先读AGENTS和本岗既有handoff/审核报告。当前产品源4c20f32、源码5973按原cloc物理口径，超873；DB AST原型da6b2a4未准入，46pass1fail且不能净省行，别重跑/改口径/把业务移配置或压缩排版。选择真正重复的持久行为：persistence/scans.py ScanStore.start 与 scheduling/facade.py EscalationFacade._run 的scan_runs创建/唯一UUID/savepoint/不可变rulesnapshot校验。旧审核建议共享transaction-local start_run(g,...)预计净28–47，仅预估需自己精确算。请先提出最小内部接口、完整事务所有权和两调用方差异：ScanStore.start自有UoW、现总是insert后duplicate取row FOR UPDATE；API_run同调用方业务UoW，现先非锁定查、插入savepoint、duplicate再查，错误规则HTTP RULE_VERSION_CONFLICT；不能内部commit，不能丢原错误类型/未知run/规则hashversion检查，不能合并API业务副作用或触碰cursor/kill恢复。分别保留必要现有锁行为，证明不会扩大死锁/非法吞异常。数据库岗只应实现自己模块，scheduler facade由固定调度岗下一槽承接，先给双方能审的signature/未应用patch和真实净行数预算，root确认后安排调度岗消费，不为阶段使净行数假改善。现BE正在Runtime唯一contract-validation单UoW优化，别改BE服务/API；独立tester正在托管+本机UI，严禁读tmp/independent、969..960/951..942/940..931、任何未发布报告/截图/输出/私钥，不联系tester。无重负载/全量重测，若新增有意义测试脚本须向root领号（下一928；930已BE预留，929rootneutralhelper）。DDL14冻结件不变。需要本岗代码/接口/日志/模块报告/handoff/实发prompt与Issue4/Issue6沟通留痕，先交设计由root准入后才实施。

## 第一次后续消息原文

请本阶段以设计自然边界尽快交付：若保留两侧原语义的共享helper净收益不够或抽象复杂，明确否决/缩小，不必为已有28–47猜测凑预算。需要精确未应用patch/net以及由scheduler负责消费的接口提案，暂不改生产。新root生产已合并仅Runtime+7的5dcb73c，全量CI待结果，当前重新计数5980/超880；不要把5973当最新或把本岗预计收益记实际。交付后释放槽，root需要排文档汇总或新源review，再安排调度岗。

## 第二次后续消息原文

编号更正：928..919刚给独立v2继续私有适配，禁止读，下一空闲918；你本轮只设计/语法检查无需新增脚本。收净+1否决建议，不批准实施，尽快提交原件与本岗交接释放槽即可；不必等待调度岗，因为草案不省行且不应增加生产复杂度。用户需要的真实故障恢复能力待部署岗承接。

## 实际效果与限制

- 产物：agents/database/scan-run-rfc/design.md、candidate-v1.patch、candidate-v2.patch、逐文件 cloc 原件和 line-budget.json；本岗日志、报告、交接及 GitHub 评论另存。
- 明确了“只删 facade”与联合预算的差别：原314、候选315，净增1，实际生产节省0；总协调已否决实施。本轮没有为旧28–47估值改口径或压缩源排版。
- 发现保留现有 API 无额外 SELECT、scanner 回读持久行、不同锁和不同规则错误需要适配；草案的 API 查不到已有行内部异常类型也未等价，已公开列为不能直接投产，不继续扩展不合适抽象。
- 首次默认88列 scratch 格式化不适用本项目，已记录并改用现有100列配置，限定恢复原方法外内容；不是产品缺陷，也不计作学生识别幻觉。
- 这不是同一用户 prompt 的第六版，也不计为人工代码修改、人工测试或学生亲写研究报告。没有接触独立测试私有资料或派生新实例。
