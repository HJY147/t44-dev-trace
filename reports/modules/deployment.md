# deployment 初始化模块报告

> 前文为已归档的初始化/M0历史；当前运行配置与CI实现状态见末尾“RUNTIME-v1”追加段。应用/容器集成仍未完成。

## 任务与依据
- 阶段：团队建立与设计准备；`implementation_status` 为未实现。
- 依据：`AGENTS.md`、本岗任务、团队规范和报告模板，以及 `specs/sources/` 三份原始材料。
- 需求关联：FR-05 发布/回滚预案、FR-08 合并门禁，AC-07 重启续扫、AC-08 性能复现、AC-09 覆盖率与真实留痕。
- 本轮不实现业务、部署配置或流水线，不宣称联调、独立验收通过。

## 职责、范围与产物
- 后续负责打包、Docker Compose、运行环境、启停、备份恢复、发布/回滚说明及主干门禁运行机制。
- 长期代码目录：`deploy/`、`scripts/ops/`、`.github/workflows/`；本轮路径核查时均不存在。
- 当前实际产物：`agents/deployment/WORKLOG.md`、本报告、`records/handoffs/deployment.json`；本岗 `github-stage-comment.md` 与 `github-interface-question.md` 保存本轮 GitHub 留言正文。
- Vue 3 / TypeScript / Element Plus、FastAPI、MySQL、RabbitMQ、APScheduler、Compose 为既定基线；组件版本尚待责任岗和总协调冻结。
- 保持前后端分离的单体分层、单机数据库与中间件；本题不引入集群编排、多地域或服务拆分。

## 云环境状态与需求
- 已有应用建议为 8 核 16 GB / 80 GB SSD；压测机建议为 4 核 8 GB / 40 GB SSD。
- 两个规格都未采购、部署或压测；建议不保证 400 并发、10 分钟、P95 ≤ 270 ms 或吞吐 ≥ 1000 次/分钟达标。
- 云厂商、地域、操作系统/架构、域名/TLS、访问授权和费用上限未确认，不把建议记作用户决定。
- 待确认资源隔离和网络连通、镜像获取、持久卷/磁盘增长、日志容量、备份保存位置及凭据注入方式。
- 数据库与队列的外部开放策略尚待冻结；凭据只通过后续约定的安全配置提供，记录不含明文秘密。

## 模块输入、输出与错误边界
- 前端输入：构建命令、产物目录、API 基路径和路由模式；部署输出：构建/代理配置与可复现运行说明，均待实现。
- 后端输入：入口命令、监听端口、健康/就绪检查、配置键、依赖就绪条件、优雅退出及日志约定；部署输出：运行及故障定位步骤。
- 数据库输入：MySQL 版本、迁移入口/顺序、卷与备份范围、恢复核对方法、迁移可逆性；部署输出：备份/恢复执行和验证记录。
- 消息岗输入：RabbitMQ 版本、队列持久化要求、消费进程入口、确认/重投与停机顺序；部署输出：运行依赖及故障演练操作资料。
- 调度岗输入：进程拓扑、单实例约束、持久状态、启动续扫/重试及停机边界；部署输出：调度启动、重启及观测入口。
- 各岗需列出依赖不可用、启动失败、检查超时和恢复失败时的错误/退出码；健康路由与配置名目前没有冻结版本。
- 以上接口均为交接清单，不是已经达成的接口契约；不得凭此进入联调。

## 打包、运行、备份恢复与发布边界
- 后续按冻结版本固定依赖、构建产物和镜像，运行说明需关联提交号、镜像摘要、配置模板及启动/停止顺序。
- 数据与中间件持久化范围由责任岗确认；容器重建不能被当作数据可恢复证据。
- 备份一致性、保留周期、加密/访问权限、RPO/RTO 与恢复核对标准尚待确认；本轮没有备份文件或恢复演练。
- 发布前需评审数据、权限、外部依赖、观测四类风险及预案；是否执行回滚由授权拍板人决定并留痕。
- 应用版本回退、数据库恢复、业务“已回滚”状态是不同操作，不能用删任务或改库绕过服务端状态机。

