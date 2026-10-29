# 356f source-aware producer：只本地工具冻结

仅支持root冻结产品`356f29983c904e949245aedfad464efc1bf7b63d`；本目录是新副本，历史neutral-r30、neutral-r30-cas、运输/旧四会话/失败prefix不改。18运行件仍name→sha/file_sizes；9个.py必须与manifest声明集合完全相同，验证/派生脚本只在tmp752。F fixture不另造第二套工具，交部署fixed admin动作按下面schema实现。

已核并原字节复制实际CI两manifest：source `50684876e08d74e8579e99b30cd3f53b676f5e4367cadbc3bfa610714ce6b088`；bundle `1ddafb7aaa1c552172cc5a0c0f48881412a8fa1fabbb400037854f4bba77a6a2`。实际context94/runtime60是字段实测，本程序不写死这两个数。BUILD_UNAPPROVED profile原SHA `c394542e393879b25042de9deee9c2263ec2ab003db8c916e21425d03f9c2f44`，root_approved=false、actual_loaded=false原样保留；不是新授权或APP已导入。

backend config=`sha256:a3f4bf81c8275dc949a91485097cb210a06f3880b5476cb05dfd2f98018d192d`。LOAD **config**=`sha256:3c4d812a6efe003770aafbdba65f9c1960ba8234ab23a133934205a70bdcda77`；既有VM Docker29 actualId/descriptor4f是同一原镜像的另一身份，不能混作config或推断换图。classic/OCI proof按精确字段逐链核，不做json substring。source/bundle/rootmanifest别名/锁/archive标签/原fileprobe SHA及完整repo相对path/bytes/mode/SHA逐项匹配。

纯数据批准边界：部署提供原BUILD_UNAPPROVED profile，root独立核实际build后**另写新批准副本**，不改原件。批准副本需root_approved=true，保actual_loaded=false，并添加实际新PUBLIC `qa_adapter_sha256=15b91449627218b011fff0768b1f84fe2e9274ec06c0486fd28f2ae9dce03f5d`及`qa_approval_receipt_sha256`；后者尚未给定，不能填旧0b批准。plan.source_profile={path:'/neutral-input/source-profile.PUBLIC.json',sha256:新批准副本原SHA}。plan原source/两manifest/counts/images/public_tool_approval必须逐值匹配profile，不能用新profile跳过它们。未批准/null/TBD/旧source/不匹配在任何client/输出/业务动作前拒绝。纯`check_source_profile_facts(profile)`只校本地事实、不批准；实际入口必须经`load_source_profile`原SHA+true门禁。

APP固定runtime preflight：官方**新backend** alias/config（实际GEN绑定），edge-only、UID10001/read-only/drop caps、无DB/AMQP业务env、保镜像PYTHONPATH、不加-I：

```sh
python -B /neutral-code/escalation_readback.py --check-runtime-only --plan /neutral-input/plan.json
```

仅解析真实t44 validator/rules，报告expected target，不冒充image/APP已导入。admin/HTTP原CLI不变：同plan的profile原件RO挂上述固定路径；GEN原件仍`/neutral-input/binding.json`。raw GEN project/database/source/G、CA/IP、预算9e原probe与锁内readmission、角色/版本/事务/幂等/TTL门禁保留。退役r30window01拒绝。生产权限入口仍root已审9e持真实锁的固定wrapper，直接admin的flag不授权。

实际APP import必须另给原receipt：kind final-backend-web-import-v1、真实source/两manifest、backend/web完整identity proof、10001/package_origin=/app/backend/t44/__init__.py/无业务env/全runtime记录；原observed_utc必须等plan.actual_loaded_observed_at，不能改旧receipt时间。images_loaded_this_observation可真或假（新prove-loaded不重新load），但必须真实bool。F后P重新观察可产生新原件，旧件/prefix保留。

assemble输出仍五件原名。session schema改为`NEUTRAL_753_INPUTS_V1`，identity由新profile写入；core81e/冻结OpenAPI不变。bindings仍canonical(packet除binding字段)+真实末尾换行之SHA；只写新目录，created/expires真实，不retime。运输由部署新356/753薄policy接手，旧0b/C10:40运输不可直接重放。

18文件manifest纯数据重派生（输出必须新文件，不覆盖已审原件）：

```sh
python -B tmp/752_backend_profile_final_20261029/derive_manifest.py --producer-dir /实际新18件目录 --output /实际新manifest.PUBLIC.json
```

当前manifest已包含实际CI两manifest，profile/QA批准和APP实际import均外部输入；后续如仅批准profile变化，无须改18代码。若目标manifest实际字节变动，先再派生新code manifest并让root/部署核新SHA，不能默换内容沿旧hash。

F仅按已发表NEUTRAL_IO_CONTRACT/FUNCTIONAL_ENVIRONMENT：部署正常CLI有限7账号见F_ACCOUNTS模板，逐个原user_id前缀0600保留。正常API manager登录→新F项目→addProjectMember：devA[2,3]、devB[2]、reviewerA/B[3]；manager只1，outsider绝不入项目。CLI F-only service仅实际F项目escalation:write；disposable另签独立可logout会话，expired允许F-only service真实TTL60并实际等待到期，保原expires，human特有过期仍未执行；login_only凭据专用。不得调用P admin.service生成短期expired会话、借P四会话、改DB/旧expires或停P组件。最终F PRIVATE env按已发表753 exact keys，真实6不同user_id/username，service无human字段按实际可null；可选未提供删键不填假值。F动作归部署fixed动作，不由此程序执行，F/P作用域完全隔离。


## LOAD legacy字段小修（97b9f3fa旧包保留、不可用于753）

旧97误把config3c写入packet.identity.load_runtime_image_config_digest，实际753 PUBLIC ADAPTER/TARGET该legacy同名字段要求**runtime Docker ImageID4f**。新生产profile必须另外包含`load_python_expected_runtime_id=sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1`和`load_python_identity_projection_sha256=ce562c117428face0b421e06b33c361b291cab26d8d3a51d24484dbd0841da2a`；原load_python_config_id保持3c，不混回同值。plan.images.load_python仍为config3c；assemble只将legacy packet字段映射expected runtime4f。

18件中的TARGET_753模板纳入精确旧PUBLIC投影的load.roles.python引用、原SHA、当前753 adapter/target模板引用；仅官方Python身份事实，不用其中旧APP结论当新产品，fresh_live_recheck_required=true。root批准副本必须同时匹配CI config3c和原OCI projection.actualId4f；启动前部署/QA仍须鲜活actual inspect/fullproof同链，不把历史投影当当前运行就绪。原BUILD_UNAPPROVED c394及CI两manifest都不改。

新增跨owner回归直接读取真实c394 build profile、ce562旧PUBLIC Python投影、sha15b公开ADAPTER的LOAD常量和TARGET_PROFILE_753.template字段，评估真实assemble身份构造表达式；红3c!=4f原件保留，修后连同原metadata负例43项0.36s绿。未stub QA/core，也未读任何PRIVATE/cases。旧39ba manifest另存LEGACY_FIELD_UNSAFE原字节，新的18manifest另派生，不能沿用旧hash。
