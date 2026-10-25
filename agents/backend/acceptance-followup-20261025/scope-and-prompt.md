# 后端公开验收缺陷跟进

- Agent-Role: backend; author/operator: AI.
- Prompt-Ref: ROLE-backend-ACCEPTANCE-FOLLOWUP-20261025-v1.
- Base: acae31a4b7e36bac38fa57367f4ca80066780273. Coordinator declares application bytes equal to C8 c8cea7e82805de5283ce67501769fa9a4efc1047; no historical source was opened to re-establish that declaration.
- Own branch/worktree: codex/backend-acceptance-followup-20261025 / .agent-worktrees/backend-acceptance-followup-20261025.

## 实际派工（总协调）

先按任务书、specs/requirements.md、specs/business-rules.md、specs/contracts/openapi.json核对D008发布基线/批准引用错误顺序；只接收已经公开的functional-v7-result.PUBLIC.json/md，不推测隐藏oracle。只读认证CLI并提出真实短TTL human token方案，不置备凭据、不改liveDB。自己分支提交报告、日志、交接并对接Issue #3；不得触碰主树、活动.runtime或冻结性能SUT；不得联系独立测试岗或读取817/829/818的其它文件、私钥、隐藏构造或Git历史。

后续总协调明确追加授权：只允许再读PUBLIC/F08-minimal-defect.PUBLIC.md/json；有效developer角色2无manager执行action7实际409 ASSESSMENT_BASELINE_MISMATCH，声明角色拒绝应403 ACTION_FORBIDDEN，后续不变/拒审计未测。按公开authority自行构造最小开发回归并修实际顺序问题；自己的worktree可轻量精选SQLite/纯领域测试，不跑full/性能；准确源码审核/CI及新独立运行由总协调另行组织。原F08 FAIL不得覆盖。

## 方案与边界

1. 新测试tmp/backend/contracts/816_acceptance_followup_20261025.py通过既有开发HTTP辅助函数创建自己的项目/任务/独立评审/评估/改期，不继承任何独立构造或ID。
2. 最小修复限定在action7已有评估、任务及请求评估版本已检查、且任务批准引用不匹配的原失败分支：先保留发布状态5与manager守卫，再应用D008基线/批准错误选择。批准引用匹配仍走原domain state/role/evidence/review顺序。
3. 不改变其它action、请求结构校验、认证/项目权限、幂等认领/重放、版本/CAS、事务、拒绝审计、契约或数据库结构。
4. 先保存原源码上回归红的原始日志/XML，再改产品；只运行新目标和原856必要邻接；没有MySQL、负载、全量CI或独立验收通过声明。
5. TTL方案只分析。当前CLI无human-token子命令；service-token不可替代human。最短合法设置60秒，未来由总协调在获准隔离campaign schema上以真实login发行并自然过期。

## 提示词改进理由

后续公开缺陷补充了可定位的最小角色/动作事实，才把最初的静态分析推进为开发复现和窄修；此前只有409错误码时没有推定产品缺陷。该追加说明是本次派工的范围收敛，不充作用户亲改、独立测试历史或新的六版提示词计数。
