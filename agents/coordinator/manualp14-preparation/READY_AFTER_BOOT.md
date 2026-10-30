# p14 开机衔接：离线准备与现场事实分开

准确待复测产品为13acb43a804e717e7485091895378511fe3d9b76。完整CI797项通过、行覆盖90.27%，本地RC并发正确性通过；正式性能尚未测量，原p13 NP保留。代码、工具、镜像的准备不等于当前环境批准。

候选新QA为r30manualp14，material为r30materialresume08，maintenance为r30restoretransition08，workspace为/root/t44-final-20261031/QA753_NEXT_V52。开机后必须确认全部未存在、未消费；不覆盖旧前缀、不自动重试或继任。原隔离schema/campaign保留，不seed、不新建tasks、不重建库。

## 开机顺序

先由用户启动16核压力机并提供当前公网IP，64核应用机继续关闭。核原SSH hostkey/实际授权、CPU/内存、当前镜像4f3身份、公开收件公钥对应私钥仍在、实际磁盘空间与原始记录／备份／运输预算。只传本新PUBLIC工具包，使用qa-install/INSTALL_README.PUBLIC.md在全新W安装；旧W不重装、不复制旧private_tools、不读取旧私钥或结果。仅包中安装器在LOAD使用收件私钥。成功仅安装，不是发压。

LOAD的实际工具与预算通过后，再通知用户开启64核128GiB应用机并提供当前IP。应用机开着时只执行已准备步骤，不扩展诊断或对照实验。

## APP更新、物料和独立准入

1. 重新核真实七角色／原卷和schema／已应用索引／排他与旧controller状态。原资源、worker、线程、连接池、环境、网络、挂载、健康和重启策略与原私有快照完整比对，禁止用默认Compose覆盖。planner/locked-task-plan.py只读生成新镜像与rollback overlay；任何config/env/overlay漂移后重新计划。模板不构成批准。
2. 新镜像包位于主项目.submission-private/build-candidates/locked-task-13ac-20261031，manifest SHA414e3069bddc03adedea3671cb5de7c9382f46f9f44bb77799c5cc7112856bd7；四产物已本地核验。按image-import/README.md仅使用原字节verify/import/prove-loaded入口。12GiB空闲等原加载条件须现场满足。新receipt和producer observation sidecar须真实产生，root权限0600，不编造旧路径、时间或stat。
3. 按planner明确命令仅更新api/consumer/scheduler/web，no-deps/no-build/pull-never；不触mysql/rabbitmq/tls-gateway或卷。重观测升级后七角色，不能沿用硬钉旧七ID的resume脚本。
4. 使用backend/RUNBOOK.md和sequence/RUNBOOK.md。先核原400/800资格，必要时通过业务接口恢复；再发行全新会话与新source/bundle/import identity，原子轮换scheduler凭据，并等待rotation之后真正新开始且完整成功的扫描。绑定本次08物料原字节、退出证明、当前scheduler；严格900秒observer边界只约束观察进程，不关VM。失败保留前缀，不降低判据。
5. 冻结工具／模板保持原字节。现场可变输入放另一个私有runtime目录：将sequence目录原字节复制到此处，仅将其P09-existing-containers.PUBLIC.json换为现场真实核准七角色快照。MANIFEST所列脚本与backend pins继续逐项核验。不要覆写冻结kit中的false模板。将真实新nonce、authorization、账户、receipt/observation、CA等置于私有输入路径，禁止公开token。所有未取得事实保持false/空。
6. transport/cms_five_transport.py原字节封装全新five；旧90b packet只保历史来源，新13ac source/bundle/receipt和new identity重新建立。qa-protocol/SOURCE13AC_PROTOCOL.PUBLIC.md规定packet legacy81e与实际v5.2 core9cf是不同字段，不能互换。新profile/approval仅由独立岗核实际事实后签发，root不填写独立review=true。
7. 使用新ENTRY prepare产生default-false；独立复核真实会话、fixture、schema、资源、排他、五件及fresh scan后，才由独立岗使用qa-controls/ISSUE_ONCE_P14.py一次签发。旧PREPARE_REUSE/issuer/SEAL不装入新流程。保持400客户端／60秒预热／600秒稳态／P95≤270ms／逐分钟≥1000／零错误和原全部断言，不做额外AB或压盘。

## 结束、证据回收和用户手动停机

实际执行退出、所有producer及外部writer停止后，按qa-controls/CONTROLS.PUBLIC.md封存新W。正常完整writer路径与FORENSIC_ONLY失败回收路径分开；失败、缺result或writer_finalized=false不能改写成true，也不能因此丢弃失败现场。forensic封存不证明raw、cohort或验收通过，判定仍由独立岗本地解密核验。

APP中性证据收齐后立刻告知用户可手动停APP；LOAD密文与receipt完整下载且bytes/SHA核实后立刻告知用户可手动停LOAD。独立本地判定不占开机等待。不新增自动关机、倒计时、guest shutdown、云stop计划或VM timer；旧工具里stop_utc入口不调用。子进程／HTTP／observer期限不等于VM停机。

本kit不含真实token、明文密钥或实际批准，测试工具与新backup key只由独立岗封装；root只搬PUBLIC密文。两个实例当前是否运行、实际授权和所有现场门禁均未在离线阶段验证。
