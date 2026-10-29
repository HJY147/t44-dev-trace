# v4：5d源、16:00Z窗口与实际连接预算

root已确定源`5d5e0a15e3b15e2f509c4ae71a927bbc35579be7`、停止时间`2026-10-28T16:00:00Z`。root报告product40682367472四job及Docker40682640278通过；这些是开发验证，不是400用户/600秒性能结论。部署岗只本地准备，原APP/LOAD云操作均由root执行。

已准备的本地对象位于`agents/deployment/v4-20261028/`：

| 对象 | SHA-256 |
| --- | --- |
| frozen-5d-1600/profile.json | 3b3b6d4ca4f01a3f7bc36ac60cd2a56ce3930220251abc886de778db6d90f6f7 |
| generation.py | 3232c18eb304d02875411d43f922b63f36a1e162c633eb808e67b3373e3cbcc9 |
| resource-stream.py | d38143741c9ffc78c0163b2badc9ce151628dd23dfc1e53292d8061cab741c87 |
| mysql-budget.py（21599字节） | 305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d |
| backend-upgrade.py | 53974361404c1d25d11b5010d0b7bb40c9c5573da16d51d5b4e7134b9a118c2f |
| source-artifact-receive.py | 0a9260cf924de60713eda8f3a63339e4a6d5e41dea9ddc5fc8700a0f6a5d7219 |
| delivery-5d-1600/manifest.PUBLIC.json | c257623f0be865e104fcf740593347fd9524e6be9b5fc0b4d938c750ee03f558 |

按`delivery-5d-1600/`的`01-part-000.sh`至`05-part-004.sh`依次提交，最后`06-verify-install.sh`。完整base64加256字节description最大15372，全部低于18000；不能把其中多个脚本合在一条云助手命令。全新远端`/root/t44-r9/v4-code-20261028-01/profile`，O_EXCL拒覆盖。安装只公共代码，无服务/业务账号/env/Token。原07:30、08:15、10:30对象及factory不变。

源码包的本地完整命令（已在本岗工作树执行，结果见source-package.PUBLIC.json）：

```bash
task_root='/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/deployment-v4-profile-20261028'
python3 "$task_root/deployment/cloud-reuse/v4/derive-profile.py" package \
  --repository "$task_root" \
  --profile "$task_root/agents/deployment/v4-20261028/frozen-5d-1600/profile.json" \
  --profile-sha256 3b3b6d4ca4f01a3f7bc36ac60cd2a56ce3930220251abc886de778db6d90f6f7 \
  --output "$NEW_CANONICAL_LOCAL_PACKAGE_DIRECTORY"
```

本地包在本岗worktree的`.agent-worktrees/.runtime/source-v4-5d-1600/source-artifact.zip`，166458字节/SHA`9ebb356360d190f466219a596f8d0954bb38399c0210d9aa75f9b47d81b9eea6`；manifest SHA`3b398cd74322d52169d1267946cc90d80c7755ed708d6bc0f9aa5029a32f9763`，source archive SHA`392222af763b6f7fe969d25e17621c381b7588a61f950adac79b6378e6f4bffb`，53实际Git源文件。真实本地receiver已完整验证CRC/安全TAR/五文件/source字节模式；它的遗留输出字段`official_zip_sha256`不把本地包变成官方CI下载。

若root选择现有官方CI运输，可以沿用`resume-source-package.yml`的精确source/stop输入，或已注册docker-integration桥：

```bash
gh workflow run docker-integration.yml --ref "$ROOT_REVIEWED_WORKFLOW_REF" \
  -f resume_source_sha=5d5e0a15e3b15e2f509c4ae71a927bbc35579be7 \
  -f resume_stop_utc=2026-10-28T16:00:00Z
```

这个旧workflow内部的source builder与v4相同（完整SHA53974361…），只有公共source包可复用；用这里审过的v4 generation，不安装workflow里的旧generation。官方artifact ZIP与其中source-artifact.zip的完整SHA都由root下载后重新核，不能把本地9ebb强贴在别的ZIP。所有随后build/prepare均绑定所选同一个实际manifest，不混用包。

远端source接收/build模板（变量必须来自root真实上传/下载及原证明，空值不能执行）：

```bash
PROFILE=/root/t44-r9/v4-code-20261028-01/profile
python3 "$PROFILE/source-artifact-receive.py" \
  --zip "$ACTUAL_SOURCE_ZIP" --zip-sha256 "$ACTUAL_INNER_ZIP_SHA256" \
  --manifest-sha256 "$ACTUAL_SOURCE_MANIFEST_SHA256" --output "$NEW_SOURCE_CHECKED_DIR"
python3 "$PROFILE/backend-upgrade.py" build \
  --package "$NEW_SOURCE_CHECKED_DIR" --manifest-sha256 "$ACTUAL_SOURCE_MANIFEST_SHA256" \
  --image-proof /root/t44-r9/image-proof.py \
  --proof-raw /root/t44-r9/proof-v2-01/proof.jsonl \
  --output "$NEW_BUILD_DIR" --run-id "$NEW_BUILD_RUN_ID"
```

新镜像ID、buildbinding SHA由本次真实build返回；这里未构建镜像，不填旧475a/a12。root选择全新namespace、输出目录、DB、CA及四个实际空闲端口。prepare仍仅文件准备：

