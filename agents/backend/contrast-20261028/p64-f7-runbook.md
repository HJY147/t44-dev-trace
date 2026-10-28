# f7 P64短诊断：先预装，再两阶段准入

源码c0268820；目标f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f，绝对截止2026-10-28T16:00:00Z。这里是模板，尚无本包实际phase/grant/budget/key/session。只root云操作；null和尖括号必须来自本次真实回执，不能原样运行或填旧a12/P16绑定。80/800/8000短诊断不是600秒正式性能授权。

## 预装与公共依赖

新工具目录 `tmp/790_backend_contrast_20261028/p64-f7-window1600/`，manifest `1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8`。APP和LOAD分别顺序执行install-part01至04.PUBLIC.txt，目的 `/root/t44-r9/p790-f7-1600-01`。完整命令15107/16004/15608/9499字节，各留300说明仍<18000；只安装13个PUBLIC模块和manifest，拒覆盖/混装，最终核所有源字节及0444/目录0755（支持umask077）。不得把未完成安装称运行ready。

APP另需已限定审过的scope桥完整安装 `/root/t44-r9/scope-bridge-v3-01`，manifest精确e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7。790_budget只复用其固定SHA的phase_operation_lock/admit_budget/live_mysql，不执行scope provisioning、不修改桥。LOAD不需要SQL预算操作。每个新phase的helper必须21599B/SHA305f9eae...25dd82d；新v4 profile02 GEN为30497B/SHA6b2da1de...b2410fd，完整值在manifest。实际source53/image/binding/CA由本次新build/prepare取得，不能把旧图片ID改标签。

宿主Linux root、Python3.10 stdlib、Docker默认context、原openssl；SQL在实际本源backend image/data-only admin，edge和LOAD使用本次实际证明的source-free官方Python alias/id。没有新监听、公用传输服务、SSH或pip。所有新文件/目录O_EXCL，失败保前缀，不自动retry/resume。

## 先把临界路径全部准备好

在S1签服务token前，先完成所有代码安装、资源collector/mirror及状态命令、LOAD keygen、公钥搬APP、两机配置与结果读取/接收命令准备。S1也有真实service有效期，不能签完再耗时写工具。LOAD先运行原transport的新SOURCE/STOP副本：

```sh
python3 -B /root/t44-r9/p790-f7-1600-01/transport/790_transfer.py keygen --output-dir '<NEW_LOAD_KEY_DIRECTORY>'
```

私钥留LOAD新0600目录；只搬public.pem及其真实SHA到APP。密封算法/线格式原样；这里只改f7/16Z两常量。APP/LOAD-configuration.template.PUBLIC.json字段全部为PUBLIC路径/哈希/身份（私钥是路径，不能放内容）。实际LOAD hostname/Python alias/id必须新鲜核验；不默认旧主机或镜像。镜像helper/mirror只是资源证据，绝不替代真实session。

## 1. root prep grant和真实空库bootstrap

根先等同源完整CI、新build、prepare/arm/config/infra/migrate所需实际预算和guard通过，再给prep-grant模板新文件。`admitted`默认false；root核事实后才填true。grant绑定source、run_id、binding SHA、namespace/database/workers、实际backend image、source_proof SHA/count53、seed44/anchor04:00、16Z、issued_at、新nonce、600TTL和原cohorts。prep的HTTP_authorized=false；roles如实记录当时mysql/rabbitmq infra，其他未启动角色若填必须标absent，不能说running。原GEN预算probe回执路径/SHA仍必填，不推384实测。

bootstrap必须在GEN idle/TLS401前，保持所有业务表空门禁；账号用原init-user stdin，seed保原seed_demo显式anchor（seed-demo CLI无anchor，不能替换成默认now）。每个admin完整调用都是同锁→原305f admit实际身份/容量→原命令/输出→释放；不持锁调用GEN。

```sh
python3 -B /root/t44-r9/p790-f7-1600-01/790_bootstrap.py \
  --phase-dir '<ACTUAL_NEW_P_PHASE>' --binding-sha256 '<ACTUAL_BINDING_SHA>' \
  --output-name fixture790-f7-01 --anchor-at 2026-10-28T04:00:00Z \
  --manifest-sha256 1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8 \
  --budget-receipt '<ACTUAL_PHASE_BUDGET_RECEIPT>' --budget-receipt-sha256 '<ACTUAL_BUDGET_SHA>' \
  --root-grant '<ACTUAL_PREP_GRANT_PUBLIC_FILE>' --root-grant-sha256 '<ACTUAL_PREP_GRANT_SHA>' \
  --scope-bridge-dir /root/t44-r9/scope-bridge-v3-01
```

实际完整source53/uid10001、三真实CLI用户、40/6000/9000/15000/V2 seed/anchor、counts/public receipt均核验。bootstrap记录prep grant和nonce，不会启动API/scheduler/负载。任何部分失败保原DB/目录，不删表重seed。

## 2. idle后另给short-P pressure grant，再S1

根原GEN idle须传实际budget两flag，并核api/consumer/mysql/rabbitmq/web/tls-gateway六实际roles及source/CA；scheduler absent，明确仅开发6-role。根另生成pressure-grant新文件，kind ROOT_P_PRESSURE_GRANT_V4、HTTP_authorized=true；roles是每role有限PUBLIC `{container_id,image_id,running,restart_count}`，六个都running/restart0，scheduler为`{absent:true}`。APP会按owner Docker labels及IDs/image/state再查。prep grant不能用于HTTP。pressure grant的source/binding/namespace必须同本次bootstrap，但不能改bootstrap事实或旧文件。

