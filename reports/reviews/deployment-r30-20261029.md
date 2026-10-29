# R30 部署准备及预算 kind 修复限定审核

当前结论：原三提交的P1已在准确修复提交 `2ca7fd377b7ad0bbe37ff9aea8924825b092a803` 关闭，新增未决P1/P2均为0；可交root作为受限部署准备、安装与新环境预检候选。BOOT与SUT grant仍HOLD。以下保留首次阻断和失败，末段记录准确修复复审，不能将原a605本身改记通过。

## 1. 对象、基线与边界

AI reviewer；`ROLE-reviewer-DEPLOYMENT-R30-20261029-v1`。工作树从 root `7374b3637b06465d448fc2e81952ba18fc676315` 建立，分支 `codex/reviewer-deployment-r30`。仅审部署三笔准确提交：`61179fca68f09e89b3f8de24b910dd42ae78a434`、`a3a1fdc4acae861491190f3b97b310f0a41191e2`、`a6054ef5d5346be8ca55103f70012ee08d333bb8`。PR45含继承root差异，本报告不准许全量merge。

只读指定部署代码、准备记录和允许的官方artifact七成员；未读QA PRIVATE、REVIEW_R30_ONLY或其他runtime私件，未联系独立测试岗。未启动云、Docker/容器、业务服务或签发会话；临时目录仅在本岗 `tmp/758_deployment_review_r30`。没有改应用、compose、specs、部署实现或原测试。

## 2. 需求与真实准入范围

目标是准确产品 `0bffe0c535e5897890aebf30879fdd3839dc52d6` 的后端制品及新窗口准备；原生CI为40827655008，与新backend构建run40833943007分开。制品ready不产生BOOT或SUT grant。root后发说明仅拟一次35/40/45分钟有限窗口；QA core可动态接受0b只是root回传，QA新版adapter、真实seed/四角色/TTL接口仍待冻结，本岗未读其正文或把它记为已验收。

**原三提交首次结论：制品身份/离线暂存范围通过；新窗口可执行准备不通过，P1=1、P2=0；BOOT与业务grant保持HOLD。** 实质结论及复现已先发root，修复复审另列于末段，行政封档后补。

## 3. 代码与制品证明链

三笔提交对应用 `backend/t44`、`frontend/src`、`compose.yaml`、`specs` 差异为空；新增部署脚本/工作流及边界测试限定diff-check退出0。工作流permissions仅contents:read、checkout不保凭据、固定source与comparison Git对象，标准ubuntu-24.04构建backend-only。官方GitHub GET确认run40833943007的工具head为61179fca、completed/success；artifact12880320744的官方记录为94895161B、digest `69b2522744b9b9c4d0bd2845c04aeb4bb570c2efe1f8c84645950cc595fd7b4e`。本岗未读取允许目录外的原ZIP，ZIP完整下载相等依赖部署回执；本岗另独立核完允许七个解包对象及其pins。

bundle SHA256 `b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345`，source manifest `0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b`，config `8e3e2a9d1f2d4706072eb0502b041d3db49d32b7a2fc48ac6b39fc2162336845`均核实。62个context文件逐Git bytes/hash/mode相等；其中backend目录53件，包括51个backend/t44文件及pyproject/lock。47项旧frozen子集确为46同、schema.py一项已发表实现差异；这不等于整个产品只有schema变动，完整产品由准确0b和62件Git核约束。

本岗从原镜像11层按顺序离线回放 `/app/backend`、specs及deployment最终文件系统，完整60件bytes/hash/mode与Git及CI的`actual-runtime-files.json`相等。CI记录为uid10001；此处是独立归档回放及核对既有CI探针，并非本岗重新执行非root容器。

官方Python pin为`python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70`。本岗只读Docker Hub不可变index→linux/amd64 manifest→config，逐件重算digest，官方四个DiffID与新backend前四层严格相同；证据`official-python-prefix-final.json`。没有执行pull/build/load。

