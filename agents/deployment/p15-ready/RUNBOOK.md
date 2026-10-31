# P15部署离线材料与现场顺序

应用准确源bcec3326b40814fdb1922bbfea7c29473b47ba47，build41171011125已成功下载核验；完整身份见BUNDLE_IDENTITY.PUBLIC.json。backend真实release为5c874a32的agents/backend/bcec-material/release（7个runtime工具py，非占位8）；sequence钉其实际core/host SHA。历史packet90b仍原字节/原800ID来源，绝不重命名为bcec。p15/material09/maintenance09/W QA753_NEXT_V53、grant/nonce/当前ID不能从旧p14/08复制。

服务器仍关闭。此目录所有工具默认不调用VM/SSH/云；plan_images与snapshot_phase只读Docker，profile默认只plan，只有明确root当前事实批准才SET PERSIST。ops只准verify/import/prove-loaded，不准derive/build/旧controller。无VMstop/倒计时停机。SSH按用户最新永久restrict公钥授权，由root保原hostkey真实核验；本包无2h或剩余3600秒gate，不调用旧USER_ONLY授权脚本。业务会话/材料horizon/900秒observer仍保留。

## 现场固定串联（由root总runner控制）

1. 原hostkey/SSH成功后核原七角色、原数据卷/schema/index、当前Cmd/Env/资源/空间，旧controller不活动且无其它压测。保存原回滚镜像与私密完整inspect/原配置。运行plan_images.py明确绑定原Compose全部文件、完整渲染SHA及overlay/request-diagnostics.on.json（只APIflag1），输出before.PRIVATE.json、新镜像overlay及手动rollback计划；config/env漂移须重plan。原workers64/pool5+overflow0保持，不用仓库默认4worker覆盖。
2. ops/final-image-bundle.py verify/import --package新包 --manifest-sha256 3e09cc1bfe5074832fbb61bc2e500f5b27bc23a987c3d68f9744dd650c126d29 --receipt全新/root路径。实际producer同时生成receipt.observation.PUBLIC.json；新source/bundle/真实path/stat/UTC时间用于backend/maintenance新双链，不预造APP收据。import不启动业务，不改卷。
3. root明确停止原owned api/consumer/scheduler/web四个精确旧ID，不动VM/MySQL/MQ/TLS/卷。确认无其它writers后profile/mysql_pl1_profile.py默认plan，按当前owner/volume真实free bytes/effective/persisted/planSHA作新root批准后apply三个SET PERSIST（redo2GiB/io1000/max2000）；成功必须持久值+resizeOK/目标对齐，durability1/1/doublewrite保持。部分失败保留原receipt，不auto rollback/后继。空间至少redo增量+2GiB并另核镜像/binlog/备份余量。
4. 执行plan产生的create_only_after_profile_import_and_root_preflight命令：同原全部Compose参数+新image overlay+flag1 overlay，`up --no-start --no-deps --no-build --pull never api consumer scheduler web`。不自动启动全部新worker。随后snapshot_phase.py --before-private原plan/before.PRIVATE.json --phase created --output全新PUBLIC.json。它检查原infraID/image、所有原资源/Cmd/Env（仅API多flag1）、卷/端口/安全/网络不变，新APP精确image；新四应用此时必须未运行。停止容器尚未附加网络ID可为空，但按原network名字只读核其实际对象ID不变，不冒附加已就绪。
5. root核真实snapshot后仅`docker --context default start NEW_API_ID NEW_WEB_ID`（ID来自实际created快照，不在此预填）。等API健康，snapshot_phase --phase api-web-ready再次核；consumer/scheduler明确running=false，不当最终就绪。输出root_approved=false表示观察不是授权；root总runner核checks/事实后创建明确已批准当前快照，供sequence/P09-existing-containers.PUBLIC.json。
6. backend release/check_inputs.py先新source/manifest/import observation双链检查（离线复制须明确--remote-import-receipt-path，APP真路径/stat须原producer sidecar）。再sequence/cohort_maintenance_v3.py维护09，原任务资格/800ID/审计/previous断点/不新建任务规则全部保留。其--new-authorization是本轮backend授权，--authorization为维护独立授权；两者不等于QA grant。按root原完整参数调用host_runner.py生成material09，必填--import-observation，真process_exit_proven/资格/horizon通过；不得只看exit0。
7. sequence/rotate_current.py --material MATERIAL/material.PUBLIC.json --backup-dir全新root私密目录。原子0600写入原只读目录bind，保留旧token备份/uid/gid/fsync/回读，不输出token。wrapper核当前bcec image/scheduler ID及false模板拒绝。root再start新consumer/scheduler精确ID，保持原资源。等待健康，snapshot_phase --phase all-ready实核七角色（API/consumer/scheduler/MySQL/MQ健康，web/TLS真实running）；中间快照不能冒all-ready。
8. sequence/observe_full_scan.py --api NEW_API_ID --rotation BACKUP/rotation-with-time.PUBLIC.json --material MATERIAL/material.PUBLIC.json --output全新扫描证据目录。绑material09原字节SHA/process_exit/current scheduler/UTC非未来；保原status/error/count及rotation之后新started且finished完整判据，command返回后严格900秒观察截止。旧未完成scan只能等原tick恢复，不能杀进程凑新scan。900秒只限observer，绝不关VM。
9. root按原CMS封装新five，并经独立P15 PUBLIC接口核真实QA runtime/profile/新会话/输入/独立一次grant后正式400/60/600；所有4路径P95≤270ms/吞吐/零错误/断言不变。APIflag1启用供诊断；proxy本轮不启，QA原full response headers/elapsed/慢样本保留由独立工具负责。app字段不被span求和替代，UNKNOWN不作0。正式退出/证据停止写入并全部回收后立即告知用户手动停机。

