# P09 数据保留后的真实中性材料刷新

本地实现及13项离线测试完成，**尚未远程运行或验收**。不改source90b产品代码、QA测试或旧P09原件；不seed、不新建400任务、不执行transition、不发压、不控制VM。

旧`r30-http-prepare.py`/`prepare_http.py`会创建400个任务，旧`assemble.py`/GEN包装器受旧window/budget约束，均不是本次恢复入口。此helper以新的显式material-preparation授权进入**原API容器**，使用它原有Settings/数据库身份；host不读取、导出或打印API的DATABASE_URL。它不是旧GEN预算的成功readmission，也不声称已做当前资源准入，协调者须另外保存实际七角色/LOAD资源和排他证据。

## 脚本边界

- `host_runner.py`：APP主机root明确调用；校验原packet绑定、新授权、指定API容器owned项目/api角色、**实际image ID**和90b revision。敏感输入只通过docker exec stdin，不放argv；API stdout/stderr全部捕获到APP私密文件，不回到Mac或云助手控制台。
- `refresh_runtime.py`：运行于现有API容器，Settings实际database必须匹配P09。原`python -m t44.cli service-token`为**同一个现有服务账号**签发新token，并读回auth_sessions真实hash/expiry/scope；manager/developer/reviewer走原HTTPS `/auth/login`，再校验持久会话和各自真实GET项目scope。每次签发的私有前缀立即flush到host捕获文件，后续失败也不伪装回滚成功。
- `runtime_support.py`：TCP显式连接packet的private connect_ip，TLS SNI/Host/证书hostname使用原origin，不关闭CA或hostname校验；在任何签发前先完成握手。实际`GET /projects`逐项目核`my_roles`冻结枚举1/2/3，再读取同一800 task/event/rules/空依赖及稳定升级级别。
- `process_guard.py`：容器内只读审计唯一nonce对应的PID/PGID/startticks状态和同库flock，缺状态/活跃组/不确定均不是退出证明，不杀其他进程或读Env。
- `refresh_core.py`：采用实际GET的原400client/800任务ID、现有event/rules和真实计数，检查当前transition state2/owner/未来计划、空依赖、稳定升级级别/版本、四会话覆盖从构包时起900秒。资格不符即拒，绝不改inventory状态、expiry或计数凑通过。重新计算fixture SHA及新packet binding；旧packet/run/window保留为provenance。

新packet的window只记录**本次构包观察时刻及900秒材料区间**，不是预设 benchmark S，不等待或追赶它。manualV4在用户实际触发时重新核真实会话并记录actual_trigger。正式400并发、60秒预热、600秒稳态、15秒请求及40秒postcheck、P95/吞吐/业务错误断言完全不变；本helper不产生grant。

## 恢复后由协调者在APP本机执行

先确认仍为原P09数据、源90b的实际API image ID、当前资源与排他性；不要提前开64核等本地排障。将五个Python脚本经SSH/SCP传到APP无敏感代码目录，例如`/root/t44-manual-input-tools/`。只传代码和未批准模板，不从APP复制账号/token/DB凭据到Mac。

账号实际位置按旧`P-accounts/completion.PUBLIC.json`的`output`核定；原wrapper契约通常是`P09/P-accounts/output/accounts.initialized.private.json`，不是`output/result/accounts.json`。原中性packet通常是`P09/P-packet/output/packet/inputs/session.private.json`，以旧PUBLIC完成收据为准。

在APP主机生成一份新的授权文件：从`authorization.TEMPLATE.json`填写旧packet原字节SHA、新material run ID（不得等于旧packet run或未来QA run）、新64位hex随机nonce；实际核对后root设`root_approved=true`。不复用旧budget receipt，不填旧S或新的预设启动日期。该授权只允许列出的会话签发和只读资格/计数，以及构包；不授权种库、任务变更、scheduler操作或压测。

```sh
python3 /root/t44-manual-input-tools/host_runner.py \
  --api-container ACTUAL_OWNED_API_CONTAINER \
  --expected-api-image-id sha256:ACTUAL_PINNED_64_HEX \
  --old-packet /root/t44-final-20261029/P09/P-packet/output/packet/inputs/session.private.json \
  --accounts /root/t44-final-20261029/P09/P-accounts/output/accounts.initialized.private.json \
  --authorization /root/t44-manual-material-authorization.json \
  --ca ACTUAL_ORIGINAL_CA_FILE \
  --source-manifest ACTUAL_ORIGINAL_SOURCE_MANIFEST \
  --bundle-manifest ACTUAL_ORIGINAL_BUNDLE_MANIFEST \
  --import-receipt /root/t44-final-20261029/P09/backend-import-receipt.PUBLIC.json \
  --output /root/t44-final-20261029/manual-material/r30materialresume01
```

