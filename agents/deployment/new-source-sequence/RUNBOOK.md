# material08 顺序入口：离线准备，尚未现场批准

实际源13acb43a804e717e7485091895378511fe3d9b76；旧packet90b只证明原400client/800task/40project/CA/角色/namespace/database历史来源。新source691422…、bundle414e3069…、新final-backend-web-import-v1 receipt及真实config766701…证明实际运行身份。两链不能互换，旧receipt路径/时间不能伪填新值。后台仍原七服务/资源；不seed/新建task/重建库，不触云，不创建VMstop timer。

本目录MANIFEST绑定后端4a5401ac的精确工具SHA。backend目录从该提交agents/backend/new-source-material原字节复制；不要把host_runner新SHA当旧ee72 pin。新maintenance_v3保留原SOURCE90b历史资格和审计/断点逻辑；新增core双链校验及新host pin，不冒称原文件未改。rotation原文件字节未改，wrapper另核新快照再调用。原prepare_next_manual/resume硬钉旧ID且自动旧授权，不能运行。

## 现场必需输入，当前全部待实际取得

- root核准升级后七角色快照P09-existing-containers.PUBLIC.json：root_approved=true、source_sha=13ac、真实observed_at、七项当前ID/image/user/limits。api/consumer/scheduler必须新backend config766701…，web新2fe34…；数据库/MQ/gateway仍原ID/原资源卷。当前模板false/containers空，不能用模板批准。
- 新source-manifest.json、backend-bundle-manifest.json、新import receipt（同bundle414e3069…）、旧session.private.json与原CA/accounts；均私密输入路径，绝不打印会话/token。
- backend新material-v2授权：material08/p14/maintenance08，nonce/new_identity/expected_api_image_id/loaded_receipt_reference必须现场真实绑定，模板false。
- 维护授权保留原schema manual11-cohort-maintenance-authorization-v2及source_sha=90b字段作为旧cohort来源，operation_id=r30restoretransition08、root_approved须显式批准、old_packet_sha/original_ids/namespace/database/排他与原controller guard全部保留；另传上述新source授权和三个新manifest。两个批准均不等于benchmark grant。
- 原发压已退出，排他、旧controller与停机timer状态经root确认；不启动旧controller、不新建timer。相关发压或维护并发时拒绝，不以回收时间替代排他证明。

## 手工顺序（变量均为现场真实路径，不是预填成功）

设置 KIT 为本目录绝对路径，BACKEND为4a5401ac新后端工具绝对目录；NEW_SOURCE/NEW_BUNDLE/NEW_IMPORT为新链三文件，NEW_IMPORT_OBSERVATION为原producer生成的NEW_IMPORT.observation.PUBLIC.json sidecar，REMOTE_IMPORT_PATH为APP上receipt真实canonical /root路径（本机复制路径不得替代），OLD_PACKET/CA/ACCOUNTS为旧来源私密文件，NEW_AUTH/MAINT_AUTH为现场真实批准文件；API_ID为新快照的api ID，API_IMAGE为完整766701 config digest。所有输出须全新，保留失败前缀不自动重试。

1. 将真实新快照存KIT/P09-existing-containers.PUBLIC.json。先核本目录与后端MANIFEST SHA、旧controller闲置、七角色身份/资源/TLS/数据库volume/schema/index/current worker/pool，以及完整服务健康。旧resume脚本不用于这一步。新配置/Env/overlay漂移必须重plan重核。
2. 执行backend零Docker双链检查，再维护：

```sh
python3 "$BACKEND/check_inputs.py" --remote-import-receipt-path "$REMOTE_IMPORT_PATH" --old-packet "$OLD_PACKET" --authorization "$NEW_AUTH" --ca "$CA" --source-manifest "$NEW_SOURCE" --bundle-manifest "$NEW_BUNDLE" --import-receipt "$NEW_IMPORT" --import-observation "$NEW_IMPORT_OBSERVATION"
python3 "$KIT/cohort_maintenance_v3.py" --mode apply --root-admit-maintenance --backend-tools "$BACKEND" --old-packet "$OLD_PACKET" --accounts "$ACCOUNTS" --authorization "$MAINT_AUTH" --new-authorization "$NEW_AUTH" --ca "$CA" --source-manifest "$NEW_SOURCE" --bundle-manifest "$NEW_BUNDLE" --import-receipt "$NEW_IMPORT" --import-observation "$NEW_IMPORT_OBSERVATION" --api-container "$API_ID" --expected-api-image-id "$API_IMAGE" --output "$NEW_MAINTENANCE_OUTPUT"
```

