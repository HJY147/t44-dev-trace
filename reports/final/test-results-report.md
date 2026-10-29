# T44 测试结果报告

当前产品源90b734f65ce6ee9f5c217e885bc7ea4857e32b48，使用v1.2冻结。准确源开发CI后端797和前端89全绿；独立F05部分黑盒实测18 PASS、1 FAIL、11 UNEXECUTED，完整验收未成立。用户采用的主要核心口径为62文件5038行；辅助3文件780行（CLI147、迁移307、seed326）单列。原固定cloc全量65文件5818行，较5100超718，原require-range仍失败；用户采用核心口径不等老师批准全部文件排除。 本报告由AI文档岗整理，学生本人研究报告须学生自写。

## 1 测试范围和证据口径

| 层次 | 目的和对象 | 证据要求 |
| --- | --- | --- |
| 静态与冻结 | 类型、代码规则、API/DDL及源绑定 | 准确SHA、规则与退出码；不等运行验证 |
| 开发模块和差分 | schema、服务、状态、存储、消息、扫描、组件 | 原红、修订、旧断言和新边界分别保留 |
| 真实依赖与统一CI | MySQL/Rabbit、HTTP、覆盖率、镜像 | 原始报告与全源分母，不能把marker或重复run相加 |
| 独立验收 | 无开发上下文实例的功能、浏览器与交付检查 | 先冻结用例、后接源；只读明确发表报告 |
| 正式性能 | 三目标类、400并发、600秒和冻结判据 | 发压有效性、端到端计时、资源及恢复边界 |
| 文档QA | 四份新Word的版式 | 新渲染逐页PNG；不代替产品测试 |

本轮文档岗未运行产品或测试。本轮仅读取总协调明确开放的753 F05 PUBLIC报告与裁决；未读取其PRIVATE、代码、日志或原始输出，也未向其发送开发结论。

## 2 当前开发验证

### 2.1 后端和契约

后端候选17771e5及身份补充集成为356f299。188项新差分1.28秒、原305项SQLiteHTTP/错误顺序/领域29.92秒由责任岗报告通过，原测试零diff；两组用途不同且与更大全套存在交集，不能据此推算统一CI总数。Member20条页SELECT22→3、Dependency23→4，空页不多查；保留path/query、父task归属及原分页形状。

校验器仅冻结SPEC对象缓存原validator并保留原schema强引用、is身份检查及前100短路；动态schema保原构造和迟发引用异常。collections-red、error-cap-red、validation-red等原失败证据保留；fixture漏task_id和源码补丁失败是开发驱动问题，不当产品缺陷或学生幻觉。本机CPU ABBA与极端无效输入观察不能替代云吞吐/P95，source-aware生产者准备不当云READY。

公开入口为[后端实际prompt](../../agents/backend/final-20261029/prompt.md)、[原始资料](../../agents/backend/final-20261029/primary-sources.md)、[差分结果](../../agents/backend/final-20261029/differential-identity-green.xml)、[原HTTP结果](../../agents/backend/final-20261029/native-local.xml)及[本机观察](../../agents/backend/final-20261029/validator-benchmark.PUBLIC.json)。

### 2.2 数据库

DB候选b9d15aca，sqlglot30.25.0锁来源4c71161f，最终本地239 passed、27 integration deselected、24.10秒，其中18项新owner含196表达式及38416有序等价关系，不将表达式或关系当独立业务用例。原默认6000 seed golden、V2关系/时间、metadata双方言和消息/查询/池守卫包含其中。Ruff、format、Bandit通过且无规则豁免。

新通知测试观察三收件人去重后一次executemany、重复调用零新通知，缺收件人FK失败回滚整组及fallback状态。SQLGlot首次规范化1失败49通过、新owner首次4失败14通过及初始Bandit问题均保留；修复语法树遍历、夹具及SQL字面量后本地绿，不把早期失败删去。当地未执行真实MySQL，准确源统一CI仍须单独核其MySQL检查和覆盖率。

