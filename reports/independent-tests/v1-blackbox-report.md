独立黑盒验收 v1：未通过整体验收。已确认新版上线评估未使旧批准失效，三类正式性能入口均超过冻结270ms阈值；另有容量引用、参数拒绝、公开排期差异和错误码契约问题。缺环境与未授权项目没有按通过计算。

发布时刻：2026-10-23T11:00:47.756926+00:00。被测提交：`e8ceefe699951c52d4b01023b47a76b575d48c2a`。冻结摘要SHA256：`23a69bf10a50a63ebcef214d6ea9d088a0a0a9094d1b9fb821bb21ed4f996ffc`，冻结时刻：2026-10-23T09:43:09.678818+00:00。全部输入哈希再次校验，原6个冻结文件未改动。

功能只使用18081/t44_acceptance，性能只使用18082/t44_perf。未读取产品源码、开发测试、开发日志或其他测试实例资料；共享文件系统隔离是流程和上下文限制。测试只创建、查询和使用被授权专属库的数据。

冻结900条用例的严格结果：通过340，断言失败183，环境阻塞328，未执行49。失败数包含97个Retry-After解释歧义和15个状态矩阵引用/守卫顺序问题，不等于183个独立产品缺陷。38个接口成功用例均通过；完整错误留痕、人工补充条件和后续白盒条件不能由接口返回替代。

FR/AC下表是冻结用例的追踪与结果统计，同一用例可对应多项；它不是代码覆盖率或需求整体通过证明。

|范围|冻结数|通过|断言失败|环境阻塞|未执行|
|---|---:|---:|---:|---:|---:|
|FR-01|796|340|124|320|12|
|FR-02|3|0|0|0|3|
|FR-03|132|23|64|30|15|
|FR-04|198|98|28|68|4|
|FR-05|159|38|69|39|13|
|FR-06|115|12|65|17|21|
|FR-07|145|48|23|68|6|
|FR-08|7|0|0|0|7|
|AC-01|793|340|121|320|12|
|AC-02|3|0|0|0|3|
|AC-03|68|23|13|30|2|
|AC-04|197|98|27|68|4|
|AC-05|195|50|79|48|18|
|AC-06|40|12|12|12|4|
|AC-07|140|48|20|68|4|
|AC-08|3|0|3|0|0|
|AC-09|7|0|0|0|7|

已确认问题及最小复现如下。项目、任务和评估编号均是本实例创建的合成验收数据；所有写操作仍使用当前任务CAS版本。

**IAT-v1-01（high，confirmed_business_failure）：新评估文档未清空旧批准，旧评估仍可交付。** 冻结编号：SCN-assessment_history。

复现：通过公开合法流程到待上线；创建评估A并由另一评审者批准。 创建同一任务新评估B，保持pending。使用此时最新task.version，以A.id/A.version请求经理action=7交付。

预期：创建B清空旧批准；未经新评估评审不可交付。 实测：项目867/任务949：A81(version2,status2)，B82(version1,status1)；approved_assessment_id仍81，旧A交付HTTP200，GET state=6。

请求ID：`15221391-46fa-4862-aa11-c85a073c132c`。

证据：`961_semantics/961_assessment_repro.json` SHA256 `6b935c65239b5e63dcb15ae0874901d10f2ef346a906da2fdea5dacbf3ab2176`；`963_execution/963_supplement_http.jsonl` SHA256 `6752aa9c530177fe772aaef6bd9ec2d8a04d608df80c098c3854aef92b59f088`。

**IAT-v1-02（medium，confirmed_business_failure）：任务负责人未列入所选迭代容量仍被持久化。** 冻结编号：ERR-createTask-CAPACITY_REFERENCE_INVALID。

复现：同项目内存在两个有效developer。创建仅包含用户4容量的迭代767。 经理创建owner_id=2、iteration_id=767的有效任务。

预期：422 CAPACITY_REFERENCE_INVALID 实测：项目766返回201，任务840.owner_id=2；稍后GET再次确认owner2未出现在迭代capacity=[4]。

请求ID：`068d7171-dceb-4107-8185-962de6396260`。

证据：`963_execution/963_tool_corrections.jsonl` SHA256 `7f7be1263970fbb741877034baf9c130d117087916b64fabd3ff2bbf22e10186`；`961_semantics/961_final_confirmation.json` SHA256 `48b54e5bfc9ce5c30f3ad18024b144fead5509ba8268a4abebf8aebfa2d55090`。