## 合并门禁交接
- 静态检查、契约测试、覆盖率三项均是主干必需门禁；覆盖率至少 80%，全量用例要求按原始任务保留。
- 各责任岗提供真实检查命令、工作目录、依赖和报告路径；总协调冻结覆盖率分母、排除规则、工具版本及仓库保护配置。
- 门禁需关联被检查提交、命令、退出码、原始结果和放行依据；失败、缺项或未运行均不得记作通过。
- 初始化曾记“流水线与仓库保护尚未配置”，其中仓库保护当时未经 GitHub 实查；保留为历史说明，不代表当前状态。
- M0 已读取总协调保护响应并实时核对 main：必需 `reviewer/stage`、`strict=true`、`enforce_admins=true`；产品三项 CI 未实现，未设置通过或合并。
- 部署岗不拥有独立验收结论，也不联系或读取独立测试内部资料。

## 执行、证据与过程
- 本轮执行目录检查、材料读取及 Python 资料结构核对；三份文件存在、JSON 字段齐全且可解析；缺失职责目录的 `rg` 退出码 2 已留痕。
- 未运行模块自测、集成、独立验收、构建、部署、备份恢复或压测；没有性能原始数据或已运行命令可交付。
- 证据位置为本岗日志、报告及 JSON 交接单；所有后续操作命令需在实现阶段真实执行后追加。
- 实际提示词 `ROLE-deployment-BOOTSTRAP-v1` 关联 `agents/deployment/TASK.md` 和总协调实际派工消息，作用是限定本轮职责、写入及事实边界。
- 实际修改者为部署岗位 AI；未发生提示词演进、用户改码或人工幻觉纠正，不生成相关虚假条目。
- M0 文档问答和提交使用 `ROLE-deployment-M0-COMMIT-v1`；真实询问、回答与授权范围见本岗日志，接口问题仍未确认。

## 问题与交接
- 总协调需冻结云环境选择、组件版本、模块启动/持久化契约、备份恢复目标以及门禁范围，再派发实现任务。
- 文档岗可直接引用上述三个真实产物；必须表述为初始化设计资料，不能写作软件交付、云资源已购买或性能已达标。

## RUNTIME-v1：部署配置与真实门禁实现

- 实际派工和后续澄清：`agents/deployment/prompts/ROLE-deployment-RUNTIME-v1.md`；本轮覆盖初始化不能写代码的旧范围，仍不租云机、不付费、不合并或发审核成功。
- 独立worktree/分支为 `.agent-worktrees/deployment` / `codex/deployment-runtime`，基于 `4b3d6e5`；仅写本岗范围。
- 实现 `compose.yaml`：MySQL8.4、RabbitMQ、4worker API、独立消息/调度、Nginx+前端，数据库/队列持久卷，宿主只映射loopback8080。
- 镜像定义 `deployment/api.Dockerfile`、`web.Dockerfile` 及各自ignore，固定官方镜像摘要；`deployment/nginx/` 实现history fallback与保留/api/v1前缀。
- Nginx日志仅request_id/status/耗时；API执行契约1MiB限制，代理2MiB上限统一JSON413、audit_id=null，不声称已审计。无新增未鉴权HTTP健康接口。
- `deployment/ops.py` 实现私有随机凭据生成、显式目标校验、独立迁移/账号CLI包装、备份及新隔离项目恢复；无drop/reset/删卷功能。操作与TLS/SSH/发布回退说明见 `deployment/README.md`。
- 备份拒绝空库、非InnoDB及未支持的可编程对象，SQL和清单校验和排他保存；恢复拒绝活库/已有目标卷，默认只输出计划。实际备份/恢复尚未执行。
- `.github/workflows/product.yml` 实现static/contracts/coverage/frontend，真实MySQL/RabbitMQ服务、独立迁移、contract/integration/fault markers、原始日志/JUnit/逐文件覆盖率产物。
- `scripts/ci/` 明确拒绝缺应用、空测试、跳过占位及未计入的生产文件；每语言完整生产源码只强制行覆盖率80%，分支/函数报告不额外设门槛，仅前端.d.ts声明文件公开排除。
- 后端已确认未来API/模块/环境键和CLI设计，但尚未交付pyproject/哈希锁/应用/测试；迁移 `t44.cli migrate --database`、账号CLI及退出码仍待编码验证。
- 部署安全测试11项、CI守卫测试6项、官方Compose schema、Ruff、actionlint及diff检查通过；证据 `agents/deployment/runtime-validation/`。这些不是业务测试或独立验收。
- 本地产品static/contracts/coverage检查均因缺应用明确退出1；不能因配置检查通过宣称产品门禁已通过。无Docker，未拉镜像/构建/启动/跑Nginx/迁移/备份恢复/压测。
- 跨岗实际Issue评论：#7/6358650740、#3/6358651374、#4/6358651899、#2/6358904057；正文在本岗runtime-*comment.md，前端测试接口尚未确认。
- 当前主干保护仍由总协调维护；没有自行修改门禁保护、合并main或发布reviewer成功。云规格依旧不保证400并发/P95/吞吐达标。