三个`ACTUAL_ORIGINAL_*`文件须是P09 packet附带的原字节，并与原packet SHA绑定。输出目录必须全新；失败前缀保留，不能覆盖或把失败当准备通过。API容器内必须实际存在GNU coreutils `timeout`（先只读probe，不存在即拒绝，无无界fallback）。执行由该容器内监督器按实际启动起300秒、TERM后5秒KILL约束整个维护进程组；同库flock拒绝并发刷新，nonce状态记录PID/PGID/startticks。host本身330秒超时并不能证明容器进程已停；无论成功/失败都另行执行只读process_guard，保存`process-state.PUBLIC.json`。只有进程组确实无活跃成员且同库锁空闲才释放新五件；否则返回`MATERIAL_EXIT_NOT_PROVEN_NO_PACKET_RELEASE`或超时状态，禁止后续prepare/压测，保留私有前缀。这里没有对任何未来benchmark设启动截止。

## 明确的APP输出与后续传输

- `.../manual-material/r30materialresume01/inputs/`：五件均以0600新建，包含`session.private.json`及`ca.pem`、source/bundle/import四件原字节。**整个明文目录只留APP/最终LOAD，不能回Mac或控制台。**
- `.../runtime.stdout.private.jsonl`、`.../runtime.stderr.private.log`：0600私有捕获，包含签发前缀和最终真实材料，root不手工查看token。
- `.../service-cli.original.private.json`：原CLI新服务凭据原字节、0600，只供APP内scheduler凭据轮换。
- `.../material.PUBLIC.json`以及host stdout：只有路径、SHA、当前计数、issued/expiry/scope、请求数量、容器身份等中性元数据；明确`external_writer_absence_proven=false`、`scheduler_token_refreshed=false`，不冒充已完成这些检查。

部署岗应在APP使用LOAD公钥新建本轮密封运输，只将cipher+PUBLIC metadata经Mac/SCP传给LOAD，在LOAD用它原私钥恢复这五件，再运行manualV4新W的prepare。旧relay和旧790 cost_stop已经是历史，不能改旧C或重放一次性旧fetch。新packet的runtime identity仍保留原上游core81e046…；manualV4 target/grant/runtime使用其新core3da347…，不混填。

## Scheduler真实凭据轮换（单列，helper不自动执行）

source90b的`backend/t44/scheduling/__main__.py`将`lambda: read_token(...)`交给Scanner，Scanner每次使用时重新读；部署factory默认挂载整个`scheduler-secrets/`目录到`/run/t44-secrets:ro`。恢复后先实际核其mount、进程UID/路径和旧凭据有效性。若需轮换，在APP中备份旧文件至root私有目录，按`material.PUBLIC.json`给出的原CLI新凭据SHA验证新文件，然后在**实际同一被挂载目录内**用临时文件+原子rename替换`scheduler-token.json`，赋实际读取UID（标准为10001）和私密权限。不要把token打印或拉回Mac，不要复制新expiry字段伪装轮换。

默认目录挂载和token-provider设计通常无需重启；若现场实际是单文件bind mount，rename可能仍指向旧inode，不能套用该结论，应由部署岗精确处理。随后观察真实持久扫描结果/错误与新会话主体，验证实际成功读取和使用；仅running不是成功。不要为了验证手工制造业务升级写入或并发启动另一个scanner。

## 本地验证及尚需live验证的项目

`python3 -B tmp/746_backend_manual_inputs/test_refresh.py`：7项通过，覆盖旧window保留/新binding、真实expiry不足、当前任务state/owner、原800 ID/计数/source原件变化、授权范围，以及fake Docker执行下敏感数据只经stdin/APP私有捕获、公开stdout与argv不含模拟凭据。`python3 -B tmp/746_backend_manual_inputs/test_runtime_support.py`另6项通过：严格TCP-IP/SNI分离及CA/hostname、证书失败、真实HTTP mock逐项目my_roles校验、560次GET的400client读回loop/变更依赖拒绝、残留孤儿进程组/同库锁拒并发。五个脚本通过Python3.10 AST。没有启动VM、连接SSH、Docker、MySQL、API或QA。

仍待live：实际账号/packet路径、64核及LOAD资源/排他、指定API image ID、原API环境DB身份、API容器到原HTTPS origin的网络与证书、800任务资格和原事件仍有效、真实TTL覆盖、scheduler轮换及成功扫描、APP密封→LOAD恢复、manualV4 prepare/defaultfalse→独立一次grant。任何失败应带公开错误码交责任岗，不自动重造数据或降低断言。


恢复现场若API仅有internal桥、不能回到宿主VPC映射端口，可显式增加`--maintenance-gateway-container ACTUAL_ID --maintenance-connect-ip ACTUAL_SHARED_GATEWAY_IP --maintenance-connect-port ACTUAL_TLS_INTERNAL_PORT`。host会核唯一同owner TLSgateway、同NetworkID/IP及内部端口映射回原origin端口。只有准备HTTP的TCP目标改变；原origin作SNI/Host、严格CA，以及新packet给LOAD的VPC origin/connect_ip均不变。此项为root报告的现场网络适配，2个新mock通过，未由本agent远程验证。