**IAT-v1-03（medium，confirmed_contract_failure）：任务ID0返回AUDIT_UNAVAILABLE而非普通参数拒绝。** 冻结编号：ERR-getTask-PARAMETER_INVALID, ERR-listTaskDependencies-PARAMETER_INVALID, ERR-listTaskReviews-PARAMETER_INVALID, ERR-listReleaseAssessments-PARAMETER_INVALID, ERR-listTaskDecisions-PARAMETER_INVALID。

复现：以合法成员GET /projects/{本人项目}/tasks/0，随后GET同项目有效任务。

预期：422 PARAMETER_INVALID及可核验拒绝留痕 实测：初次/projects/300/tasks/0及复查/projects/766/tasks/0均503 AUDIT_UNAVAILABLE，audit_id=null，original_error_code=PARAMETER_INVALID；相邻有效GET200。未推断内部原因。

请求ID：`71fe3474-22ae-40f1-bebf-4ea18219a1fe`, `a7e0fb51-70e3-4e76-9a36-9b79458df289`。

证据：`963_execution/963_errors.jsonl` SHA256 `f99d54dc0009aef18a3d1589e37edb5b779bec901c9794ab1a12af68476df3de`；`961_semantics/961_final_confirmation.json` SHA256 `48b54e5bfc9ce5c30f3ad18024b144fead5509ba8268a4abebf8aebfa2d55090`。

**IAT-v1-04（medium，external_observability_gap）：公开审计不能重建完整排期前后差异。** 冻结编号：SCN-schedule_diff, SCN-boundary_values。

复现：经理更改任务排期及延期预案，按返回audit_id查询项目审计。 比较五项计划字段的旧值和新值；包含长度2000的延期预案边界。

预期：公开证据可比较完整原值/新值、版本和决定者。 实测：项目864审计7056的before/after仅暴露version，未包含完整计划。只认定外部可观测缺口，不宣称内部schedule_changes表缺失。

证据：`961_semantics/961_summary.json` SHA256 `eb2954db85a8248d6cec307e046feaca6c823efc1dd8af056122897efba3e043`；`963_execution/963_supplement_http.jsonl` SHA256 `6752aa9c530177fe772aaef6bd9ec2d8a04d608df80c098c3854aef92b59f088`。

**IAT-v1-05（medium，confirmed_error_code_contract_failure）：证据空数组与契约顶层错误的错误码偏离冻结分支。** 冻结编号：ERR-transitionTask-EVIDENCE_REQUIRED, ERR-createTaskReview-EVIDENCE_REQUIRED, ERR-createReleaseAssessment-EVIDENCE_REQUIRED, ERR-reviewReleaseAssessment-EVIDENCE_REQUIRED, ERR-handleNotification-EVIDENCE_REQUIRED, SHAPE-validateContractPayload-extra。

复现：在其他前置满足时，将必需evidence改为空数组。 对合法contract-validations顶层增加client_actor_id，候选payload本身保持合法。

预期：前者422 EVIDENCE_REQUIRED；后者422 PARAMETER_INVALID。 实测：前者422 PARAMETER_INVALID；后者422 CONTRACT_INVALID。请求均被拒绝；没有观察到缺证据通过或伪造主体生效。四种阻塞来源的空证据亦同。

请求ID：`297e99f5-a99e-4092-8808-d85283f4073e`。

证据：`963_execution/963_errors.jsonl` SHA256 `f99d54dc0009aef18a3d1589e37edb5b779bec901c9794ab1a12af68476df3de`；`963_execution/963_notifications.jsonl` SHA256 `38648bc6ce723a5433cc74386001e6964ff1c8eea48742a3644c94db397d6ccf`；`961_semantics/961_block_required_detail.json` SHA256 `e45a898e6fb8f4a980eea7c5f93def405d6ebe685ecd0108ff39c57389848cc8`。

**IAT-v1-06（high，measured_performance_failure_on_reported_topology）：三类入口完整400并发10分钟的P95均超过270ms。** 冻结编号：PERF-transition, PERF-contract, PERF-escalation。

复现：在报告所述专属库、同机部署和400个独立任务上，依次执行三批独立600秒稳态。 保持270ms、零稳态失败、至少10000主成功请求的冻结阈值。

