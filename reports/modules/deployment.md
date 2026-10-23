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