## 4. Docker29、source/run/time与预算接口

原image-proof.py SHA pin不变。实际归档含OCI manifest `6a3bab22a6bd36fd4d7be73b3cb745d9a0f73a504efab6c496701ceb6c96c762`及原config/layers。用真实归档构造本地inspect投影，classic config-ID及OCI descriptor→原config→有序layers两分支通过；改descriptor size、labels或layer顺序分别拒绝。没有退化为只比`.Id`、只信tag或跳过DiffID。实际Linux/Docker29 loaded/cache身份仍未执行，必须在真实APP上另取证。

新derive验证准确bundle/source/tool pins、未来30分钟至12小时UTC、新run格式，拒覆盖输出；生成prepare又要求派生run-id完全匹配。原硬截止、arm先于infra、操作锁、真实预算receipt+SHA与source/stop/mysql UUID复核结构仍存在；stop/status有独立出口。原20项测试验证部分边界，但遗漏了下述实际新旧接口失配。

**P1 R30-BUDGET-KIND-01：新phase不能进入预算门禁。** `r30-window.py:160`将generation kind替换为`r30-official-backend-production-entry-window-v1`，`:171-174`却携带原字节`mysql-budget.py`（305f9e...）。预算模块`v4/mysql-budget.py:87-88`的checked_binding只接受`exact-pinned-production-entry-generation-v4`。实际派生generation写入新kind，operation_lock/probe-budget/后续admit会拒绝，无法进入migrate/idle。

复现使用准确三提交工具实际derive、0700/0600的本岗无凭据最小binding，调用实际预算checked_binding，得到`V4_ONLY_NO_OLD_CAMPAIGN_ADOPTION`；证据`kind-probe.json`及final stdout。首次审核断言把生成文本误认`KIND`变量而非实际字面量，exit1原stderr保留；只改本岗断言后exit0，未改被审代码，预算拒绝两轮均已发生。

责任岗需给严格新kind的预算派生副本和新pin，并保留旧305f原件；除精确kind绑定外原预算/锁/receipt/测量语义应保持，仍拒旧kind混入。或提供等强的、经复核的代际绑定方案。不可删除checked_binding/实际预算门禁绕过。复审须实际执行新phase binding→operation_lock/预算入口的离线正反例，而非仅比较预算文件hash或AST。

## 5. 镜像件数与实际运行资源

| 范围 | 实际含义与影响 |
| --- | --- |
| 新运输制品 | APP只收1个新backend镜像；七个ZIP成员是文件，不是七个容器。LOAD不接收backend镜像 |
| APP idle | 6常驻容器：mysql、rabbitmq、api、consumer、web、tls-gateway。infra先启2件，idle再启4件 |
| scheduler | 默认未启；获得明确项目scope/token后另启，常驻变7件。未启时不具备scheduler运行覆盖 |
| 实际镜像种类 | 上述常驻只用backend/mysql/rabbitmq/web/nginx共5种；api/consumer/scheduler复用backend。六旧cache role还核python/node，它们不是APP常驻容器 |
| 一次性操作 | migrate/admin/credential-admin最多串行1个操作容器，运行时可能临时+1；这些operations配置未设mem_limit，预算不能当允许多个并行运维操作或内存总量保证 |
| API进程 | P方案1个api容器配置64 workers；不是64镜像或64容器，更不证明8CPU吞吐能力 |
| 数据库 | P API池上界320，加consumer15、scheduler15、串行operation15、health4、observer1、预算probe1及安全余13，合计384。必须实际max_connections及运行峰值观测，配置384不是观测384 |
| 内存 | P常驻六件mem_limit之和约25.5GiB，scheduler后约26.5GiB，仅配置上限；另有host/collector/临时operation，不证明实际内存或可用余量 |
| LOAD | 计划仅PUBLIC工具/新中性材料、已核官方Python工具环境；新版QA/driver adapter未定，实际容器/进程/线程数量和资源预算不能先认定 |