DB四件为[prompt](../../agents/database/final-20261029/prompt.md)、[报告](../../agents/database/final-20261029/report.md)、[核对](../../agents/database/final-20261029/verification.json)、[规模](../../agents/database/final-20261029/source-count.json)。DB单岗Actions40867341358四job成功由[公开元数据](../../records/ci/database-final-20261029.jobs.PUBLIC.json)记录，不冒当前整合源完整验收。

### 2.3 前端

前端产品9cf79dde仅合并七组相同CSS声明，254组selector/media声明序列相同；既有四测试文件89项、typecheck/build均exit0。831.48kB chunk警告保留，未调整阈值。模块夹具五屏宽六十状态无pageerror/横溢出，桌面/手机十二组PNG SHA相同，四图由前端AI实际看。API路径均由夹具拦截，不能称真实后端、云或独立浏览器通过。

完整computed-style探针含运行时ID和未规范化属性序列，严格比较失败，原件保留；其失败与独立PNG字节相同是两种证据，不能互相覆盖。夹具枚举错、内存受控中断130及PIL缺失属准备/工具过程。米咖主题、空串、0/null、错误解释、会话卸载及原38API/v1.2字节未改。

前端四件为[PLAN](../../agents/frontend/final-20261029/PLAN.md)、[REPORT](../../agents/frontend/final-20261029/REPORT.md)、[validation](../../agents/frontend/final-20261029/validation.json)、[artifact SHA](../../agents/frontend/final-20261029/artifact-sha256.json)。

### 2.4 整体CI和镜像

准确90b产品整体Actions40928297882四job成功，后端797项零失败错误跳过，行2485/2754=90.232389%，分支719/852=84.389671%，排除0。混合88.851913%不是行率。前端89项零失败pending/todo，行364/390=93.33%，分支821/932=88.09%。五份官方ZIP原件与128成员hash由审核岗核证，原始证据见records/ci/90b734f6-40928297882。

Docker Actions40928465279成功，实际checkout合成merge56217，产品路径字节与90b相同。其余三个上下文job原标skipped，不能说Docker全job零跳过；预期共享flock负例exit1保留。这是托管Linux合成Compose，不能替目标APP、独立或压力结果。
免费双镜像Actions40869531724真实成功，工具63c78169、产品源356f299；backend和web均新构建，部署岗后续已核官方artifact12894714534完整ZIP SHA及六原件，sourceprofile actual_loaded=false/root_approved=false，仍不能填已导入/部署。部署岗初始本地5项验证使用真实Git/generic函数、显式Docker seams及真实OpenSSL加密解密SHA相等，不等云、SQL、HTTP或正式负载；APP实际备份/恢复仍待执行。

## 3 独立验收和历史失败

| 历史阶段 | 当时公开结论 | 当前使用边界 |
| --- | --- | --- |
| v1 e8ceefe | 900场景340通过、183断言失败、328阻塞、49未执行；三组P95均失败 | 183不等183独立bug，不移植到90b源 |
| v2 4c20f32 | 多阶段子集执行，UI001/002/003及能力阻塞，整体不完整 | 开发修复与窄审不倒改原报告 |
| v3 bc5 | 功能25/26、浏览器6/6、粗故障4/4；白盒和交付物有限，整体NOT_ACCEPTED_INCOMPLETE | F08原优先级断言保留，后续D008是人的新规则选择 |
| v3 正式 | P95 9512.069/3086.148/8272.364ms，三组失败，组失败1021/0/2 | 两组采样不足、同次资源unknown不后补，原判定不撤回 |
| 原H1 | 六次prepare失败，正式NOT_RUN | 工具330/5预算不当教师门槛；不是正式性能失败测量 |
| H2 | 六次exit1，恢复5true1false；产品结论INCONCLUSIVE | 有效400并发测量未成立、不支持S1/S2排名 |
| 云839 C | 0完整正式组，短窗及预热502，稳态部分NOT_RUN | 触及case不等完成全部后置条件，旧C源码不当当前源 |

H2完整fixture和600秒调度不等有效并发，发压循环延迟/CPU、TIME_RANGE_INVALID过窄oracle、未收到ACK不等未提交及聚合漏成功分别保留。两次866正式目标请求0、P95未测得，不用前置改计划的P95替代升级；没有由文档岗复核私密raw。详情见[M10交接](M10-night-test-handoff.md)和[公开H2摘要](../acceptance/v4-performance-h2-public-summary.md)。新方法局限不倒推为旧v3判定失效。