### RUNTIME-v1 远程收尾

- 实现提交3857b2e55fcb7fe99b38fa2d85b086662b762f6c已push；草稿PR #15（base codex/team-bootstrap）已创建并attach，未合并。
- 首次远程run39912067161四job均因缺应用/测试/前端manifest失败；Compose/Nginx语法步骤及真实服务初始化成功，但未执行产品用例或覆盖率。精确回执与日志见runtime-validation/remote-initial*。
- api镜像加入authoritative specs/contracts白名单，不复制原始材料；实际路径、后端哈希锁和迁移/恢复仍待集成。结果Issue评论#7/6359033289，正文与PR正文均保存在本岗目录。

### RUNTIME-HANDOFF-v1 当前结论

- 运行配置最终修复6d713eb8fa5af419fe061c8c9b2061f2699472dc已push；原始日志gzip+SHA保真，阅读稿规范尾空白，diff检查通过；authoritative contracts COPY已核对，无sources。
- 最新总协调保护回执为root records/github/protection-v2-response.json：main五项必需检查已配置，strict/enforce_admins=true；旧“只有reviewer/stage”不代表当前。本岗未改保护/重跑/合并。
- 本次仅归档与回复CI真实pytest/JUnit/coverage命令；后端目前纯domain基础仍不是API完成。PR15保持草稿并已attach，首次run失败、缺应用和未本机构建的限制不变，待应用齐备后集成。

### INTEGRATION-v1 当前checkpoint

- web构建路径8e8、CI编号迁移7e4已发布；统一集成265d89bd的run39931640641四项真绿由总协调通知，不代替本岗Docker联调。
- 已接真实service-token CLI，scheduler目录只读/JSON0600、共享flock持久卷；操作包装先停scanner再轮换撤销/启动。凭据不入.env或公开输出。
- 新Docker application job/972 driver将真实build/up/迁移/seed/4worker/HTTP/SPA/413/凭据轮换/停写备份和隔离恢复；尚未执行，本机无Docker。
- 本地23 guard、配置/Ruff/actionlint通过；FE新CI命令真实通过whole-src行92.21%。原始证据在agents/deployment/integration-validation。
- tmp路径为tmp/backend、tmp/deployment/997_ops.py、tmp/ci/996_gates.py，新增971凭据guard/972独立Docker driver。无云部署、性能或独立验收结论。

### INTEGRATION-v1 真实运行结论