```bash
python3 "$PROFILE/generation.py" prepare \
  --factory /root/t44-r9/campaign-935/p/controller.py \
  --upgrade-binding "$NEW_BUILD_DIR/upgrade-binding.json" \
  --upgrade-binding-sha256 "$ACTUAL_NEW_BUILD_BINDING_SHA256" \
  --source-package "$NEW_SOURCE_CHECKED_DIR" \
  --source-manifest-sha256 "$ACTUAL_SOURCE_MANIFEST_SHA256" \
  --original-proof /root/t44-r9/proof-v2-01/proof.jsonl \
  --image-proof /root/t44-r9/image-proof.py \
  --output "$NEW_CAMPAIGN_DIR" --run-id "$NEW_RUN_ID" \
  --app-ip "$ACTUAL_APP_PRIVATE_IP" \
  --f-tls-port "$F_TLS_PORT" --f-http-port "$F_HTTP_PORT" \
  --p-tls-port "$P_TLS_PORT" --p-http-port "$P_HTTP_PORT" \
  --p-workers 64 --p-pool-size 5 --p-max-overflow 0 \
  --stop-utc 2026-10-28T16:00:00Z
```

F固定4worker/default5+10；仅P API写两个显式ENV，consumer/scheduler/运维不继承。P7只5/10；P16可5/10或15/0（API240，总304），或20/0（API320，总384）；P64只5/0（API320，总384）。不接受64×(5+10)。保留的API10g/MySQL12g等原Compose limits未因64核机器自动增加，实际内存是否足够仍待root观测，不能用新机器推定达标。

按每个新phase的实际prepare回执选择`PHASE_DIR`和`PHASE_BINDING_SHA256`，F/P分开执行，不同时启两组业务挤占资源。16Z截止前至少600秒才可新启动动作；stop/status保留原清理出口：

```bash
python3 "$PROFILE/generation.py" arm --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$PROFILE/generation.py" config --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$PROFILE/generation.py" infra --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$PROFILE/generation.py" probe-budget --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
```

prepare/arm/infra不准入业务。`probe-budget`只读实际MySQL，绑定CID、宿主PID/starttick、镜像、StartedAt、namespace、数据库、server UUID、真实max；配置prior384/128不算实测。返回`budget_receipt`及`budget_receipt_sha256`，作为后续两变量；真实不足则保留失败，不启动迁移/API/consumer/web/scheduler。

```bash
python3 "$PROFILE/generation.py" migrate --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256" \
  --database "$ACTUAL_NEW_PHASE_DATABASE" \
  --budget-receipt "$ACTUAL_BUDGET_RECEIPT" --budget-receipt-sha256 "$ACTUAL_BUDGET_RECEIPT_SHA256"
python3 "$PROFILE/generation.py" idle --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256" \
  --budget-receipt "$ACTUAL_BUDGET_RECEIPT" --budget-receipt-sha256 "$ACTUAL_BUDGET_RECEIPT_SHA256"
```

每次migrate/idle/scheduler-token/rotate/start都在同共享锁内重查真实预算和实例身份；实际Config.Env只筛两个池容量键，API按P计划，已运行consumer/scheduler必须无覆盖而有效5/10，其他ENV不输出/保存。初scheduler absent仍记缺失，等真实scope请求（不能猜项目ID）后root/backend桥再调用原真实credential-admin，新增GEN参数同上。桥不能沿用只传phase/binding的旧调用。

共享互斥给backend直接SQL步骤：从当前phase加载已双pin的`mysql-budget.py`，使用`operation_lock(Path(PHASE_DIR), PHASE_BINDING_SHA256, timeout_seconds=min(10, remaining_deadline_seconds))`。文件`<phase>/.v4-operation.lock`为0600/同owner、O_NOFOLLOW/CLOEXEC/nlink1、flock EX|NB，50ms轮询，0–30秒且默认10；超时失败。每SQL步骤持至结果读取后释放，调用子GEN前必须释放。observer用独立`.v4-observer.lock`，一个持久连接；两方确认同一契约，未覆盖的外部并发SQL不能算已准入。

只读持久观测模板（root使用新输出名；不改业务SQL、隔离、pre_ping或持久性）：

```bash
python3 "$PROFILE/generation.py" observe-mysql \
  --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256" \
  --budget-receipt "$ACTUAL_BUDGET_RECEIPT" --budget-receipt-sha256 "$ACTUAL_BUDGET_RECEIPT_SHA256" \
  --until-utc "$ACTUAL_OBSERVER_STOP_NO_LATER_THAN_16Z" --interval-seconds 5 \
  --output "$PHASE_DIR/receipts/mysql-observer-UNIQUE.PUBLIC.jsonl"
```

输出Connections/Threads_connected/Max_used_connections/Uptime/Threads_running等，固定connection_id证明观测连接未重建；首delta=null、计数reset/missing明确。全局计数含health/admin/observer，不能据此精确归因业务churn；自身1槽、health4、单运维15、临时预算probe1分别记录。此持久CLI路径目前仅真实本机pipe守卫，无真实MySQL持久客户端验收；若实际读取不完整必须保留raw和标缺。

结束用原owned stop保卷，root再按预算停VM、保盘，不自动删除/释放或更改旧结果：

```bash
python3 "$PROFILE/generation.py" stop --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$PROFILE/generation.py" status --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
```

仍需root真实预算/完整角色ENV和identity、独立新F、短诊断后明确新600秒授权。旧270/active400/600秒与LOC门禁均未更改；资源机器配置不能替代代码规模验收。