历史理由true误同1、会话迟到403及部署capture超时等真实红绿链提供有限复审证据，只关闭对应准确源/缺陷，不能概括全球通过。历史33/35页Word的QA、旧真实运行及新源候选分别保留。

## 4 质量门禁和当前待验项

| 检查 | 当前可确认 | 尚需处理 |
| --- | --- | --- |
| 规格与兼容 | 当前v1.2、38API/130Schema、18表226列及DDL保持 | 按全错误和权限组合取得准确源执行证据 |
| 开发CI | 准确90b后端797/前端89全绿及全源分母已核 | 公开原件commit绑定，不能替独立功能和正式性能 |
| 独立功能与UI | 旧公开结果与失败保留 | F05原18/1/11保留，不能预填完整通过 |
| 正式性能 | 旧失败/H2不确定结果真实 | P06待回填：新准确源有效发压和三组完整正式结果 |
| 恢复和删除 | 镜像构建、受控备份工具本地验证 | 实际APP备份、下载解密、隔离恢复和root资源释放 |
| 规模 | cloc2.10 5818行65文件，较上限超718 | 范围仍失败，不改根/压行/搬实现充达标 |
| 研究和人工 | U001/U002原文、真实AI过程和本人材料来源 | 学生最终自写正文、人工12修改/3幻觉/5映射的真证据 |

[固定计数](../../records/metrics/final-candidate-20261029.PUBLIC.json)与[原要求复核](../../docs/reports/requirements-source-audit-20261028.md)分别说明项目口径和原文定义边界。模块239、188、305、89存在覆盖和依赖关系，不能相加冒充总场景；表达式/断言数、HTTP数和黑盒整例也不能互换。

## 5 可追溯性和交付说明

每项FR到模块/测试的正向关系及从模块回到FR的反向关系见[追踪矩阵](../../docs/reports/FINAL-20261029-traceability.json)。当前文档的来源hash、声明时点和待核字段另有清单，新增公开结果按准确源更新，不覆盖历史失败。AI发现、AI修复、测试驱动问题和人的实际选择分别归属。

四份新Word在FINAL90b独立私密目录导出，逐页PNG检查；性能待回填不提前声称通过。Word版式QA不代替产品验收，本稿没有学生研究正文。当前提交位置和各历史档案由[提交导航](submission-map.md)统一管理。

## 本轮证据边界

用户采用的主要核心口径为62文件5038行；辅助3文件780行（CLI147、迁移307、seed326）单列。原固定cloc全量65文件5818行，较5100超718，原require-range仍失败；用户采用核心口径不等老师批准全部文件排除。 原命令、逐文件结果和分组见[本轮计数](../../docs/reports/FINAL90b-source-count.json)及[原文件集分组](../../docs/reports/FINAL90b-core-runtime-groups.json)。

准确产品90b的官方Actions40928297882后端797、前端89零失败错误跳过；后端行2485/2754、分支719/852，前端行364/390。Docker40928465279实际checkout是PR合成merge56217f14568c7cd5ac6e83aaf4d890883e755ef9，已核产品文件字节与90b相同；不称纯90b checkout或正式验收。详见[官方CI核证](../reviews/90b734f6-ci-evidence.md)。

独立F05原18 PASS、1 FAIL、11 UNEXECUTED保留；唯一FAIL为非法page的400严格工具断言与冻结422类型校验优先级缺乏无歧义依据。实际422拒绝并持久审计，暂不确认为产品缺陷，也不改成PASS。38操作被观察不等全成功路径，479错误分支未观察，完整黑盒验收未成立。[明确发表报告](../../docs/reports/FINAL90b-public/753_F05_REPORT.PUBLIC.md)和[裁决](../../docs/reports/FINAL90b-public/753_F05_VERDICT.PUBLIC.json)为本轮独立资料入口。

P06正式性能结果待回填。当前没有可报告的新正式P95、吞吐或400并发达标结论；待具名PUBLIC报告到达后按准确源、有效发压、三类目标、完整稳态与恢复边界填写，旧失败保留。
