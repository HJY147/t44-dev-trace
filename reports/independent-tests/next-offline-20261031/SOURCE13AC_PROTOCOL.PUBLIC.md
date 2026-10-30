# p14 中性输入协议确认（仅模板，不是准入）

已冻结v5.2可接受新source13ac及其新source/bundle/import真实原件，不存在将source固定为90b的分支。原正向合成prepare就是exact13ac；本次补8项针对性负向检查：旧90b source、把packet legacy runtime字段误填新core、错误OpenAPI、错误packet版本、source/bundle/import原始字节变化，以及重新绑定hash但receipt.source_sha仍为90b，全部拒绝。测试只用合成会话与CA替身，无网络、Docker或SUT，没有新增产品断言或改动冻结工具包。

候选标识暂定：QA r30manualp14、material r30materialresume08、maintenance r30restoretransition08、W=/root/t44-final-20261031/QA753_NEXT_V52。schema/campaign沿用原隔离库是总协调规划信息，尚未核实当前库及排他事实。以上均未执行；标识还须现场核不存在、未消费及不覆盖。

## 五件原始输入（opened/inputs）

|文件|必需内容与绑定|
|---|---|
|session.private.json|schema=NEUTRAL_753_INPUTS_V1；run_id=r30materialresume08；新created_at/window、environment、四真实sessions、当前完整inventory、fixture_sha256/counts、loaded_receipt_sha256/reference、identity、binding_sha256；新nonce及maintenance/schema/campaign等中性补充一并封入新物料并纳入binding。禁止公开token。|
|ca.pem|真实CA PEM原字节SHA等于packet.environment.ca_sha256；origin严格https，无userinfo/query/fragment，路径空或/，connect_ip须私网。adapter只解析CA，不能证明当前服务证书真实有效，后者仍需中性证书事实。|
|source-manifest.json|原字节SHA等于独立profile.source_manifest_sha256及packet.identity同名字段；内容与真实source13ac/实际镜像映射需独立审核。不能重命名旧90b原件。|
|backend-bundle-manifest.json|原字节SHA等于profile及packet.identity.backend_bundle_manifest_sha256；真实bundle/source/config关系须独立审核，adapter不自动验证manifest内部每个产品文件。|
|backend-import-receipt.json|原字节SHA等于profile.backend_import_receipt_sha256、packet.loaded_receipt_sha256与loaded_receipt_reference.sha256；内部source_sha必须为exact13ac，source_manifest_sha256及bundle_manifest_sha256必须分别等于profile，identity嵌套值必须包含实际APP config digest（有或无sha256:前缀）。真实七角色映射及实际导入事实需中性原件另审。|

五件整文件SHA另在运输manifest/独立审核记录绑定，其中session.private.json整文件SHA不要混同其内部binding_sha256。packet.binding_sha256计算为：去掉binding_sha256字段后，用ensure_ascii=False,separators=(',',':'),sort_keys=True,allow_nan=False序列化为UTF8并加一个换行，再SHA256。任何增加nonce/维护/schema补充字段也须先纳入此计算。每个输入受16MiB读入上限。

## profile与packet的双runtime字段

TARGET_PROFILE.runtime_sha256及实际grant.runtime_sha256必须为新v5.2 core 9cf747e308969ceba37e2cfcfa6591def45e118ad928c4f310f57b6ecf37542a。

NEUTRAL_753_INPUTS_V1沿用的packet.identity.runtime_sha256必须为81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf，这是运输协议历史常量，不是90b产品source，也不允许执行旧runtime。packet.identity.git_commit必须为exact13ac；source/bundle/SUT config/LOAD binding/OpenAPI均须等于新profile。source13ac搭配全新原件和新packet可通过；旧90b packet仅改material名仍在TARGET_git_commit或ACTUAL_IMPORT_source_sha拒绝。

LOAD字段load_runtime_image_config_digest按冻结adapter既有常量精确匹配sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1；字段命名不能代替实际镜像descriptor→config映射，现场仍单独核真实镜像身份。

## 当前会话与库存

sessions精确四角色manager/developer/reviewer/service；每个真实token、user_id、expires_at、project_ids，service.scopes包含escalation:write。全部expiry严格晚于审核时刻+900秒，准备/执行各重新核。inventory.schema=772-inventory-v1，captured_at非未来，rule_version当前；400个client_id恰为0..399、至少35项目、800个互异任务；transition_task.state=2且owner=developer，计划终点超过审核时刻+900秒+86400秒；escalation_task非6/7，既有event的task/project/schedule/rule绑定一致，四角色覆盖每项目。

请交真实完整Task快照，不只裁剪adapter最低字段：原runtime使用version、schedule_version、delivery_cycle、review_cycle、iteration_id、owner_id、title、description、plan、latest_review_id、approved_review_id、approved_assessment_id、approved_assessment_version、artifact_revision、created_at、escalation_count及阻塞字段等；event须完整id/task/project/schedule/rule/level/recipient_ids。独立岗按冻结OpenAPI验证。adapter的零SUT准备成功不证明快照与当前DB一致、后置断言完成或MQ送达。

## default false模板与后审边界

同目录TARGET_PROFILE.TEMPLATE.PUBLIC.json、APPROVAL.TEMPLATE.PUBLIC.json和PACKET_IDENTITY.TEMPLATE.PUBLIC.json均为无效占位模板：approved=false、所有执行标志false、无观察时间/nonce/真实SHA，不可直接复制到W/public当批准。adapter需要approved=true的真实独立身份审核才能prepare，但该真实审核以后仍限IDENTITY_ONLY_FOR_ZERO_SUT_PREPARE，functional_authorized/benchmark_authorized/grant_allow全部false；本次没有签发该审核。实际profile精确原字节SHA与当前adapter SHA由APPROVAL绑定。

以后新身份审核完成后的零SUTprepare入口为：
```sh
sh "$W/public/ENTRY_MANUAL_753.sh" prepare "$W" r30manualp14 "$FRESH_PACKET_OPENED"
```
本轮未执行；它只在network none容器核文件/CA/库存/会话并产生environment.json及grant.default-false.json（allow=false），不访问SUT。回收公开PREPARED_DEFAULT_FALSE回执、environment精确SHA、完整default-false及SHA、五件SHA/内部binding及现场中性资源/排他/证书/fixture/schema补充证据；不回收token给协调者。

新nonce、maintenance/schema/campaign、七角色真实性、资源排他等不是adapter内置必填门禁，必须由独立当前审核补充绑定，不得因prepare成功就宣称全部核实。旧grant/material已消费，旧packet window不能改名为新窗口。真正新packet必须来自当前原件和新会话，保留其真实provenance。允许一次执行仍需以后用户授权及独立fresh default-false审核；当前无真实target/profile、nonce或allow=true。
