# CORE-FOUNDATION-v1 模块交接

状态：**纯领域基础代码存在并完成本岗自测；API、数据库、事务及集成未实现。** 此模块不冻结Q002的字段/HTTP取舍。内部Enum值是语义名，不代表对外数字或SQL存储编码。

## 输入、输出及调用责任

`t44.domain.decide(TaskPosition, Command, GuardContext) -> Decision` 不读取时钟、不执行I/O、不导入ORM、不改变传入对象。

- TaskPosition：内部七状态和阻塞前状态；构造时拒绝不一致阻塞来源。
- Command：九种不可变类型，包含本次原因、责任环节、依据、证据或不透明业务引用；没有target_state/set_state输入。
- GuardContext：服务端已加载的成员/角色/责任人、前驱状态、轮次与排期版本、当前评审和上线/回滚证明。实际证据内容、模板完整性、资源归属与引用必须由未来服务门面验证后注入，不能采信客户端布尔声明。具体纯实现TransitionContext拒绝非布尔标记、字符串角色及可变容器。
- Decision：原/目标TaskPosition、Action、原命令及Effect集合；未来事务门面负责CAS、apply、成功审计、outbox和幂等。当前模块不写入任务或自动执行发布/回滚。
- DomainViolation.code：仅内部语义；HTTP状态/对外错误码待用户取舍及规格冻结后由适配层映射。

start与submit_review仅负责人developer；评审由reviewer/manager，代码通过人不能是owner；待受理阻塞由manager，开发阻塞由负责人developer，评审/上线阻塞按该阶段角色。解除返回保存的原状态，客户端不能选择返回目标。依赖只在start、unblock返回develop、rework时检查；reject_review不暗加该限制。通过评审及交付会检查当前轮次/审核对象、证据、独立评审、当前排期与已审回滚预案。返工/评审退回只返回清批准及轮次效果，当前没有持久化计数修改。

已与数据库岗确认其MySQLSettings/create_mysql_engine、SqlAlchemyUnitOfWorkFactory、CommitUncertain为后续组合根注入边界；当前未导入或调用。没有数据库/消息/调度的业务门面，也未提供假API满足部署preflight。

## 真实依赖与运行命令

依赖来源为 `backend/pyproject.toml`，实际生成：

```text
uv pip compile backend/pyproject.toml --extra dev --python-version 3.12 --universal --generate-hashes --output-file backend/requirements.lock
uv pip install --python .venv/bin/python --require-hashes -r backend/requirements.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation ./backend
```

CPython3.12/macOS本机安装成功、pip check通过，本地项目wheel构建安装成功。相同锁版本对Linux x86_64/Python3.12的目标解析成功，但未执行Linux运行或MySQL认证。首次pip --require-hashes及Linux pip wheel下载因本机证书链失败，日志保留；未使用trusted-host、关闭TLS或修改全局证书。

[PyMySQL官方安装文档](https://pymysql.readthedocs.io/en/latest/user/installation.html)说明caching_sha2_password/sha256_password需要rsa额外依赖，因此声明PyMySQL[rsa]且锁含cryptography；安装后PyMySQL RSA后端实际导入成功，未连接数据库。口令依赖采用argon2-cffi，后续Token采用opaque方案；没有实现认证/会话，也没有JWT依赖。

部署岗确认测试标记contract/integration/fault由真实相应用例使用；本岗基础单元测试不贴这些标签。当前实际命令：

```text
.venv/bin/python -m ruff check backend/t44 backend/tests/backend
.venv/bin/python -m ruff format --check backend/t44 backend/tests/backend
PYTHONPATH=backend .venv/bin/python -m coverage run --branch --source=t44.domain -m pytest -c backend/pyproject.toml backend/tests/backend/domain --junitxml=agents/backend/core-domain-final.xml -ra
.venv/bin/python -m coverage json --pretty-print -o agents/backend/core-domain-coverage.json
.venv/bin/python -m coverage report -m
.venv/bin/python -m bandit -r backend/t44 -f json -o agents/backend/core-bandit.json
```

Ruff/格式/Bandit退出0，106个领域单元测试通过；仅t44.domain含分支覆盖约98%。不是HTTP契约测试、MySQL实库、模块联调、独立验收或全项目覆盖率达标。所有日志/JUnit/JSON位于agents/backend/core-*，原始SSL和初次import排序失败保留。
