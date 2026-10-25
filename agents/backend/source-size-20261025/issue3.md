Agent-Role: backend AI
Prompt-Ref: ROLE-backend-SIZE-v1 / ROLE-backend-SIZE-v2

已实现并提交内部 domain v2，产品 stagecommit `a07ad028a8efad4ecd186246bf2b7935c361b117`（父回退点 `a19af36`；从 integration e45a2b9 需连同父提交集成），本地分支 `codex/backend-domain-v2-size-20261025`。按总协调“集成后跑完整 CI”要求未 push；当前 codex/** push 会自动启动 product CI。

- 固定 cloc 2.10、原工具 SHA 完全相同，允许产品范围 2363 → 1987，实际净减 376，含全部新 helper 和已删 commands.py。初始 600–700 目标未达到；把本岗376仅从给定总6335相减是5959，仍不是全局5100达标或合并后计量。
- 根据总协调对内部实现取舍的明确授权，Command/Gate/Cycle/effect 桥接改为可信 persisted-row snapshots → 纯领域 task patch/decision_type → 原事务 CAS 门面。REST/OpenAPI/DDL、版本/资源归属、D008 state→manager→baseline、rollback preflight、人力规则、重放/拒审计/锁边界保留。旧内部接口迁移和故障修正已写设计/报告。
- 最终开发验证：170 域/边界/差分 pytest case + 143 原字节 HTTP/816 case 通过，0 failure/error/skip。原106中91行为 case实际走v2，15仅历史fixture构造器验证；另63真实v2类型安全 case、57120组精确 base 决策/错误优先级差分。16个事务/codec/CAS函数及原 DELIVER/ROLLBACK preflight 有窄 AST 相等证明，整次重构不宣称 AST 等价。
- 离线5动作、9×4000匹配桥接/决策 CPU比0.738–0.813，仅数微秒的无SQL/HTTP比较，不是正式270ms/400人/600秒/零错性能证明。
- 历史源码只作为 hash-pinned 测试 oracle。Git检测 commands.py 为历史fixture rename 不表示生产逻辑移出计数：阻断所有 tmp/历史oracle导入后，lazy真实app构造和纯START决策仍实跑成功；新规则与输入校验全部仍在计数产品目录。

证据：`agents/backend/source-size-20261025/report.md`、`prompt.md`；`tmp/811_backend_size/validation.json`、固定cloc/JUnit/静态/差分/微bench原样本及 `no-test-runtime-dependency.json`。WORKLOG/module/handoff已更新。a19af36 的 earlier139绿曾被过宽绑定，已明确更正：它仅是源码恢复点，不是最终全测绿候选；最终v2已修展示枚举/初始错误字典snapshot并重跑143绿。

待总协调：集成 DB/其他候选后固定口径全量计数、准确合并源完整CI/审核；MySQL锁、正式性能与独立验收均仍未证明。实际作者/执行者为后端AI，不记用户手改。
