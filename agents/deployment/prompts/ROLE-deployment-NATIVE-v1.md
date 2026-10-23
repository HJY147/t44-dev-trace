# ROLE-deployment-NATIVE-v1

实际派工；不是建议版或用户亲自改码记录。操作者：部署岗 AI；范围决定者：总协调，依据其转达的用户 U019 夜间常规自治授权。

## 总协调原始派工原文

你是T44固定部署岗的新实例（不是独立测试、不得读其私密）。唯一工作目录 /Users/yang/Desktop/nothing/软件开发大作业 ，公开repo HJY147/t44-dev-trace。用户睡觉8h授权常规问题自己解决，截止2026-10-24 01:43UTC/09:43北京，大业务判断留待其返回。先读AGENTS/agents/deployment/TASK与现有部署门面/报告，自己worktree codex/deployment-native 以根当前2f56277之后最新根HEAD为基点，勿动根索引。任务先做项目内完整native RabbitMQ+API+consumer+APScheduler环境设计/能力准备，不租资源、不全局安装/改配置、不碰独立数据/端口/冻结契约/生产业务代码。当前Mac arm64 macOS27.0.1/8core/24GB，无Docker/brew/erl。root已仅依赖准备：records/decisions/local-mq-runtime-preparation.json已commit275dd3e；root明确可读的 records/validation/local-mq-official-downloads.json、local-erlang-build*.json和 .agent-worktrees/.runtime/native-mq-20261023/layout.json（私密目录中这组依赖文件不是独立资料）可读。官方OTP28.5.0.7 tarSHA ddf17db6...与Rabbit4.3.6 generic tarSHA aa0ff5de...已下载全摘要核GitHub官方release资产，解包在该ignored runtime；现root在编译Erlang attempt2，总预算1800s/make -j4。不要中止/并行重编译，由root通知编译/crypto probe结果。不是任何服务通过。请官方primary source核版本兼容与CLI，先提交部署设计：Rabbit loopback端口/节点/epmd与分布式口、所有cookie/数据/日志在项目内（不要重设HOME/home/CODEX_HOME，不能把secret放argv/log；研究Erlang明确cookie-file/-home等正确方式）；随机私密凭据/vhost隔离、进程拥有权/停止/启动回执、API消费者scanner依赖/来源/hash/角色scope TTL与轮换、最小正常消息/60秒调度验证和原失败保留。旧用户预览5173→18080(DBt44_demo_v11)、旧独立5175→18084、DB13306/PID7980绝不动；不替root提前启动业务负载。可建议先新t44_native_demo小2项目40任务做完整演示，未来独立v3需全新UI/perf库/vhost，由根冻结后提供中性环境，不能植入任何测试预期。当前根app：backendA7584/前端9560；UI002c56专审已过待整合、Issue28仍设计，故服务最终SUT必须等根绑定。自己的设计/脚本实现限deployment职责，先设计commit报告根准入后服务启动；若新验证test文件需873起根预留，现883–874新独立私密不可读。维护WORKLOG/module/handoff/实际prompt与Issue7/PR真实对话精确readback，阶段commit/push。root会核源再集成。不改main或宣布性能/独立/云通过。

## 后续明确范围

总协调：根attempt2已编译/安装成功（configure19:58:39→19:59:06、make19:59:06→19:59:43、install也exit0），root records/validation/local-erlang-build.json 和attempt1、official-downloads均可读；先前还没runtime probe。授权你设计阶段做一次有限非分布式依赖能力probe（必须 -nocookie 防默认home写入，noshell/crypto+ssl/OpenSSL info+init home参数验证，进程正常halt、无Rabbit/API/DB业务启动）；包括验证ERL_FLAGS=-home会不会与erl默认-home出现两值并回退XDG，不要假设只有一值。我读官方auth.erl 438同结论，无单独cookiefile参数。端口提案先保留；18086/5177未来v3未绑定，demo更宜独立新18088/5178便于不占独立预留，请设计中分开。待设计commit我准入broker启动。

总协调：可以，在当前授权能力探针范围补一次随机0600 cookie文件+-args_file前置eval的非分布式有限验证；只输出匹配布尔/home是否保持/无分布式，不输出cookie字面量/完整env，保存actual argv/文件hash/退出码。同步核server与CLI真正使用的启动参数/boot先后、-nocookie与前置eval实际覆盖两者，而非只依据通用init文档推定；服务启动仍等设计提交准入。若适用，该标准args_file+file read方案比deprecated env路径更便于版本化，记录真实取舍，不改官方源码/用户HOME。

## 作用与产物

本派工将本地原生依赖、全loopback、Cookie与凭据、精确源、进程拥有权、逐次回执及独立资料边界写入同一个可审查范围；不记作同一用户提示词的多次演进。产物为 deployment/native/、本岗 native-validation/、工作日志、模块报告和结构化交接单；实际执行失败与后续修正分开保存，未授权服务不提前启动。
