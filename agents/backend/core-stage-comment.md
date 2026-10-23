Agent-Role: backend
Prompt-Ref: ROLE-backend-CORE-FOUNDATION-v1
Refs: #3

真实基础实现位于 `codex/backend-core` 独立树：`backend/t44/domain/` 的七状态九种typed command、纯 `decide` 状态机与不可变Decision/Effect；角色、证据/轮次和依赖通过可信纯上下文注入，不导入ORM，不接收target_state，不执行I/O。依赖仅start、解除阻塞回develop、rework三处检查；评审失败不暗加依赖限制。

`backend/pyproject.toml` 和 `requirements.lock` 已真实建立：uv0.12.17 universal/Python3.12/hash编译68包，本机uv --require-hashes安装及项目wheel安装成功，pip check无破损；Linux x86_64/Python3.12另解析67包，与通用锁版本一致，但未执行Linux运行。PyMySQL[rsa]含cryptography，argon2-cffi与opaque方案，不加JWT。初次pip及Linux wheel下载因本机证书链失败，原日志保留，未关闭TLS或改全局证书。

实测：106个领域单元测试通过，Ruff检查/格式检查和Bandit退出0；仅t44.domain含分支覆盖约98%。JUnit由pytest内置输出，JSON为coverage CLI，已与deployment对齐，无额外pytest JSON插件。初次Ruff两处import排序失败及修复均保留。

本轮没有API路由、数据库连接/迁移、事务/CAS/幂等/图锁、成功/拒绝审计、MQ/调度实现，没有HTTP、MySQL实库、模块联调、独立验收或性能结论。Q002按本轮派工仍待用户取舍，契约/DDL复审结论由reviewer另发，本岗不宣称冻结或通过。边界、命令、原始证据及实际派工见 `agents/backend/core-interface-notes.md`、`core-*` 日志、`CORE-FOUNDATION-v1-prompt.md`，不是用户亲自改码。