预期：各批P95<=270ms、稳态失败0、>=1000主请求/分钟 实测：流转3035ms，契约1908ms，升级5506ms；稳态失败均0，吞吐均达标。三批均由原阈值产生exit99。

证据：`962_performance/962_transition_summary.json` SHA256 `2961da6f832e7ac01426701f894cf416070ca2e40c9d865b3431b473f5bd8bba`；`962_performance/962_contract_summary.json` SHA256 `657763d34f12753bcfe9e98cb5facdb15d3cdd2769337aa46a1152221757becd`；`962_performance/962_escalation_summary.json` SHA256 `0ad5a8a422c9ce24136ae8b0cd69319ae9e61423d0c2d4a47f51626a34beff49`。

正式性能使用k6v2.3.0，独立三批各400活动闭环VU、30秒预热、30秒稳态前排空、完整600秒稳态及最多30秒收尾。每VU串行请求，因此不声称每一瞬间都有400个并行套接字。完整客户端往返P95使用请求发起时的阶段标签；跨边界完成的在途请求保留，新发起的收尾请求排除。吞吐为600秒内主成功数除以10。

|入口|进程UTC开始—结束|主成功数|主请求/分钟|P95毫秒|稳态失败|重放|结论|
|---|---|---:|---:|---:|---:|---:|---|
|transition|2026-10-23T10:14:08.233604+00:00 — 2026-10-23T10:25:12Z|69101|6910.1|3035|0|0|超过270ms；exit99|
|contract|2026-10-23T10:29:19.565974+00:00 — 2026-10-23T10:40:21Z|233965|23396.5|1908|0|0|超过270ms；exit99|
|escalation|2026-10-23T10:41:27.296670+00:00 — 2026-10-23T10:52:33Z|34836|3483.6|5506|0|0|超过270ms；exit99|

初始数据经公开API检查为40项目、6000任务、9000DAG边、11400评审+3600决定。冻结准备脚本原拟14000+1000，实际使用中性预置11400+3600，15000总数一致但组成差异如实保留；通过公开API重新分配604条边，在不删除数据、不改变9000总数的前提下准备400个无依赖开发中任务。前批真实写入累积审计、幂等、排期与事件记录，批次间未清库。数据属于synthetic，不证明真实评审质量。

请求组成为：流转每轮GET后真实block/unblock；契约按登记/流转/评估1:1:1校验真实结构，断言未执行业务守卫；升级每轮GET、经理改期开启新schedule_version、服务身份创建全新事件，断言created=true。202只表示持久接受，未测得真实broker端到端延迟。

拓扑为同一台Mac桌面（arm64，8物理/逻辑CPU，24GiB，macOS27.0.1），API4worker、MySQL8.4.11、k6经loopback共用主机。协调安静窗口停了构建/图形渲染/浏览器负载，但WPS等桌面背景进程仍存在，未做主机或客户端/服务端隔离。仅抽样本实例k6进程资源，未独立采集API/DB进程CPU和RAM，不能把测得延迟归因于单一组件或外推云服务器容量。

|入口|k6资源样本数|最大RSS MiB|最大CPU（ps口径%）|
|---|---:|---:|---:|
|transition|46|2358.6|175.9|
|contract|58|3633.7|241.6|
|escalation|64|1983.0|122.7|

原始数据完整保留并逐行复算，P95与k6一致。transition预热有5658个409，且与此前因输出工作目录错误终止的技术预热共用warm命名空间；没有把整次运行称为零失败。正式transition稳态使用独立steady命名空间，原始稳态重放0/失败0。提前终止的技术预热不算10分钟结果。contract的首次解释器/脚本路径准备错误未形成正式负载，修正后才开始完整批次。工具适配保留原件、diff、原因与SHA，只修夹具提取、凭据格式、运行命名空间和输出路径，未改预期或性能阈值。

复现入口命令保存在各run证据；以下模板须使用原始冻结准备要求的同等专属环境与新鲜凭据/运行ID，工作目录为私有962_performance，不能将实际输出写到仓库其他路径。
```sh
IAT_COHORT=transition IAT_RUN_ID=<fresh-run-id> IAT_OUTPUT_PREFIX=962_transition PERF_FIXTURE=<private-fixture-absolute-path> NO_PROXY=127.0.0.1,localhost k6 run --out json=962_transition_raw.json 962_load_selected_v2.js
# 分别将cohort/output改为contract与escalation，各自完整600秒；原阈值保持。
```