- 精确应用SHA `31f4dff935973162544951fe0660ce208edb7007`：Docker run39932723829 success；同SHA product39932723908/39932729585 static/contracts/coverage/frontend四job均success。原始证据在integration-validation/run-39932723829。
- 实际build两镜像、迁移/账号/seed2项目40任务、全Compose健康、API4worker、401/登录/项目任务HTTP、SPA history fallback和双层JSON413均通过。API超1MiB拒绝有audit_id；代理超2MiB为null。
- 真实0600/UID10001私密凭据只读挂载、跨容器flock拒绝第二scanner、受控轮换撤销旧session、2次持久扫描创建16条记录通过。Token未出公开输出，产物不含.env/私密JSON/数据库dump。
- 停写备份→新项目/隔离库恢复：19表行数/内容checksum一致；恢复迁移18业务表226列passed/already_applied，源重启HTTP可读。首次探针误计docker-init失败完整保留，修正识别而未降低4worker断言。
- 本机仍无Docker；这是托管Linux synthetic联调，无服务器租赁、公网TLS部署、队列异机灾备、生产RPO/RTO、性能或独立验收结论。

### INDEPENDENT-LINUX-HARNESS-v1 中性能力

- 新workflow acceptance-environment + deployment/acceptance提供下一轮tester运行条件；产品/harness精确双SHA分开，真实MySQL/Rabbit/API4worker/consumer/scanner/前端；只初建synthetic空项目，不写独立用例。
- 专用SELECT审计、服务stop/pause最长120秒租期/恢复、真实账号和调度scope CLI；凭据runner私有/mask、Token只读。
- tester本地私钥、冻结接收证书，CMS AES256-GCM/RSA-OAEP加密stdout/stderr/固定输出；公开artifact不含.env/凭据/coverage/私有用例，14天内tester解密审查后自行发布。
- dispatch当前因main无该workflow尚不可用，提供严格分支+request.json变更push入口；不改main保护。本岗953实际25guard/Ruff/actionlint通过；托管环境能力自检待执行，独立harness模式待tester冻结。
- 过程/静态证据acceptance-environment-validation；不替代既有Docker联调、独立fault验收或正式性能。

- 首次中性环境check39958418657失败：服务就绪及容器内审计通过、combined宿主client失败，具体异常原日志未记录；恢复=true，加密roundtrip未证明。原失败完整归档，不写作通过。
- 必要复核已获授权：分阶段安全诊断后仅对实际观测的internal-only不可达监听修验收override；提前创建合成归档输出。新增service-credential真实CLI短TTL/escalation:write/显式project，私密stdout或0600文件；能力自检不调用业务案例。953现37guard/Ruff/actionlint通过，revision2/product4c20f32待真实复核，harness仍未选择执行。

### 中性托管环境能力最终回执

- run39961035953 success：环境68b3bb2/product4c20f32分开，原始公共execution/crypto/控制事件/回执在acceptance-environment-validation/run-39961035953；首败39958418657保留。
- 观测MySQL2003/TCP111/无实际port绑定/internal-only后，只修验收override bridge，SQL/AMQP真连通；service bearer实际CLI/session scope/TTL300/0600通过；Rabbit stop/recover、finally恢复及合成CMS roundtrip通过。
- 953部署guard37项/Ruff/actionlint通过，不是tester用例。harness=false、profile=false；独立冻结入口/真实接收证书和独立fault/性能均待其后续执行，不重复本轮能力check。

### RECOVERY-MQ-v1 增量能力

- 新recover逐次JSON含独立ID/UTC/实际步骤exit/恢复服务，失败非零且结构化false；仅对实际暂停服务unpause，所有必须up --wait等全成功才true，保留部分恢复/失败证据，不扩大服务权限。
- SUT固定4c20f32，核实际MQ默认/无override；context新增主与quarantine拓扑、真实outbox wrapper字段、Pika属性/mandatory的中性元数据，不提供业务预期。
- 原953扩至49guard/Ruff/actionlint通过；revision3能力复核待远程执行，harness/profile不执行，旧回执保留。

