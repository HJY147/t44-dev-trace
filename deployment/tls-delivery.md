# 准确 C 的私网 TLS delivery（待审核/云执行）

工具与产品分开：`tls-delivery.py` 同时包含私有资源生成 helper 和单阶段运维 wrapper。产品固定 `0dfb55c2191200d947c5423fd9ee74bb0812cc5a`，不修改其 Dockerfiles、compose.yaml、.env、daemon/DNS/安全组。只供已授权的云助手 root 审查后逐阶段执行；没有 all、重试、回滚、删卷或凭据初始化操作。

原 C 的 web 继续仅 loopback:8080。新增相同 nginx tag+digest 的 ECR sidecar，非 root UID10001、只读、edge-only，唯一新绑定为**应用机 RFC1918 私网 IP:8443**。链路为 load HTTPS → 额外 TLS gateway → C web HTTP → 4worker API。额外 gateway/TLS 开销属于测量拓扑，原固定六服务资源采样不含它；不能称私网已通或性能已通过。443/公网不新增绑定，安全组不改。

生成一天有效的临时根 CA 和含准确 IP SAN 的 serverAuth 叶证书，检查签名、IP、余下有效期和公私钥匹配。根 CA key 留在主机 root 私有目录且**不挂载、不传输**；仅叶 key0600/UID10001只读挂载，配置/叶证0644受外层0700保护。TLS1.2/1.3；客户端须信任单独传递的 ca.crt 并核 IP SAN，禁止 verify=False/-k。代理不接管 C 的1MiB/413契约，不记录 access/query/body/Authorization。

## 审核后单阶段命令

前提：root 已核 helper SHA；精确 C 位于 `/opt/t44-c-0dfb55c`、tracked clean，root-owned .env0600已 init/config；Docker default context 必须本地 unix。`/run/t44-delivery` 必须 root-owned0700。root 在其中以0600保存 `app-private.env`，恰好一行 `T44_APP_PRIVATE_IPV4=<已核应用私网IPv4>`（占位不能直接运行），不公开其内容。新 runtime 目录名不得已存在。

每个云助手任务都独立使用完整前缀（示例 helper 路径由 root 审核 relay 后确定）：

```sh
python3 /run/t44-delivery/tls-delivery.py \
  --source-root /opt/t44-c-0dfb55c \
  --runtime /run/t44-delivery/tls-C-v1 \
  --private-env /run/t44-delivery/app-private.env prepare
```

将最后一个阶段名逐次替换，**看回执后另行决定下一步，不连成一键执行**：

| 阶段 | 明确行为 | 整阶段上限 |
|---|---|---|
| prepare | 排他新建私有CA/叶证/overlay/manifest | 120s |
| config-check | 原 C `-f` 加同一 private overlay `-f`，config --quiet | 30s |
| pull | 仅 mysql/rabbitmq/gateway 从 ECR 同 tag+digest拉取 | 300s |
| infra | 只启动DB/MQ，--no-build --pull never，等待健康 | 240s |
| migrate --database t44 | 仅plan；需另一次显式加 --execute 才运行原C迁移 | 180s |
| seed --database t44 | 原C seed-demo：40/6000/9000/15000 | 300s |
| token --project-id ID（可重复不同ID） | 原C credential-admin初次发行scheduler scope；运行中拒绝，已有token拒绝覆盖 | 120s |
| start | 原C api/consumer/scheduler/web+gateway，--no-build --pull never | 240s |
| status | compose ps，详情仅私有回执 | 30s |

表中 t44 必须替换为 .env 的显式项目库；ID只能来自实际已核项目，不由工具猜。账号/fixture-admin stdin交后端单独方案，本工具不包口令。token不支持轮换、不停止服务、不自动续期，仍受原C TTL3600约束；需要续期应另审同overlay的显式方案，不能偷用只含原compose的ops.py命令。

所有运维显式相同两份 `-f`；不依赖 COMPOSE_FILE，清除继承 COMPOSE_* 和远程DOCKER_HOST/CONTEXT。整阶段预算还含 preflight/证书检查，且硬拒绝超过 **2026-10-24 09:00 UTC（北京17:00）减120秒**；云助手外层应短于自动释放且略高于该阶段预算。不会延长20元预算/17:00释放。Docker CLI超时不代表daemon任务已停；失败仅标 state_requires_observation，raw stdout/stderr/超时退出信息保留runtime内0600，先只读核状态，不能盲重跑或声称清理成功。

原C API/web镜像须实际完整构建并核对回执才允许应用启动。root转述：v2 FROM-only probe已成功，但完整build北京15:13:15/601s/exit124；web已export，API仍依赖下载，**完整构建未成功**。本工具没有本机Docker/云执行；私网SG连通、实际TLS握手、DB迁移/seed/token/启动均待root真实执行，不把本地guard当部署通过。

旧checkpoint 3ccaa5d的19项guard保留为历史；其中以stdlib替代SAN检查未覆盖原x509 -checkip的退出语义，不能作为真实错SAN拒绝证据。审核P2发现该命令错SAN也可能ret0，现改为 `openssl verify -CAfile ca.crt -verify_ip IP -purpose sslserver server.crt`，移除单独checkip，keypair/expiry/manifest保持。补4项针对性合成guard通过（命令形状、非零传播、key不匹配、过期拒绝）。本机LibreSSL3.3.6不支持-verify_ip，真实正/错SAN两次命令均因选项不支持退出1，语义结果为null；**Ubuntu实际正/错SAN边界待root审查后核验**，不能说已通过。没有Docker/云握手或性能测试。

官方依据：[nginx TLS配置](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)、[OpenSSL证书扩展](https://docs.openssl.org/3.0/man1/openssl-req/)、[OpenSSL verify_ip验证选项](https://docs.openssl.org/3.0/man1/openssl-verification-options/)。
