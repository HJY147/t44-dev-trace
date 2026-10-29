# R30 最短执行接缝（未来root执行；本岗未启云）

当前仅本地合成验证。root批准的是材料准备，不是正式grant。产品source固定0b，APP原始import60、CA/角色/窗口/身份仍须启动后实际取得，不能用模板/CI receipt代替。源码context62和import runtime60是不同计数。

顺序：源码/镜像/全部代码与密文传输工具/infra预检齐 → 初始化三合成账号并原seed6000 → 获实际40项目ID与容量/预算 → 所有可运行前置检查齐后签4材料身份 → 正常API新增400任务/400已有任务事件并读回 → 实际count/snapshot/独占写者证据 → 一次性组装新包 → 原部署密封/中转 → 新QA adapter prepare默认false → 另一次root决定才可grant。四会话不足覆盖完整window+30秒则停止，不延长、重登、重试或retime。必要API写不是正式测量。

1. 将本目录完整只读安装为`/neutral-code`，actual计划/输入置`/neutral-input`，本轮全新0700输出根置`/neutral-output`。在准确backend镜像内用`python -B`；**不使用-I**，保留官方镜像PYTHONPATH。所有操作的新目录必须不存在。
2. root填`plan.template.PUBLIC.json`的新run/namespace/DB、窗口、CA/IP字面量、actual import原件SHA/绝对原路径/UTC及同SHA完整config/OCI/DiffID/package链审查；把允许写与实际project IDs按阶段明确冻结。backend/LOAD值分别为冻结config身份，不把OCI actual_id等同config。origin必须是与connect_ip完全相同的私网IPv4字面量；普通HTTPS CA/IP验证保留。
3. 以下所有`admin.py`调用，**外层必须由root已审9e budget helper持有准确本轮binding的admitted上下文和operation lock，直到该命令结束**。传入原GEN probe原始bytes(kind=actual-owned-mysql-budget-v4)，其SHA绑定plan.budget.actual_admission_receipt_sha256（历史字段名，不是锁内新admission的SHA）。owner在锁内另落admission.PUBLIC.json(role=lock-held-live-readmission)并持锁覆盖docker退出，不修改plan/intents；脚本不替代外层admission或锁，直接admin.py不是授权入口。旧305f拒绝。本岗不猜部署P1的外层命令，由root使用已复审P1调度入口承接。

```sh
# 每个seed/service/count各有明确同run/namespace/DB/binding intent；新目录、原APP实际receipt。
python -B /neutral-code/admin.py seed --plan /neutral-input/plan.json --intent /neutral-input/seed.intent.json --budget-proof /neutral-input/current-budget.json --import-receipt /neutral-input/backend-import-receipt.json --binding /neutral-input/binding.json --output /neutral-output/seed-01 --root-budget-admitted
python -B /neutral-code/admin.py counts --plan /neutral-input/plan.json --intent /neutral-input/read.intent.json --budget-proof /neutral-input/current-budget.json --import-receipt /neutral-input/backend-import-receipt.json --binding /neutral-input/binding.json --output /neutral-output/baseline-count-01 --root-budget-admitted
```

`seed`只调用正式`seed_demo(factory, projects=40,tasks=6000,dependencies=9000,records=15000,seed=ACTUAL,anchor_at=ACTUAL_UTC)`；不改产品CLI。账号用原`python -m t44.cli init-user --password-stdin`在同预算保护下初始化，秘密只读受保护stdin。原seed默认复用synthetic-manager/developer/reviewer；root已有bootstrap若不同，先核对真实用户名/既有manifest，不能偷偷重置或再seed。seed自身保空表/manifest不匹配拒绝，禁止删库迁移凑数。

4. APP idle6实际为mysql/rabbit/api/consumer/web/tls-gateway；实际scope令牌+部署`scheduler-start`后APP7，LOAD另计，一次性容器另计。scheduler保持required；它可能合法CAS任务版本，consumer可能合法改变事件disposition，不承诺全库静默。root完成前检查后，仅用下面service一次原CLI+HTTP三次login签4材料session。scheduler所需基础凭据由部署原入口单独如实记录，不默认偷用材料包凭据。

```sh
# service intent.operation=service-token；service_name必须本namespace新名字。
python -B /neutral-code/admin.py service --plan /neutral-input/plan.json --intent /neutral-input/service.intent.json --budget-proof /neutral-input/current-budget.json --import-receipt /neutral-input/backend-import-receipt.json --binding /neutral-input/binding.json --output /neutral-output/service-01 --root-budget-admitted
# source-free执行器可在现有Python镜像运行；仍-B且本目录可导入，不安装包。
python -B /neutral-code/prepare_http.py --plan /neutral-input/plan.json --accounts /neutral-input/accounts.json --service /neutral-output/service-01/service.json --ca /neutral-input/ca.pem --import-receipt /neutral-input/backend-import-receipt.json --binding /neutral-input/binding.json --output /neutral-output/http-01 --root-admit-http-preparation
```

