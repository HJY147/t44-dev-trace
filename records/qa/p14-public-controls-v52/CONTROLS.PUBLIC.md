# p14/v5.2 PUBLIC控制接口

仅离线接口交付；当前无真实身份/nonce/环境准入或grant。原400/60/600、阈值、业务/审计/后置断言均不改。新INSTALL密文包仍保持原hash，不因增加本PUBLIC目录改变。

|旧包装|兼容结论|
|---|---|
|OBSERVE_PHASE_PUBLIC_753.py|可原字节复用；workspace/run为参数，只读白名单phase及trigger。已复制并核原字节一致。RUNNING400仅表示栅栏释放，不证明400同时HTTP、当前alive、稳态完成或性能通过。|
|SEAL_753.sh|不可复用：容器检查硬编码p12；原inspect错误被吞并不能证明安全。新SEAL_P14_V52.sh明确p14、全producer/writer停止声明、Docker枚举失败即阻塞；容器内核新manifest及全部工具/key SHA后调用本W/private_tools/backup.py。|
|ISSUE_ONCE_753.py|不可复用：run硬编码p12，且无v5.2 core/adapter/manifest/source绑定门禁。新ISSUE_ONCE_P14.py固定p14/material08/source13ac与新工具hash、保留原资源与400/60/600、15秒请求/40秒后置/900秒上界，只允许原default-false的allow改变。|
|PREPARE_REUSE_753.py|不要装入新kit：仍是旧p12旧工具绑定。使用已交新ENTRY的prepare入口，必须在当前独立身份审核完成以后。|

## 观察（以后现场允许时）
```sh
python3 OBSERVE_PHASE_PUBLIC_753.py /root/t44-final-20261031/QA753_NEXT_V52 r30manualp14
```

## 一次issuer（仅独立测试岗，当前不得签发）

新脚本默认仅验证，不写文件：
```sh
python3 ISSUE_ONCE_P14.py grant.default-false.json independent-decision.json
```
真正当前独立审核与用户授权均完成以后，独立岗才可加`--issue-after-current-review NEW_GRANT_PATH`；`xb`拒绝覆盖，输出只改allow。当前没有任何实际approved decision或allow=true文件。

decision需包含：status=INDEPENDENT_CURRENT_NEUTRAL_REVIEW_APPROVED_ONCE，run_id=r30manualp14、material_run_id=r30materialresume08、default_false_sha256、environment_sha256、source_git_commit=exact13ac、source_manifest_sha256、tool_manifest_sha256、qa_adapter_sha256、current_actual_app_config_digest、nonce、neutral_binding_sha256、current_schema_fingerprint、reviewed_utc、minimum_real_session_expiry、latest_trigger_before_utc，及脚本REVIEW的9项全部true。所有值必须来自真实审核，不能由协调者填写为已审核。模板默认DRAFT与false。nonce须新生成且不可预测、未消费，独立核物料；脚本的长度检查不代替该事实审核。实际触发严格早于latest_trigger_before_utc，且该上界≤最短会话expiry−900秒；身份/输入/资源/排他变化全部失效。

## 封存（运行退出且所有producer/writer真的停止后）
```sh
sh SEAL_P14_V52.sh /root/t44-final-20261031/QA753_NEXT_V52 r30manualp14 /root/t44-sealed-p14/r30manualp14.753backup EXITED_ALL_PRODUCERS_AND_WRITERS_STOPPED
```
输出父目录须已存在，路径须在W之外，密文及receipt均不得存在。最后一个参数是操作者真实声明，覆盖执行容器、所有producer/后台writer及operator-channel/evidence-neutral写者；脚本不能自动证明外部写者全部停止。它会拒绝目标容器非exited/dead状态，核本W实际result.writer_finalized=true，并在network none只读W容器核新manifest/全部工具（含新backup.key）SHA后执行本W的backup.py。root不读工具/key内容，仅搬密文及同名.receipt.json。封存失败留证、不覆盖/不重试；不能将创建备份当内容验证通过。

独立岗本地用本轮新backup key与verify_backup.py核cipher bytes/SHA、认证解密/压缩流/全文件hash，再用新verify_raw核raw/footer及原业务/后置断言。旧key或旧p13 PRIVATE不参与。新包备份器64GiB密文上限保持原字节；要提前核W全体内容/备份/运输副本磁盘预算。封存容器2CPU/2GiB/64pids与旧接口一致，未在真实Linux/容器下验证。

本次6项本地控制自检通过：历史时刻合成验证仅检查default-false；当前时刻拒绝已过期合成decision；旧run/core/改变400/600或allow=true全部拒绝；DRAFT在python -O下仍拒绝且未创建输出；observer只投影白名单不读PRIVATE结果；seal错误参数在Docker之前拒绝。shell语法/Python AST通过，未执行真实Docker/封存/任何grant输出。
