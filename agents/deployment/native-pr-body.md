新增项目内 macOS 原生 broker 生命周期工具，提供 prepare/start/inspect/stop 与失败清理，限定项目0700目录、0600随机Cookie/账号/单vhost、全回环和精确拥有权；端口占用拒绝启动，不停止外部进程。保留完整环境设计，应用阶段仍等根绑定最终SUT与新schema/凭据。

精确运行实现 `7e94258898404eff8890aae9dc6d419f0cbdd468` 的run2实际start/inspect/正常stop全部true：标准args_file/-nocookie/-sname文件Cookie setter和真实CLI认证、密码后端、无guest/无tags、资源regex与回环listener验证，最终Rabbit/EPMD进程均不存在。EPMD实际含127.0.0.1和::1回环；原IPv4-only设计差异与根接受澄清如实保留。仅本地开发能力，初始化nocookie短窗明确记录，不是生产安全批准。

验证：16个本岗873合成安全守卫、Ruff、diff通过；原run1 start=false/cleanup=true及更早有限probe失败原件/SHA保留，未放宽严格输出/权限/监听/拥有权门槛。证据位于本岗native-validation/stage1-run1*、stage1-run2*，公开metadata/私有非秘密输出secret literal匹配0，dump不打开/上传。

本阶段不含新schema、API、consumer、scanner、UI或Pika业务消息启动；无独立验收、正式性能或云部署结论。不改HOME、官方源码、业务代码、契约、Compose、门禁或main，旧预览和现有MySQL不在操作范围。

Agent-Role: deployment
Prompt-Ref: ROLE-deployment-NATIVE-v1
Refs #7