确认原400 transition state2、800全资格/原断点审计均满足，保留真实维护receipt；任何未知结果须使用原inspect/previous路径，不直接重跑apply。maintenance接口模式/previous守卫保留。

3. 执行backend fresh material-v2（原400/800角色、horizon、binding、process_exit全部保持）：

```sh
python3 "$BACKEND/host_runner.py" --api-container "$API_ID" --expected-api-image-id "$API_IMAGE" --discover-maintenance-gateway --old-packet "$OLD_PACKET" --accounts "$ACCOUNTS" --authorization "$NEW_AUTH" --ca "$CA" --source-manifest "$NEW_SOURCE" --bundle-manifest "$NEW_BUNDLE" --import-receipt "$NEW_IMPORT" --import-observation "$NEW_IMPORT_OBSERVATION" --output "$NEW_MATERIAL_OUTPUT"
```

必须实际FRESH_MATERIAL_NOT_BENCHMARK_AUTHORIZATION且material_process_exit_proof.process_exit_proven=true，不能用exit0单独替代资格通过。

4. 原子轮换现有scheduler目录bind内凭据，再观察完整新扫描：

```sh
python3 "$KIT/rotate_current.py" --material "$NEW_MATERIAL_OUTPUT/material.PUBLIC.json" --backup-dir "$NEW_ROTATION_BACKUP"
python3 "$KIT/observe_full_scan.py" --api "$API_ID" --rotation "$NEW_ROTATION_BACKUP/rotation-with-time.PUBLIC.json" --material "$NEW_MATERIAL_OUTPUT/material.PUBLIC.json" --output "$NEW_SCAN_OUTPUT"
```

原rotation守卫：0600/single-link/原CLI原字节SHA/原挂载目录只读bind/原uid gid/原子replace/fsync/回读；保存旧token私密备份，不打印。只改现有token文件，不创建第二scheduler。确认现有scheduler/consumer已按原资源健康运行；若未运行，只能root核新快照精确ID后显式docker start对应ID，不能用旧resume预期ID。不得停掉正在推进的旧未完成scan去凑新扫描：原tick会续旧run，observer须等待rotation后真正新started且finished、status2/error空/scanned_count>0。900秒仅observer边界，非VM停止时间。错误/超时保留每条观察，不能降判据。

5. 用原cms_five_transport.py原字节封装新five（其SHA来自原kit），LOAD端独立核新packet/身份/材料与测试冻结。新QA W=/root/t44-final-20261031/QA753_NEXT_V52；p14/grant由独立岗新freeze，部署岗不批准，不复用p13或旧material/grant。新原始计数/首因/关闭完整性工具由独立测试岗负责，不能计入部署自测。

## 本地验证范围

仅脚本语法/3.10 AST、manifest及少量未批准/旧source/旧image拒绝检查。未运行任何实际维护、发行会话、凭据轮换、scanner/DB查询、封包或发压；现场排他、旧timer闲置、真实新快照与import receipt均仍待实核。测试退出/证据停止写入并回收核验后立即告知用户手动停机。

4a5401ac新门禁：APP live maintenance/host均以真实receipt canonical path对auth ref及producer receipt_path三方绑定，验证原文件uid0/mode0600/mtime_ns/bytes/SHA；ref/receipt/observation三时间必须相等且UTC非未来。离线check_inputs只以显式remote路径验证来源，不能声称本机fsstat等于APP现场。缺sidecar不得自造；需原import producer现场生成。原144d/a60包作为历史draft保留，不是最终kit pin。

Observer修订：--material必填并对rotation.material_sha256原字节绑定、本轮packet_run_id08与process_exit_proven绑定，rotation.scheduler_id须当前批准快照scheduler；rotation时间必须UTC非未来。command返回后再次严格检查monotonic<deadline，超900秒的成功结果拒绝，不作为新完整扫描通过。原status/error/count及started/finished相对rotation的判据保持；900秒不控制VM。
