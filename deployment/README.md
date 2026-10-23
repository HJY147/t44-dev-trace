# 单机运行与恢复

这些文件已实现部署配置；应用包、哈希依赖锁、迁移/账号 CLI、前端构建入口须由对应岗位交付后才能构建。本轮开发机没有 Docker，未构建镜像、启动 Compose、执行迁移/恢复或压测。规格建议不是性能保证。

## 前提和边界

- Linux 单机、Docker Engine 与支持 `up --wait` 的 Compose v2（建议至少2.24）；本项目没有集群或多地域。
- Python3.12 用于 `deployment/ops.py`；操作工具只依赖标准库。生产镜像固定多架构摘要，版本更新需重新验证和留痕。
- `backend/requirements.lock` 必须含哈希；运行包为 `backend/t44/`，DDL为 `specs/database/`。API `t44.api:app` 使用4个 worker；消息与调度分别为 `python -m t44.messaging`、`python -m t44.scheduling`。
- Vue3/TypeScript/Element Plus，Node24、pnpm11.25.0，`frontend/pnpm-lock.yaml`、`pnpm run build` 输出 `dist/`；Nginx同源转发 `/api/v1`，保留完整前缀，支持HTML5 history路由。
- 只有 `127.0.0.1:8080` 映射宿主。MySQL、RabbitMQ（包括管理面板）没有宿主端口；持久卷分别为 `<project>_mysql_data` 和 `<project>_rabbitmq_data`。不要增加公网数据库/队列端口。

## 配置、迁移与运行

在仓库根目录执行；以下是待部署主机上的操作说明，不是本轮执行结果：

```sh
python3 deployment/ops.py init-env
python3 deployment/ops.py config-check
python3 deployment/ops.py infra
python3 deployment/ops.py migrate --database t44
# 先确认DDL评审、明确目标、迁移CLI已实现；上条仅输出计划。
python3 deployment/ops.py migrate --database t44 --execute
python3 deployment/ops.py start
python3 deployment/ops.py status
```

`init-env` 独立随机生成256位数据库应用/管理员和队列凭据，以0600权限排他创建 `.env`，拒绝覆盖。模板 `deployment/.env.example` 只含占位值，不能当真实配置。不要贴出 `docker compose config` 完整结果；`config-check` 仅用 `--quiet`。`.env` 不提交。工具校验显式库名与配置相同，禁止系统库和重复/不安全值；不从 shell 读取任意覆盖值。Docker目标明确使用 `.env` 中 `T44_DOCKER_CONTEXT=default`，更改前核对 `docker context inspect <name>`，不让继承的 `DOCKER_HOST` 悄悄改变目标。

迁移是独立的显式步骤；应用容器不会自动修改DDL。未来入口 `python -m t44.cli migrate --database <name>` 尚未实现/核对退出码，部署包装会原样失败，不用占位成功。迁移前备份、确认版本和逐表评审，由数据库岗交付正式核对命令。只有迁移成功才能启动应用；直接跳过该步骤不是支持的操作流程。

应用健康检查在容器内部检查TCP/进程与数据库 `SELECT 1`，没有公开未鉴权探针。它不能证明业务状态机正确、队列消息已消费或扫描已续跑。API和调度不以RabbitMQ初始就绪作为启动条件，保留队列故障降级路径；消费者等待队列健康。独立调度只启动一份，仍需调度岗实现跨进程防重/重入控制，不能用Compose副本数替代幂等。

## 账号和会话

```sh
python3 deployment/ops.py account init-user --username manager --display-name '项目经理'
python3 deployment/ops.py account revoke-sessions --user-id 1
python3 deployment/ops.py account revoke-session --session-id 1
```

初始化要求交互终端，两次读取口令，经stdin送入后端CLI，不放在命令行参数或环境日志中。只包装后端的 `init-user --password-stdin`、`revoke-sessions`、`revoke-session`，不新增用户管理API。后端使用不透明会话摘要，不使用JWT密钥；这些CLI当前仍待实现和联调。