consumer在idle已经启动，真实MQ到达时会消费/写库，不能称无后台影响。scheduler是否启动会改变扫描/升级路径；两项都必须进入新中性运行绑定及资源记录，不能由镜像包数推导并发能力。F/P不并行是runbook计划，需要真实执行中保持。

## 6. 执行、失败与证据

本岗离线重放owner原13+7项，共20 tests OK/零failure/error，临时写入重定向本岗758；只适配ROOT/PACKAGE/`__file__`读写位置，原断言未改。另独立完成62Git/60层回放、classic/OCI两正例和三身份变异拒绝。调用链封锁全部非Git subprocess，不会意外执行Docker。该脚本最终JSON和完整stdout已写；其final process status因并行工具封装解析不支持的artifact endpoint失败而未取得，`commands.json`明确exit_code=null，不伪记shell exit0。20项原始unittest OK与本岗结果JSON单列保留，不与其他产品CI相加。

kind复现最终exit0确认的是**预期拒绝/阻断事实**，不代表部署通过。官方base第一次系统Python CA验证失败及certifi缺失均保留；改用既有venv certifi正常CA验证后exit0，未关闭TLS或保存/打印registry token。GitHub直接artifact endpoint被connector拒绝400，随后使用run-artifact-list工具取得官方记录；不是artifact/build失败。一次rg猜错v4/generation-template.py路径exit2，定位真实generation-f4后继续。完整命令、真实结果与原stderr在`tmp/758_deployment_review_r30`。

没有重跑产品CI、Linux loaded/cache、真实MySQL/RabbitMQ/HTTP、guest/systemd、SUT/性能或QA验收；没有把部署20绿照抄成预算绑定通过。

## 7. 门禁与封存方案

| 检查项 | 判定 |
| --- | --- |
| 1 身份/SHA | 通过限定三提交；不准PR45全量merge |
| 2 需求/范围 | 通过限定；产品、compose、specs不变 |
| 3 接口 | **不通过**：R30预算kind失配P1 |
| 4 DB兼容 | 无DDL变更；真实DB预算及加载未验证 |
| 5 状态/代际 | 新run/时间/拒覆盖静态通过；预算kind阻断 |
| 6 权限/数据 | pins、非root文件证据通过；无私件访问 |
| 7 并发/事务 | 原操作锁结构保持；新phase无法进入预算锁，真实资源未验证 |
| 8 幂等/故障 | 拒覆盖、归档身份变异拒绝通过；实际stop/重启未执行 |
| 9 证据真实性 | 准确source/build/归档/原失败分列；非独立验收 |
| 10 整体准入 | **BLOCKED_FOR_EXECUTABLE_WINDOW**；制品可离线暂存，BOOT/SUT grant HOLD |

runbook已区分guest owned stop与provider停费，计划35min停业务/封存，40min前分别发出两原机节省停机，45min前复核STOP、节省停机、auto-release=`-`及原盘保留；不down-v、不删除实例/盘。该计划合理但未执行。resource seal/LOAD完整尾部/最终摘要与provider后验缺失时应如实标缺，不能等证据拖过费用边界；外部cost-stop监督不能依赖SSH/guest成功。真实run/T0/WORKLOAD_STOP/COST_STOP、旧namespace隔离、原两机/盘/时钟和auto-release仍须root实际绑定/核实。

## 8. 结论与复审输入

当前三提交的制品可作离线暂存和修复候选；**不能作为已可执行的新窗口或BOOT授权依据**。P1仅由部署owner修复后交准确新SHA复审，本岗不代修。后续仍需真实Linux loaded/cache/源来源证明、新run/time/resource绑定、后端真实seed/四角色/TTL材料、QA新版adapter和完整工具/SUT限定准入。即使全部准备关闭，也仅准明确的一次有限观察，不继承旧grant、session或成绩，不改规模5880超780与既有性能未通过边界；本岗不发global reviewer/stage、不改main保护、不发APPROVE。

### 2ca7fd37 修复复审及当前判定