每成功一个login就0600排他存`session-prefix/ROLE.json`及原始私有HTTP响应。人的时间明确为request_started/response_observed/原meta server_time，绝不伪称actual issued_at；service issued_at来自原auth row。第三人失败保前两人prefix，不自动再登录。最终sessions保持原token/expires；400任务由正常create/start，400事件由正常升级API或已有最高事件，后台照常投递，不预造所有通知。最短路径实际任务应为6400，即约6000的新实际样本；评审11400+决定3600=15000、依赖9000均用真实counts核，不删数据凑6000。

5. API完成后在同9e外层预算锁中再执行`admin.py counts`，全新输出`/neutral-output/final-count-01`。root采集`exclusive-proof.template.PUBLIC.json`的真实写者/namespace证据和scheduler/consumer实际运行证据，填实际fixture_ready_at，不移动原T0/end/stop或签发时间。不得把预期布尔值当观测。

```sh
python -B /neutral-code/make_evidence.py --plan /neutral-input/plan.json --facts /neutral-output/http-01/factual-snapshots.json --counts /neutral-output/final-count-01/counts.json --exclusive-proof /neutral-input/exclusive-proof.json --output /neutral-output/evidence-01.json
python -B /neutral-code/guard.py evidence /neutral-input/plan.json --metadata /neutral-output/evidence-01.json
python -B /neutral-code/assemble.py --plan /neutral-input/plan.json --evidence /neutral-output/evidence-01.json --sessions /neutral-output/http-01/sessions.json --counts /neutral-output/final-count-01/counts.json --ca /neutral-input/ca.pem --source-manifest /neutral-code/source-manifest.json --bundle-manifest /neutral-code/backend-bundle-manifest.json --import-receipt /neutral-input/backend-import-receipt.json --binding /neutral-input/binding.json --output /neutral-output/new-packet-01 --root-admit-new-packet
```

`assemble`只写NEW/inputs规定五件：session.private.json、ca.pem、两原manifest、actual原import receipt。created_at为首次实际完成时刻，随机新nonce，除binding字段的canonical JSON+LF做绑定。新目录拒覆盖，不retime旧包。inventory≤300s、窗口780..900秒、end到stop≥90秒、T0距created≤600秒、四expiry>end+30秒。原proof不够新/target改变必须重新实际采集，不能伪造observed_at。

6. root在原已审部署新密封/传输接口搬运这个全新目录；本工具不重用旧key/path/opaque包，不改QA adapter/core。官方`ENTRY_0B_V24.sh prepare --workspace ACTUAL --neutral-opened-dir ACTUAL --run-id ACTUAL`只network-none准备，输出精确default-false grant。执行、外层hard-stop和资源采集仍须root独立批准与部署；本岗不执行、不填true。

本地证据只证明合成输入/代码可运行性，不证明真实Linux/Docker/MySQL/TLS、预算锁实持、实际session/材料或正式性能就绪。root必须记录实际exit、输出原件；失败保prefix，今天有限窗口结束后保盘停机。

## GEN04实际绑定与阶段范围（替代任何旧自造namespace）

原GEN没有run_id键。guard读取plan.gen_binding.path同原件raw SHA，从project=t44-cloud-RUN-p/f与database=t44c_RUN_p/f配对解析RUN r30[a-z0-9]{5,12}；plan.namespace就是实际project，run与packet同一r30window01。核kind/generation_kind/source/两manifest/phase/IP/TLS/绝对stop；只含738B公开投影、缺真实config/image/crypto/TLS/filehash的资料拒实际准入。wrapper把同原件只读挂入/neutral-input/binding.json，不改原binding。

T0是root实际生命周期起点，G=binding.stop=T0+35min，C=T0+40min独立；S+20/E+33/D780是本轮稳妥布局。E≤G且E≤C−90s，P≤S−150s（预留跨机/prepare120s+授权30s），所以S+20时P≤+17:30。HTTP/packet过cutoff即停止，packet用C作cost-stop但同时受真实G约束；没有旧包retime。

账号在seed前由原CLI初始化：accounts.init-input.template.PUBLIC.json是owner stdin-file接口，三0600私密密码stdin→固定init-user命令，原stdout user_id回填私密accounts.http-input.template.NO_SECRETS.json。密码不进argv/stdout、没有新账号类别，不改DB凭据。seed/counts阶段authorized_project_ids=[]，不要求不存在的项目或scheduler令牌；原函数仍核实际空dataset。counts读回真实project_ids后用下式产生全新下一阶段plan，不猜1..40、不改binding/source/T0/window：

```sh
python -B /neutral-code/stage_scope.py --seed-plan /neutral-input/seed-plan.json --counts /neutral-output/result/counts.json --output /neutral-output/material-plan.new.json --allow-write login --allow-write service-token --allow-write createTask --allow-write transitionTask --allow-write createEscalation
```

owner固定admin输出约定：容器--output=/neutral-output/result必须为新目录，不是JSON文件；service=result/service.json，counts=result/counts.json，seed=result/seed-result.json，原CLI私有prefix保留。owner回执给root准确对应的主机result路径；CLI flag或proof格式不代表外层授权。
