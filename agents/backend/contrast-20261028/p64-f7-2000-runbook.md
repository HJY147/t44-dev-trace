# f7 P64 20:00窗口：先预装、再两阶段准入

本版只作新窗口派生，不续旧授权。工具目录`tmp/790_backend_contrast_20261028/p64-f7-window2000`；source仍f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f，stop为2026-10-28T20:00:00Z，manifest为`2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de`，delivery为`305c5a722ee94d1339b2400a292bbc83416e6c40ba3c0a4b7fc49efdcfd41352`。本岗没有actual phase/binding/grant/budget/CA/key/session；模板不能直接运行。

APP、LOAD各按顺序投递`ui-part01.PUBLIC.txt`至`ui-part07.PUBLIC.txt`，其内容已经是完整外层命令，直接投递，禁止再次base64。若root现有helper要对输入包装一次，只给对应`raw-partNN.PUBLIC.sh`。两种方式各选一种，不可重复安装。同一目的`/root/t44-r9/p790-f7-2000-ui03`，旧1600目录保留；raw最大11750，完整UI+300最大16090，全部<18000。安装最后行必须all_thirteen_verified=true；拒覆盖、混装，PUBLIC源0444/目录0755。

APP仍依赖已审原scope桥`/root/t44-r9/scope-bridge-v3-01`（manifest e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7），只读复用budget方法，不改旧scope桥或执行其callback。新GEN路径`/root/t44-r9/v4-code-20261028-03/profile/generation.py`，SHA9edafbbff0586b5f77a701bd37f715685fba4169abaae510474343af75a8b427；每phase helper仍305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d。真实预算receipt路径/SHA必须由本次probe提供，不推384实测。GEN所有必要budget flags保持；父进程不跨GEN持锁。

模板pin勘误：777968原两配置模板误继承16Z transport摘要；须用本次修正模板，`transfer_sha256`精确为`ba11a4d5cf7bdf70f632beafcccb09129831b91c958b6ba7d7f546d8773f6b07`，与manifest所列及已安装12574B transport一致。修正后APP模板SHA`1c1db93d19a985ea48681eb0e96d3122031d149297c8bd7c36ece95647e67c73`，LOAD模板SHA`ed79ef8d8b53e09cac8318a1d1a75aa98c80a06779ed7a0a4c298bc0c9f3efaa`。只更新准备配置的输入pin，13运行文件、manifest、delivery和七分片不重装/不重打包；actual配置填入真实字段后需重新计算其自身SHA，模板SHA不是实际配置SHA。

在S1前完成全部安装、资源collector/mirror、LOAD keygen及公钥搬APP、两侧PUBLIC配置和读取/接收命令预写。LOAD私钥只存新0600目录，只有公钥与真实SHA可搬APP：

```sh
python3 -B /root/t44-r9/p790-f7-2000-ui03/transport/790_transfer.py keygen --output-dir '<NEW_LOAD_KEY_DIRECTORY>'
```

root实际prepare/arm/config/infra/migrate和预算守卫通过后，核真实新source53/image/binding并签prep grant（默认admitted=false、HTTP_authorized=false，actual字段null）；roles如实为当时infra，不能把absent写running。业务空库bootstrap必须先于GEN idle/TLS401，不清理正常auth审计以凑空表。原三用户CLI、seed44/显式04:00anchor、表空/count门禁不变：

```sh
python3 -B /root/t44-r9/p790-f7-2000-ui03/790_bootstrap.py \
  --phase-dir '<ACTUAL_NEW_P_PHASE>' --binding-sha256 '<ACTUAL_BINDING_SHA>' \
  --output-name fixture790-f7-01 --anchor-at 2026-10-28T04:00:00Z \
  --manifest-sha256 2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de \
  --budget-receipt '<ACTUAL_PHASE_BUDGET_RECEIPT>' --budget-receipt-sha256 '<ACTUAL_BUDGET_SHA>' \
  --root-grant '<ACTUAL_PREP_GRANT_PUBLIC_FILE>' --root-grant-sha256 '<ACTUAL_PREP_GRANT_SHA>' \
  --scope-bridge-dir /root/t44-r9/scope-bridge-v3-01
```

bootstrap每原admin生命周期与后续S1分别同phase operation_lock→原budget.admit实际MySQL身份/容量→原SQL/CLI→释放。其后root原GEN idle（实际budget两flags），核api/consumer/mysql/rabbitmq/web/tls-gateway六角色running/restart0、source/CA，scheduler absent；另签本次全新pressure grant/nonce，不能用prep发HTTP，也不能复用旧16Z身份或session。

```sh
python3 -B /root/t44-r9/p790-f7-2000-ui03/790_host.py stage1 \
  --phase-dir '<ACTUAL_NEW_P_PHASE>' --binding-sha256 '<ACTUAL_BINDING_SHA>' \
  --fixture-name fixture790-f7-01 --split-name split790-f7-01 \
  --manifest-sha256 2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de \
  --budget-receipt '<ACTUAL_PHASE_BUDGET_RECEIPT>' --budget-receipt-sha256 '<ACTUAL_BUDGET_SHA>' \
  --root-grant '<ACTUAL_PRESSURE_GRANT_PUBLIC_FILE>' --root-grant-sha256 '<ACTUAL_PRESSURE_GRANT_SHA>' \
  --scope-bridge-dir /root/t44-r9/scope-bridge-v3-01
```

从新S1 PUBLIC回执填原先准备好的APP/LOAD配置（实际controlSHA、CA、binding、grant、budget、收件key、镜像/主机和mirror pins）；模板tools_dir已指ui03。压力临界路径不再编程或安装。APP producer→原S2真实TLS登录/441独占任务对→原密封算法→PUBLIC metadata及OPAQUE，密码/token只0600私件；只root搬opaque。依次用预装receive metadata/part，再consumer，不改线格式：

```sh
python3 -B /root/t44-r9/p790-f7-2000-ui03/790_producer.py --configuration '<APP_CONFIG>' --configuration-sha256 '<APP_CONFIG_SHA>'
python3 -B /root/t44-r9/p790-f7-2000-ui03/790_receive.py metadata --configuration '<LOAD_CONFIG>' --configuration-sha256 '<LOAD_CONFIG_SHA>' --input '<COPIED_PUBLIC_METADATA>' --input-sha256 '<COPIED_METADATA_SHA>'
python3 -B /root/t44-r9/p790-f7-2000-ui03/790_receive.py part --configuration '<LOAD_CONFIG>' --configuration-sha256 '<LOAD_CONFIG_SHA>' --input '<COPIED_OPAQUE_PART_I>' --input-sha256 '<COPIED_PART_I_SHA>'
python3 -B /root/t44-r9/p790-f7-2000-ui03/790_consumer.py --configuration '<LOAD_CONFIG>' --configuration-sha256 '<LOAD_CONFIG_SHA>'
```

part按本次实际part_count逐个接收，不把其JSON再整体base64扩大；producer完整终端≤17000、片raw≤11800。原所有元数据/SHA、解密后真实session检查、330秒全矩阵准入、每cohort90秒、600私包TTL及原服务有效期、失败停发/保inflight/一次marker全部保持。80/800/8000与400active/no-think仍是短开发诊断，六角色/scheduler absent不等于正式七角色600秒验收。过期或失败保前缀，禁止改时间/TTL、自动重跑或删库重seed。