- 增量revision3/run39974397951失败如实保留：stop恢复true；pause后unpause0但up --wait1(unhealthy)，逐次/最终回执false，MQ metadata/绑定通过。依真实诊断增加unpause后的60秒有界只读健康观测，原服务/动作范围不变；51guard/Ruff/actionlint通过，revision4固定4c待必要复核。

- revision4/run39975896833真实通过逐次stop/pause/最终JSON和MQ metadata/绑定。另补保留基础→应用依赖顺序的必要守卫，52项通过；最终实现revision5待同4c复核，旧各次原始回执分目录保留。

### RECOVERY-MQ-v1 最终交付

- 运行实现f118f9dd35bc2cde69affe235f5a499d03a396fc；SUT固定4c20f32；capability run39977039692真实success，stop/pause两次独立CLI JSON及final receipt均true、MQ实际元数据/绑定通过。52本岗guard/Ruff/actionlint通过。
- public execution/回执/原始gzip+SHA在recovery-receipt-validation/run-39977039692；首次f0失败、d8通过均保留。最终中性protocol为deployment/acceptance/README.md。
- 本次harness/profile=false，不接触独立内容、不评价其私密结果；无SSH。后续仅交接，不重跑或改实现。

- 中性白名单checkpoint 6b681dd73694bf18430f1bce4bdf00ffd1ae762e已push：deployment/acceptance/neutral-handoff/manifest.json列7文件和逐文件SHA256，manifest SHA256=362a9914e31bfdc3709a941ca9cb26b199a933f3ca8e1c959d0c9bde86c6f21b。仅成功元数据投影及协议/MQ/crypto；开发过程、失败详情与原始日志排除，供根单向转交。Issue7 https://github.com/HJY147/t44-dev-trace/issues/7#issuecomment-6368531787；PR15 https://github.com/HJY147/t44-dev-trace/pull/15#issuecomment-6368534363。本轮结束等待集成，无新增环境或测试运行。


### NATIVE-v1：项目内macOS原生设计checkpoint

- 本轮基点275dd3e/独立codex/deployment-native；实际派工ROLE-deployment-NATIVE-v1。本地开发运行设计deployment/native/README.md涵盖Rabbit/API/consumer/APScheduler、全loopback与独立生命周期，不替代Compose/云部署。
- 根完成OTP28.5.0.7项目prefix编译，固定官方Rabbit4.3.6/OTP下载SHA沿用根真实证据。12个版本主源SHA、一次无分布式crypto/ssl成功probe、实际双home结果见agents/deployment/native-validation。
- Cookie early-init两次真实失败均保留：先引用/UTF8词法，再auth未初始化的distribution_not_started。Darwin不读Linux XDG后备。下一阶段候选为独立-sname先初始化auth后项目args_file读取新随机Cookie，必须根准入真实认证；无secret argv/env、无HOME/官方源码修改。失败dump0600ignored不公开，broker不得复用probe Cookie。
- 演示候选新t44_native_demo(2项目40任务)/API18088/UI5178，AMQP25674/EPMD24369/dist35674/CLI45674–45683全loopback；未来v3/UI与perf必须另库/vhost，由根冻结。旧5173→18080、5175→18084、MySQL13306/PID7980及业务数据受保护。
- 设计列明最终精确SUT/锁/关键源SHA、私密账号与scope/TTL300/轮换、PID/PGID/UID/启动时间拥有权、逐次false失败回执、最小真实消息与60秒周期扫描验证。数据库权限/初始化由根协调，现未读取旧秘密或启动服务。
- 当前只完成设计及有限依赖probe；没有broker、API、consumer、scanner、业务库或UI运行结论，没有新独立/性能/云通过声明。原始提示词/工作日志/JSON交接已同步；根审查后再推进受控能力阶段。

- NATIVE stage1根7763402准入后，新增部署wrapper(runtime.py)与873合成守卫，15项/Ruff/diff通过；随机私密definitions、标准args-file Cookie setter、精确拥有权和逐次false回执已编码。现尚待一次自有全回环EPMD/Rabbit实际启动、CLI认证、监听/vhost/权限和安全停止验证；API等不在本阶段范围。