## 备份与隔离恢复

```sh
mkdir -m 700 backups
python3 deployment/ops.py backup --database t44 --output backups/t44-20261023.sql
python3 deployment/ops.py restore --database t44_recovery --project t44-restore-20261023 \
  --confirm-target t44-restore-20261023/t44_recovery --input backups/t44-20261023.sql
# 上条只检查清单/校验和并打印目标计划；确认后才创建隔离恢复实例：
python3 deployment/ops.py restore --database t44_recovery --project t44-restore-20261023 \
  --confirm-target t44-restore-20261023/t44_recovery --input backups/t44-20261023.sql --execute
```

备份只选配置库，先拒绝空库、非InnoDB表、视图、触发器、例程及事件，避免不一致或静默遗漏；当前18表设计采用InnoDB。使用 `mysqldump --single-transaction`，不输出DROP/建库/USE，也不在备份期间自动执行迁移；备份时禁止并行DDL。SQL与SHA256清单以0600排他创建，拒绝覆盖。备份含业务数据，须在另行确认的加密介质/受限位置保存；保留周期、异机副本、RPO/RTO未决定，本工具不声称已满足灾备。

恢复只接受本工具格式及匹配校验和，要求不同于业务库的显式目标库、新 `t44-restore-*` 项目和完整 `project/database` 确认；已存在目标卷一律拒绝。它仅启动全新隔离MySQL卷、确认目标空库并导入，随后核对表数，不替换运行中的数据库，不清理已有卷，不执行drop/reset。不要导入来源不明SQL。若导入失败，保留隔离实例调查，换新项目重新演练，不能清空已有目标。

表数不是完整恢复验证：数据库岗还须核对迁移版本、SHOW CREATE TABLE/约束、业务行数及事务/权限/消息幂等，应用岗执行恢复回归。当前mysqldump和恢复尚未运行。队列卷持久化不等于可移植备份；RabbitMQ消息的灾后重投依赖数据库outbox/消费去重和消息岗恢复契约，目前不能承诺队列恢复达标。备份/恢复工具不做业务“已回滚”状态迁移。

## 访问、日志与发布回退

本地或SSH隧道使用 `ssh -N -L 8080:127.0.0.1:8080 <host>`，浏览器访问本地8080。正式运行须由授权管理员在主机TLS终止代理配置可信证书、HTTPS和访问范围，再转发loopback8080；不要直接把HTTP登录口令暴露公网。域名/证书/租赁未执行，也未启用公网入口。TLS代理必须覆盖伪造追踪/转发头；API当前不信任任意proxy头。

访问日志只输出request_id、status、request_time、upstream_time，不记录Authorization、body、原始querystring、URI或口令；Nginx错误级别收敛为crit，避免默认请求错误日志夹带querystring。代理限2MiB，由API执行契约1MiB限制和拒绝审计；代理提前拒绝的更大请求返回冻结Error字段的JSON 413，`audit_id=null`，只用追踪ID关联日志，不伪称数据库已审计。

发布须记录已审查提交/镜像摘要、契约和迁移版本、备份位置、四视角风险、回退方案及拍板人。回退应用只能选择兼容当前数据库的旧镜像；不自动反向迁移、不删除任务、不从备份覆盖活库。需要数据恢复时先做上述隔离验证，再由授权人决定人工切换。`stop` 只停止容器、不删卷；本工具不提供 `down -v`。400并发/10分钟、P95和吞吐仍待真实独立发压验证。

## 配置依据

- [Compose健康依赖与独立步骤](https://docs.docker.com/compose/how-tos/startup-order/)
- [官方Compose规范](https://github.com/compose-spec/compose-spec)，离线schema及固定来源见 `deployment/vendor/`。
- [Docker Official Images](https://github.com/docker-library/official-images)，镜像tag及多架构摘要已在2026-10-23向官方registry核对；未拉取/构建。
