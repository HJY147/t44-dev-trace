部署阶段 ROLE-deployment-TLS-DELIVERY-v1：工具实现已推送 3ccaa5da198e63e4f7161e131a131e246e8fa61a（codex/deployment-tls-delivery），固定产品 C=0dfb55c2191200d947c5423fd9ee74bb0812cc5a 未改。

产物：deployment/tls-delivery.py（SHA256 9d4e997b36208bd4950034df8a9d1b335ded4d4b162a5834f85d12d9ec7409fe）及 deployment/tls-delivery.md。单独私有 overlay 仅将 DB/MQ 换为 ECR 同 tag+digest，增加同原 nginx digest、edge-only 的私网8443 TLS gateway；根 CA key 不挂载，叶 key0600只读、严格 IP SAN/证书验证，客户端不可关闭验证。原 C web loopback/源码/env/daemon/DNS/安全组不改。

运维 wrapper 核 C/clean/root-owned0600.env/私有文件hash/本地unix context，显式双-f；每次仅 prepare/config/pull/infra/migrate(plan或显式execute)/seed/token/start(--no-build, pullnever)/status 一阶段，保留北京17:00减120秒绝对截止及阶段预算。初次token限定实际项目，拒绝运行中的scheduler，不包账号口令、自动续期、回滚、删卷或重试。失败raw只保存在主机私有0600回执。

验证仅本地19项必要边界guard、真实本地证书签名/到期/keypair和CI配置Ruff/compile/diffcheck。macOS LibreSSL缺目标OpenSSL3 -checkip，初次本地失败保留；guard仅该项改用stdlib解析实际SAN，chown mock，生产严格命令保持。没有Docker/Ubuntu握手/云或CI执行。额外TLS gateway开销须计入拓扑，既有六服务资源采样不含它。

接口交接：请root审核上述helper及同一overlay的阶段命令后，另核客户端CA传递、实际私网SG连通及完整C镜像构建回执；后端单独处理fixture-admin stdin。root最新实际UI转述完整v2 build北京15:13:15/601s/exit124，web已export而API依赖未完，保留原失败；不把FROM probe/本地guard写成完整构建、部署、正式性能或独立验收通过。20元/17:00不变，无实际部署动作。