### NATIVE-v1 stage1 最终能力

- 精确运行实现7e94258898404eff8890aae9dc6d419f0cbdd468：run2真实start/inspect/正常stop均true，Rabbit11070/EPMD11063停后不存在；首次run1整体false/cleanuptrue原件保留。证据本岗native-validation/stage1-run1*、stage1-run2*。
- 标准args-file/-nocookie/-sname后项目0600新Cookie setter与CLI实际顺序/认证得到证明；单随机用户无guest/tags、单新vhost、四资源regex及真实密码后端认证通过。未做Pika业务消息。16个部署合成守卫/Ruff/diff通过。
- 实际Rabbit127.0.0.1:25674/35674；EPMD同时127.0.0.1及::1:24369，全回环，根接受相对原IPv4-only提案的技术澄清。nocookie短窗保守上界server0.275471s/CLI最大0.132151s，仅本地开发能力，不是生产安全批准。
- 42public/373private非秘密outputs+args对3Cookie/2AMQP口令literal扫描均0，范围/输出SHA已存；dump保持0600ignored不解析/上传。所有旧环境和MySQL不在操作目标。
- phase1归档后等待根最终SUT/schema/credentials；API/consumer/scanner/UI、正常消息/60秒真实扫描、独立/性能/云仍未验证。

### RUNTIME-METADATA-v1 只读观测能力

- 基点9fb24f1f0e173ef37d0cee8b14b080f190ca6d58；独立codex/deployment-runtime-metadata，新增metadata.py与control runtime-metadata，context仅声明不自动采集。六服务ID/标签校验、字段白名单，runner CPU/内存/cgroupv2、实际HostConfig/API数量/MySQL固定标量/Nginx投影/daemon关系；未知incomplete非零，无资源或业务修改。
- 953共75合成边界通过、Ruff通过，原件agents/deployment/runtime-metadata-validation；首lint失败保留。没有Docker/GHA/正式压测或实际资源观测结论；原七命令及cf685d7修复保留，不读取独立资料。协议deployment/acceptance/README.md新增只读快照段，限定cgroupv2/可见范围/当前Nginx文件等边界。

- 完整实现SHA b3ee0ac2f261b5f453af4a8c0fb5516ba06645d0已推送；Issue7 https://github.com/HJY147/t44-dev-trace/issues/7#issuecomment-6375611388实际发布并API读回一致，回执另档。中性转交仅运行协议/命令与版本；开发日志/测试原件不供独立岗，实际runner快照待调用方显式取得。


### NATIVE-APPLICATION-v1 phase2设计

- 根ec3e6b0准入有限新demo应用生命周期；设计application-design.md/实际prompt已归档。根给修后精确bc5aef9c62393134582affb7a690acb33ac2b833，92文件SHA/44Py20TSVue核对一致，旧42243从未起app。
- 已显式允许的t44_native_demo私密三JSON均0600，只CRUD用户、不读admin，不DDL/reset/seed；private环境需复制后改PYTHONPATH。原Vite18080 proxy/Node PATH缺失风险已识别，计划owner overlay与bundled Node，不改源/锁。
- controller/871、依赖安装与API4worker/consumer/60sscanner/UI、轮换/回收尚待实现/真实执行；本设计checkpoint不构成完整环境运行或独立/性能/云通过。

- controller现已实现，871为19项合成守卫通过、Ruff通过；原fixture/静态失败已保留。最终源92文件与私密输入/端口预检通过，拥有权/源/secret/坏输入/真实flock守卫有效；依赖准备和实际应用周期尚未执行，不将编码能力写成运行通过。

- 原checkpoint预检声明写早：真实controller首次计数错含部署/Vite文件而失败，未起服务；已按root业务目录口径修正，所有92文件照常核hash，新增守卫后20项/Ruff/真实预检通过，失败原件另存。