## 本地验证与未验证

真实bundle原helper verify exit0、95context逐Git bytes/SHA/CI runtime61证明，7observer合成边界通过、created阶段/资源漂移/allready误判拒绝、本地错bundle在Docker前拒绝、AST3.10/新planner与phase Ruff通过。源模板root_approved=false、会话/nonce无真值、APPreceipt/PL1/创建/启动/维护/轮换/扫描/QA均未运行。仅离线部署材料完整，不能当现场或正式验收通过。profile恢复必须独立fresh plan/批准，rollback仅明确手动，不自动重启/缩容。

## 总kit内可直接执行的精确CLI

设KIT为总kit解包绝对目录，PACKAGE为上述bcec真实镜像包APP绝对目录，API_ID为新快照API ID。APP_SOURCE_MANIFEST=$PACKAGE/source-manifest.json，APP_BUNDLE_MANIFEST=$PACKAGE/backend-bundle-manifest.json，NEW_IMPORT为ops实际producer生成的全新receipt，NEW_IMPORT_OBSERVATION=$NEW_IMPORT.observation.PUBLIC.json。OLD_PACKET/CA/ACCOUNTS保持原P09私密来源；AUTH是本轮backend/authorization.TEMPLATE.json依据真实事实独立批准的副本，MAINT_AUTH是维护09专用批准副本，二者均非QA grant。EXPECTED_API_IMAGE必须完整为sha256:479c406502b2e4834a0e8ab9ed3fd35e60df60601a041348b1e4a97825056f0e。NEW_MAINT_OUTPUT/MATERIAL/ROTATION_BACKUP/SCAN_OUTPUT均是全新APP绝对输出路径，不能覆盖旧前缀。包内backend/是真实release7py，不需要找原仓库。

```sh
# 零Docker新source/receipt副本来源检查：APP本地路径也明确传原/root路径；若在Mac先检查，REMOTE_IMPORT_PATH仍为APP真路径而非Mac路径。
python3 -B "$KIT/backend/check_inputs.py" --old-packet "$OLD_PACKET" --authorization "$AUTH" --ca "$CA" --source-manifest "$APP_SOURCE_MANIFEST" --bundle-manifest "$APP_BUNDLE_MANIFEST" --import-receipt "$NEW_IMPORT" --import-observation "$NEW_IMPORT_OBSERVATION" --remote-import-receipt-path "$REMOTE_IMPORT_PATH"

python3 -B "$KIT/deployment/sequence/cohort_maintenance_v3.py" --mode apply --root-admit-maintenance --backend-tools "$KIT/backend" --old-packet "$OLD_PACKET" --accounts "$ACCOUNTS" --authorization "$MAINT_AUTH" --new-authorization "$AUTH" --ca "$CA" --source-manifest "$APP_SOURCE_MANIFEST" --bundle-manifest "$APP_BUNDLE_MANIFEST" --import-receipt "$NEW_IMPORT" --import-observation "$NEW_IMPORT_OBSERVATION" --api-container "$API_ID" --expected-api-image-id "$EXPECTED_API_IMAGE" --output "$NEW_MAINT_OUTPUT"

python3 -B "$KIT/backend/host_runner.py" --api-container "$API_ID" --expected-api-image-id "$EXPECTED_API_IMAGE" --discover-maintenance-gateway --old-packet "$OLD_PACKET" --accounts "$ACCOUNTS" --authorization "$AUTH" --ca "$CA" --source-manifest "$APP_SOURCE_MANIFEST" --bundle-manifest "$APP_BUNDLE_MANIFEST" --import-receipt "$NEW_IMPORT" --import-observation "$NEW_IMPORT_OBSERVATION" --output "$MATERIAL"

python3 -B "$KIT/deployment/sequence/rotate_current.py" --material "$MATERIAL/material.PUBLIC.json" --backup-dir "$ROTATION_BACKUP"
# root核created/infra-ready真实新ID后才执行，不能用模板ID：
docker --context default start "$NEW_CONSUMER_ID" "$NEW_SCHEDULER_ID"
# 等健康并核all-ready snapshot后：
python3 -B "$KIT/deployment/sequence/observe_full_scan.py" --api "$API_ID" --rotation "$ROTATION_BACKUP/rotation-with-time.PUBLIC.json" --material "$MATERIAL/material.PUBLIC.json" --output "$SCAN_OUTPUT"
```

maintenance未知结果应保留并用同入口--mode inspect --previous原输出（其原inspect守卫保留），不能再apply强行重跑。所有backend/core pins从5c874a32真实RELEASE计算；旧packet SOURCE90b只是来源，本轮auth/source/bundle/image必须全是bcec。永久SSH不代表永久业务token，原业务session/horizon/自然过期检查不变。未知/失败停止串联、保留前缀，root立即告知用户是否可停机，不自动创建后继运行。
