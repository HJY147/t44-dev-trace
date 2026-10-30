# 本地原工具准备

候选QA=r30manualp13；material=r30materialresume07；maintenance=r30restoretransition07。现有p13 PUBLIC字节及400/60/600/P95≤270ms/每分钟≥1000/零业务错误和原全部断言不变。模板均未批准，不可直接作为原工具输入。

实际完成：原manifest SHA核对和全部6项工具/密钥字节核对；ENTRY/ADAPTER SHA核对；原V4 capsule用原transport key解封成功，原capsule工具检查cipher/archive/全部文件hash。原p11密封备份用原backup key和原verify_backup验证cipher SHA/长度、认证链、footer/压缩流、全部31文件hash并与原receipt对齐。没有解压落盘、阅读业务结果或重判历史。

原runtime成功导入，标准库依赖可用，400/60/600常量一致；ADAPTER和verify_backup --help成功。runtime原CLI没有--help，该尝试返回usage并exit 1，已澄清而未修改。其offline-check/timer-gate引用的辅助脚本不在冻结manifest内，本轮未运行、未补造；正式入口仍是原ENTRY execute。

原字节工具、密钥及实际检查日志保留在本岗独立PRIVATE，不随公开包分发。原backup key、transport key、runtime和verify_backup均已实际使用，无此类缺件。未验证云端Linux/runner安装；本机不能替代LOAD环境。

## 精确准入结构与待填字段

TARGET_PROFILE_753.UNSIGNED.template.json保留原753-target-profile-v1全部键；固定runtime_sha256/openapi_sha256/load_runtime_image_config_digest/manual_start_protocol不可改。其余源提交、源/bundle/import SHA、SUT/web/LOAD实际image/config ID、APP及LOAD观察UTC必须由本轮原件填入，不能继承旧值。actual_loaded=false直到独立审查真实导入/加载证据。APPROVAL模板approved=false，scope=UNSIGNED_TEMPLATE_ONLY；独立审核后才绑定目标准确字节SHA、源、ADAPTER SHA及issued_utc，scope限定IDENTITY_ONLY_FOR_ZERO_SUT_PREPARE，所有执行许可保持false。

schema-supplement模板沿用原t44-schema-supplement-current-neutral-v1：runtime_source、database、current_observed_utc、current_schema_fingerprint_sha256、current_index_layout_sha256；files及five_input_binding逐项{bytes,sha256}；transport_receipt_sha256、runtime_material_public_sha256和本轮链标识。所有null必须填真实原件；保留旧迁移before/after/SQL/stdout的原字节，另收本轮current-schema。不得把历史采集UTC改名成当前。DDL/字段/持久化契约的冻结v1.2语义比较须独立审查，原V4不内置此补充验证。

原ADAPTER实际opened结构：opened/inputs/{session.private.json,ca.pem,source-manifest.json,backend-bundle-manifest.json,backend-import-receipt.json}。session.private.json schema=NEUTRAL_753_INPUTS_V1，run_id为material且不同于QA；created_at真实UTC；identity七键git_commit/source_manifest_sha256/backend_bundle_manifest_sha256/sut_image_config_digest/load_runtime_image_config_digest/runtime_sha256/openapi_sha256。packet.runtime_sha256是原兼容身份81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf，工具runtime则为3da34780a224bb3a9462e750f1cae9af316bab3ef457d75c8e0c2f2dcd7df339。

原packet还需binding_sha256（排除本字段后原enc：sort_keys、compact UTF8、末尾换行）、loaded_receipt_sha256/loaded_receipt_reference.sha256、window的start_utc/end_utc/cost_stop_utc、environment的origin/connect_ip/ca_sha256、sessions四角色manager/developer/reviewer/service、inventory、fixture_sha256、counts。secret仅PRIVATE。原验证器要求会话真实到期>当时+900秒、service escalation:write、400 client_id=0..399、800不同任务且至少35项目、项目范围及实际任务/升级资格，不能只检查JSON形状。

现场必须补齐七角色实际容器/image/config/health/源/导入原件、APP/DB/LOAD资源预算和排他/无旧运行、LOAD原runner及installed工具hash、p13 run/result/phase/history不存在且未消费、当前schema、会话/fixture/TLS、云盘ID及PL1/40GiB/3800IOPS与MySQL卷→nvme0n1p3→唯一40G parent关联。两份APP历史原件和五份schema历史原件只作provenance，历史SSH到期与scheduler health不证明下轮状态。

## 原入口和检查调用（当前不执行）

新收件完整性辅助程序不接触工具/云/SUT，不替代独立审查：

```sh
python3 CHECK_INTAKE_PUBLIC.py /independent/current/schema-supplement.PUBLIC.json /independent/current/evidence /independent/current/opened/inputs
```

仅检查链/字段/逐文件字节，不能证明事实新鲜性或语义。未填模板应拒绝。审查完成、真实身份签发后才可使用原绑定检查：

```sh
python3 /root/t44-manual13-public/PREPARE_REUSE_753.py --workspace /root/t44-final-20261029/QA753MANUAL10 --identity-dir /root/t44-manual13-identity --packet-opened /root/t44-material-r30manualp13/opened --check-only
```

--check-only仅核公开绑定/新路径；不验证packet/installed工具。真实prepare去掉该标志，必须在后续明确窗口和身份准入后；当前两者都不运行。prepare产生default-false grant，原ISSUE_ONCE在独立当前证据审查后才可签一次性grant；原execute/seal命令沿用原READY_INTERFACE.PUBLIC.md，不自动重试/后继。

未来backup先核cipher SHA/长度与原receipt，再由独立PRIVATE调用已验证原工具（目的目录必须不存在）：

```sh
python3 /independent/PRIVATE/frozen-tools/verify_backup.py /independent/PRIVATE/r30manualp13.753backup /independent/PRIVATE/frozen-tools/backup.key --extract-dir /independent/PRIVATE/recovered-r30manualp13
```

另将返回compressed_tar_sha256和files与receipt核对。完整性不等于性能通过，原始结果由本岗独立处理，只发布PUBLIC cohort/性能/独立结论。

实际提示词ROLE-testing-P13-LOCAL-TOOLS-20261031-v1：限定原工具本地可用性及空白接口，未产生测量用例或当前批准。