- phase2依赖attempt2锁hash/pipcheck/frozenfrontend/types/build全exit0；run1两真实completed/60.383994s、API4worker/UIproxy/TTL300/flock/Pika局部真，整体exit1/cleanupfalse（DTO解析错误、shutdown CLI超时）；原失败保持。只读16confirmed事件/26通知精确关联，后置全PID/端口gone另列。根准入一次freshcycle以既有eventIDs复核、补轮换与正常清理；当前未开始二轮，不宣称完整通过。

### NATIVE-APPLICATION-v1 phase2实际交付

- 实现0a6da88/SUTbc5a，新run2整体exit0/cycletrue/cleanuptrue；API4worker/consumer/UI5178proxy、新两扫描60.303070s、session4→5双项目TTL300轮换/新tick/锁/全回收及正常全停实际完成。源92SHA不变、新端口无监听、全部旧受保护监听baseline相同。
- 正常16confirmed事件/26通知发生于run1（当轮整体exit1/cleanupfalse仍保留），二轮既有ID/收件人和manager可读10通知复核，不声称二轮新publish。证据native-application-validation/run1-*、run2-capability.json、application-driver-run2.json；23项871+3受影响873/Ruff/diff通过。不含完整浏览器业务、独立、性能或云结论，当前所有自有服务停机。

- 证据封档e142470；新draft PR34 https://github.com/HJY147/t44-dev-trace/pull/34，Issue7/6375242146与已合并PR31/6375242564实际评论/PR34正文严格回读一致，PR31原历史正文逐字保留。现全停机并交根专项复核，不再运行cycle。

### NATIVE-CAPTURE-TIMEOUT-v1 设计待窄修

- 审核c688发现capture首次超时后child清理exit0会误返回成功，精确5ef/0a6原红与历史run2成功并列保留。先补现有设计，实际prompt另存；仅计划capture超时事实/实际返回码修复及五个合成边界，不启动服务、不读取私密输入，当前尚未修复。

- NATIVE-CAPTURE-TIMEOUT-01已窄修：首超时永久失败、保留actual childrc；清理未确认也留回执。原同例真实红→绿，五项capture合成/Ruff/diff通过，应用除capture AST/原守卫/runtime未变。未读凭据/起服务/跑cycle，历史0a6结果不移植，新代码等待根复审。

- 修复实现b238978（application SHA5ed6844d…），PR34当前代码/正文已更新；Issue7/6375565697、PR34/6375566016及正文精确回读，原公开P2失败保留。现封档待根复审，不声明审核放行或新代码cycle通过。

### API-PROCESS-METADATA-v1 识别边界窄修

- 原脚本的两种fake init-wrapper树均红（2 supervisors）；修为明确Python -m uvicorn模块前缀，保留strict==1。相同反例及多真实supervisor拒绝/原投影4相关项通过、Ruff通过；只API_SCRIPT变更，证明/红绿原件agents/deployment/api-process-metadata-validation。
- 仅合成边界，无真实进程/Docker/旧故障/压力重测。不是stage05实际原因结论；b3ee/H11 incomplete及封存正式结果不更改、不倒填。
- 实现SHA c0a5e89b2442da2a9149e1d37c2a424d52aff7c0已push；Issue7 https://github.com/HJY147/t44-dev-trace/issues/7#issuecomment-6376040442已GET读回一致。后续仅资料收尾，真实stage05原因及原资源incomplete仍未由本轮验证。

### NATIVE-BOUNDED-DEMO-v1设计

- 新codex/deployment-bounded-demo基于rootc1aff，先本人函数I/O/stop/rotation设计，原PR31/34和运行历史保持；只bc5新native专属库/端口。当前尚未实现/运行serve，工具/必要合成后等根压力窗口与新增范围专审；不回填独立/性能结论。