root随后提供准确 `2ca7fd377b7ad0bbe37ff9aea8924825b092a803`，在a605之上。唯一工具实现变化为r30-window.py预算派生及pin链；旧v4/mysql-budget.py、应用、compose、specs无改动，限定源码/说明diff-check0。本岗 `758_budget_fix_review.py` 逐字核adapter与该Git对象一致，实际derive：新预算完整字节等于旧305f仅替换唯一KIND字面量，新SHA为`9e98632fa1885bf4327b04a95daeba5cee4ad909b536e91ac8b11a1e58488a61`；adapter为`f2f850b5e17bd688811413ac535d36c0345ec9a0472df18dc22b65e758342896`。GEN.BUDGET_SHA/R30_ADAPTER_SHA、resource中GEN SHA、profile七件SHA均一致；窗口生成的GEN/resource实际SHA随真实run/time变化，未用fixture hash代替。

本岗最终探针exit0：准确derive→新0700 phase/0600真实binding→预算checked_binding接受→真实fcntl operation_lock进入→实际GEN operate(probe-budget)经预算绑定/锁后到mysql live哨兵。外层phase_binding和systemctl明确使用替身，live哨兵立即抛出，不执行Docker/SQL；旧v4 kind仍以原错误拒绝。这证明新kind入口已通，完整measure/admit/receipt/预算计算逻辑字节保持，**不证明实际MySQL测量或云admit通过**。原P1历史保留，状态改为`CLOSED_IN_EXACT_CODE_SCOPE`。owner新5项原红3FAIL/2ERROR与后绿、旧7回归仅核其报告，本岗不重跑或相加。初次定位误猜新增测试路径read128，后定位tmp760/test_budget_chain.py；非业务失败。

当前新增未决P1=0/P2=0；root可整合**原三commit加准确2ca7修复**作受限部署准备/安装与新环境预检候选，仍不可全量merge PR45、不可发global批准。必须从新fix重新派生全新profile，不使用a605旧profile。BOOT与SUT grant仍HOLD，直到root关闭实际绑定/QA/后端材料等前置。

### APP loaded raw proof 的实际出口

root实际操作顺序应是：先核新profile七件真实SHA（adapter f2f850、新budget9e9863及GEN/resource链），完整artifact七件/source/bundle原字节与pins；在获准Linux APP上执行runbook的`r30-window.py import-backend --package ... --manifest-sha256 b2db... --receipt <全新路径>`，成功后**在任何业务/infra动作前**按准确2ca7的`agents/deployment/preparation-r30/LOADED-PROOF-INTERFACE.md`完整Python命令调用`window.backend(package, bundle_hash)`，用排他`a.save`写全新的`loaded-runtime-proof.PUBLIC.json`，再按实际bytes计算整文件SHA。此命令会真实执行none/read-only/UID10001文件探针；本岗没有执行。

需回收的原件为：完整loaded PUBLIC JSON及其真实bytes/SHA、原source-manifest.json及`0c5b...`、原backend-bundle-manifest.json及`b2db...`。loaded JSON必须含实际image identity与runtime完整60行path/bytes/hash/mode、uid、package_origin、python_version、sys_executable、business_env_absent、canonical file-set hash和backend53件计数；identity区分actual descriptor-ID与config-ID。新中性adapter还需将这些真实原件/hash绑定本轮run/source/window/机器与资源profile，并核60行集合严格等于source manifest去掉两个Dockerfile，不能只信计数。

`import-backend`的minimal receipt只有`full_runtime_files=60`和identity等摘要，不含60行；CLI `verify-loaded`也只输出identity，二者均不能代替上述完整raw proof。CI60件、归档离线60件或预填成功也不能冒充APP loaded。该接口说明当前无真实proof文件/hash；如果新QA adapter要求其他字段，需先冻结对应schema而非开机后临时放宽。consumer已在idle、scheduler仅scope显式启动后第七件的真实角色说明应随新中性包保留。