三份原始指标证据：

- `962_performance/962_transition_raw.json`，589052169字节，SHA256 `f075cdce64fdf7bd9ae684a3315822e94769607308920faab689395694d55c96`。
- `962_performance/962_contract_raw.json`，1191321952字节，SHA256 `efd2bfe8d599745483db3a2db6dc3c8d4c256a44625727487f51e79e31c846cc`。
- `962_performance/962_escalation_raw.json`，418623223字节，SHA256 `a242dc331637a944d4726558abb851ae62450705f5586becd7edbf8699f724bb`。

补充语义观察与冻结900结果分开保存：24项中21通过、3失败，原始20项语义中18通过，后续分页、升级竞争与按实际Retry-After等待的登录限流通过；新评估批准失效、完整公开排期差异及阻塞必填错误码不符。50组不同键同版本竞争均观察到一次成功/一次VERSION_CONFLICT、版本仅增1和一个成功审计；同键竞争、历史快照重放、DAG环竞争、自审限制、角色转移、移除成员即拒绝、部分跨项目引用、UTC1000/9999微秒与只读契约已取得实际观察。它们没有自动将需要更多观察的完整冻结用例改为通过。

真实调度器创建20个超期任务的20个level2事件。停止并重启本实例自建的调度进程组，再观察78秒，仍为同一20事件且各计数1；最终有20责任人+20经理的fallback=true站内通知。实际通知时间约晚于事件143–145秒，早期90秒夹具观察期限不是业务承诺，不据此编造永久丢通知或异步SLA。最初仅停包装器导致锁冲突的“重启”未计入真正重启证据，后续进程组停启证据单独保留。

以下差异保留，暂不扩大为安全漏洞或成功非法流转：97个409的严格Retry-After断言与其“原请求处理中”的文字语义冲突；15个非法状态矩阵使用另一同项目任务的评审/评估，404引用拒绝先于预期409，未证明非法迁移被允许；SQL形态/非法/不存在项目选择器常先403，冻结分支期待400/404/422，而业务规则也写先项目权限。未观察到SQL执行、跨项目数据泄漏或伪造身份生效。初次限流补充任意等8秒的失败属于测试程序问题；后来按实际60秒Retry-After等待61秒已观察到正常401，未算产品缺陷。

尚缺能力及边界如下：

- 真实专属RabbitMQ及停启/重投/confirm/consume证据：MQ投递/重复消费/恢复后同事件不再提醒未验证；202仅代表持久接受。
- 受控服务UTC/故障点/请求持有/提交应答丢失/API进程生命周期：微秒升级边界、审计故障、提交不确定、活动租约恢复及原子性故障矩阵受阻。
- 按request_id查询全局/未鉴权安全留痕的脱敏只读能力：122个冻结分支的完整留痕观察受阻；API给出的audit_id不是独立持久性证明。
- 真实过期/禁用身份及特定不可公开构造的边界夹具：过期身份和不可达错误分支受阻，不猜测数据库ID。
- 真实续扫游标及部分完成进度可观测控制：完成一轮后的scheduler停启已观察，250任务处理中断恢复尚未验证。
- 中性前端URL/版本归属与可用浏览器入口：5个UI用例环境阻塞；HTTP验证不证明页面行为。
- 另阶段授权的源码/DDL/CI/覆盖与真实提交材料：10个LATER用例未执行，未证明80%覆盖、结构、有效代码行数或真实人类参与。

无真实RabbitMQ；AMQP指向本机拒绝端口，现有证据只证明实际fallback分支。未经故障点/应答丢失/活动请求持有控制，黑盒不能证明内部同一事务。项目审计可查询不代表未鉴权全局留痕已独立核验。未读取源码，因此未证明SQL参数化、Argon2id路径、DDL、门面/DI、80%代码覆盖、3500–5100有效代码行、真实CI门禁、AI过程材料或真实人类审批。

JSON伴随报告给出输入SHA、完整脱敏证据清单、FR/AC统计、各性能批命令和上述复现。完整900用例步骤及逐条私有结果继续保留在私有目录；父协调者只接收公开报告。修复后的复测应由新建无开发历史实例执行，此实例不接收开发解释。