- bounded serve/stop工具已实现：固定bc5/current新run、显式时限、信号安全点、TTL300前轮换/新tick、owned runner请求及公共白名单；17项新范围合成/Ruff/CLIhelp通过。只工具阶段，无真实服务/360秒实跑，等待根压力窗口及新增范围专审；旧cycle/P2历史不移植。

- 新draftPR37/Issue7#6376409216真实发布并精确回读，工具实现4ef57b6；root明确先给DB比较窗口，本岗仍全未启动，待其清理完成和root另准入360秒。没有新增运行/正式性能结论。

### NATIVE-BOUNDED-DEMO-v1 唯一360秒实跑失败

- 根独占窗口准入后，4ef57b6真实360秒保持已就绪、两扫描60.292813秒、1次额外TTL300轮换/新tick；API/consumer/UI各1次，3自有服务会话全撤销，原16事件只复核无新publish。
- 原exit1/cleanupfalse：旧verify_stopped误把仍写终稿的serve runner自身计入。各应用/broker停止局部true、external driver已wait退出及全部PID/端口后置absence单列，不回写原成功。证据native-bounded-demo-validation/serve-run1-*。
- 全部旧监听baseline/92源hash保持；根已释放窗口，只封档后先设计窄修与合成红绿，不再运行360/长serve/HTTP/SQL；新范围审核仍pending。

- 原失败先封档f1598b9后，先行设计勘误仅选择四角色全部generation及APIchildren，runner外部wait单列；计划同例红绿/残留拒绝三类合成，当前尚未改工具或执行。

- self-runner窄修在先行设计c191后完成：仅verify_stopped四角色全部generation/APIchildren选择；原942同例红→新源同guard绿，3新方法含8真实角色代/5APIchildren残留拒绝，Ruff绿，无OS动作/服务/新360。capture/runtime不变，新SHA见self-runner-source-scope，等待新增范围专审。
- 旧snapshot7端口不包含v3的5177/18086，不是v3过去全时未变证据；只离线纠正，未来另准入须增补UID/start/argv hash基线，当前不补跑。

- 待审代码/evidence62ac2f327e7523ffed69a2bd9f98c87ba2372931（源084618…）已push；PR37新正文/当时head62ac/drafttrue及Issue7#6376718503、PR37#6376718790均GET逐字一致，末尾仅文档回执归档，最终head另报。原4ef唯一360false保留，新源未实跑；交根专项复核后本轮结束。

### NATIVE-BOUNDED-DEMO-v1 新唯一360复验全停

- 根在a7bad限定复审/1e9整合后另准入新fresh360，工具仍62ac/084618、应用bc5/92SHA、runtime未改。app_20261023_233238_345882真实exit0/summarytrue/cycletrue/cleanuptrue；原4ef360失败原件不改。
- 首两扫描60.324684s/额外TTL300轮换1次，API/consumer/UI各1/scanner3代/4worker，3服务凭据+ready会话全撤销；controller验证4条/DB同UTC8completed分口径，旧16/26只复核/新outbox0。
- 截止23:38:39.043824Z→实际停止请求23:38:39.044609Z→summary23:38:41.688950Z→外部wait实际exit0；12登记PID含workers/runner及Rabbit/EPMD全gone，新端口closed，九端口三个观察点身份全等（本次补充，非旧snapshot或全时监控证明）。
- 后置提取原bytes JSON失败exit1单独保留，窄转hex后只读提取exit0，无服务重跑。证据serve-retest-*；窗口已释放，4h尚未准入，独立/性能/云不推定。

- 三份公共验证脚本依root预留号移至tmp/deployment/864、863、862，字节/SHA不变，路径mapping说明只归档目录变化，原私密执行/失败/扫描原件保持，无重跑。

- 新360证据10182/目录迁移13cd均push；PR37正文/head13cd/drafttrue、Issue7新结果6376963887及迁移6376983708、PR37对应两评论共4条均GET逐字一致。最终仅文档回执封档，工具62ac/084618未变，当前全停；4h另待根准入。
