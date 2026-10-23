项目当前没有可直接使用的本机 Docker/Erlang 服务环境，本变更先交付可审查的项目内 macOS 原生运行设计。所有组件目录、Cookie、凭据与日志限定项目，AMQP/EPMD/distribution/CLI/API 全回环；演示使用新库与独立端口，旧预览与现有 MySQL 进程受保护。

设计涵盖独立 API/consumer/scanner 入口、精确 SUT/依赖 hash、scope/TTL300/轮换、进程拥有权和真实逐次启停回执，以及根准入后最小消息与60秒调度验证。当前 Cookie early-init 仍需受控分布式能力验证：无分布式 crypto/ssl probe 成功，两次 Cookie 失败的原始结果均保留；不会将静态设计写成服务启动通过。

验证：本岗 JSON/凭据未进入公开产物/diff 检查通过；无服务、数据库业务、UI、独立验收或性能运行。新文档与本岗记录不改变业务代码、契约、Compose、门禁或 main。后续服务启动等总协调对设计准入及最终 SUT 绑定。

Agent-Role: deployment
Prompt-Ref: ROLE-deployment-NATIVE-v1
Refs #7