```sh
python3 -B /root/t44-r9/p790-f7-1600-01/790_host.py stage1 \
  --phase-dir '<ACTUAL_NEW_P_PHASE>' --binding-sha256 '<ACTUAL_BINDING_SHA>' \
  --fixture-name fixture790-f7-01 --split-name split790-f7-01 \
  --manifest-sha256 1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8 \
  --budget-receipt '<ACTUAL_PHASE_BUDGET_RECEIPT>' --budget-receipt-sha256 '<ACTUAL_BUDGET_SHA>' \
  --root-grant '<ACTUAL_PRESSURE_GRANT_PUBLIC_FILE>' --root-grant-sha256 '<ACTUAL_PRESSURE_GRANT_SHA>' \
  --scope-bridge-dir /root/t44-r9/scope-bridge-v3-01
```

新split control包含同source的pressure grant，原fixture control中的prep记录保持。S1原SQL/CLI/事件不变/独占441对/版本检查不改；一整个S1数据容器在共享锁及原budget.admit后执行，释放后再HTTP。真实candidate/selection/control SHA从PUBLIC完成行取得。根立即只填两份预先准备好的driver配置实际control/CA/新grant/新binding/收件key/mirror pins；不要在此时开发脚本或安装其它东西。

## 3. 一次S2→密文→接收→原matrix

APP配置包含actual phase/fixture/split/budget/grant/scope桥、收件公钥/keySHA、CA、已起资源mirror handoff路径/SHA、新output目录；LOAD配置包含同binding/grant/control/CA/key pins、新work目录、仅LOAD私钥路径、实际mirror目录/绑定、hostname及Python alias/id。两个配置写好并核SHA后才启动producer：

```sh
python3 -B /root/t44-r9/p790-f7-1600-01/790_producer.py \
  --configuration '<ACTUAL_APP_PUBLIC_CONFIG>' --configuration-sha256 '<ACTUAL_APP_CONFIG_SHA>'
```

producer先核manifest/binding/public key/mirror，原edge S2严格TLS真实登录并造441对；每个pressure grant在phase O_EXCL一次marker，不能新split重发同grant。密码/token不打印，session只0600私包；原600 TTL、实际service/user expiry和created_at不改。producer调用原transfer密封三输入和独立资源mirror，输出PUBLIC metadata及OPAQUE。终端输出≤17000；若首part放不下则只打印metadata，root按预写的读取命令逐part读。每段raw≤11800，part JSON约16000，含包装/说明仍必须<18000，不能再base64整个part JSON扩大。

把producer终端JSON和每个part-i.OPAQUE.json原样放到LOAD新PUBLIC/OPAQUE文件（root复制时仍用O_EXCL），核实际复制SHA。用预装接收器，不在临界期写代码：

```sh
python3 -B /root/t44-r9/p790-f7-1600-01/790_receive.py metadata \
  --configuration '<ACTUAL_LOAD_PUBLIC_CONFIG>' --configuration-sha256 '<ACTUAL_LOAD_CONFIG_SHA>' \
  --input '<COPIED_PRODUCER_TERMINAL_PUBLIC_JSON>' --input-sha256 '<EXACT_COPIED_SHA>'
python3 -B /root/t44-r9/p790-f7-1600-01/790_receive.py part \
  --configuration '<ACTUAL_LOAD_PUBLIC_CONFIG>' --configuration-sha256 '<ACTUAL_LOAD_CONFIG_SHA>' \
  --input '<COPIED_PART_I_OPAQUE_JSON>' --input-sha256 '<EXACT_COPIED_SHA>'
```

对实际part_count的0..N-1逐次导入；接收器只核身份和ciphertext片SHA、独占写raw片，不解密、不发matrix。原consumer另核全压缩包/解压大小/总SHA，再原helper open、真实session语义、资源mirror live numeric状态；一切完整才运行原790_load：

```sh
python3 -B /root/t44-r9/p790-f7-1600-01/790_consumer.py \
  --configuration '<ACTUAL_LOAD_PUBLIC_CONFIG>' --configuration-sha256 '<ACTUAL_LOAD_CONFIG_SHA>'
```

原baseline1=80、warmup40=800、measure400=8000，400 active无think；330秒全矩阵准入、每cohort90秒、完整计数/共享abort/逐请求绝对截止全部保留。输入还有一次matrix marker防换output重跑。过期、失败或不完整停止该臂，保实际partial/inflight，禁止改timestamp/TTL/阈值/门禁或自动重跑；旧session不续包。完整结束也仅短开发诊断，600秒正式性能须另明确授权和独立协议。

## 本地证据与未运行边界

68唯一本地检查=原33诊断+13transport+13新grant/budget负例+9实际安装/opaque接收，0failure/error/skip，FastAPI旧依赖有1条上游弃用warning未改依赖。实际f7 Git53文件快照跑原CLI/seed/S1/S2/原handler兼容；SQLite/TestClient不是MySQL/真实HTTP。3个数据/S1/S2业务文件逐字同，HTTP除configure外18函数/类逐字同，原46用例66assert在仅身份/时间字面更新后AST原序同；transport只有SOURCE/STOP两常量。business-byte-proof/verification和JUnit见工具目录。host3.10仅AST，实际本机Mac/Python3.12；本岗无云/新CI/独立私件/正式性能结论，待根限定审核和本次真实准入。
