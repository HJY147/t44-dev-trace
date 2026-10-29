# R29 开机前/开机后顺序

仅是执行接口，未在云端运行。原f7镜像复用不免除实际复核；固定截止12Z不表示可持续开机到12Z，云计算窗口由根限制为约一小时。

## 一次安装

APP/LOAD分别执行本目录 `install-via-github-api.PUBLIC.sh`，完整脚本5228B，SHA `d5546d0f2bcbd19c24a5648d7b089ed6dd9ecd2ae3bd43fae5d199da81361bf0`。它是完整POSIX sh脚本，直接发送；不得再按“只内层”漏算全文或双重包装。固定源commit `f1fff60facc1e10378164e4b79c4d9c2894ba326`，单次API下载公开code bundle 64819B/SHA `0f2aef008a8cbf69fdfaad27a59eea85a3b5c149301a4018aa064ca4d76bd6c1`。20件代码/manifest全部核验后才排他写入。成功末报kind为 `R29_EXACT_PUBLIC_CODE_INSTALLED`、installed_files=20、SUT_or_sessions_or_services_started=false。任一目标已存在就拒绝；不要自动覆盖/删目录。

| 对象 | 目标/摘要 |
| --- | --- |
| profile目录 | `/root/t44-r9/r29-code-01/profile` |
| profile.json | `5b0eef799680cbc30c5096d37b4fbffb32087add52410045e33842c972d4237a` |
| generation.py | `95802bf9e2a0d263bc00e1f2e5f046c553e29037e3c100eefebf09e81a95acc3` |
| resource-stream.py | `475c534dca91e9eeff9c64320d4b0d1a458faf6418ecc4efd408e9f56fdb3c92` |
| P64目录 | `/root/t44-r9/p790-r29-01` |
| manifest.json | `a5510d962deee65ace91a3fa7cf93d0c720e1cb08e4b841220b75e9cc082e590` |
| transport/790_transfer.py | `8600110b54f45240a6e45ea62c9be6f567529e374807d0ca593dde3fd7605db7` |
| MySQL budget helper | 原`305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d` |

原桥 `/root/t44-r9/scope-bridge-v3-01/manifest.PUBLIC.json` 须核 `e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7`；本包不改它，也不启其scope供应。

## 实际库存和新阶段

先在原两实例核停止状态/原盘/自动释放为空，再开机，核当前IP、原缓存镜像与工具原件；不复用旧进程PID/已过期授权。root报告原build binding `/root/t44-r9/backend-f7-build-01/upgrade-binding.json` SHA `df84e9b1dbcf8946209ae6ae0ea868d63dc96b60d01c2bae7f3d621e65b311b0`，实际backend镜像 `sha256:a7d3dde54efda1405bbd7d9f5f5b7c5a6439f1afd1dc8c50b2ed8b37625fa5da`。本岗没读原私有binding，只验证builder源码无时间字段。root必须重新观察实际对象，不能拿此表填不存在资源。

下列是新目录/新命名计划，未创建。`APP_IP`必须由根实际核验填入。保留legacy兼容编号 `r28p64gen04`，不要改成原正则不接受的r29前缀。

```sh
GEN=/root/t44-r9/r29-code-01/profile/generation.py
python3 "$GEN" prepare \
 --factory /root/t44-r9/campaign-935/p/controller.py \
 --upgrade-binding /root/t44-r9/backend-f7-build-01/upgrade-binding.json \
 --upgrade-binding-sha256 df84e9b1dbcf8946209ae6ae0ea868d63dc96b60d01c2bae7f3d621e65b311b0 \
 --source-package /root/t44-r9/source-f7-checked-01 \
 --source-manifest-sha256 3368534aececbb5441225e7859338aa3079b6e41798e38673bd8f337f8993577 \
 --original-proof /root/t44-r9/proof-v2-01/proof.jsonl \
 --image-proof /root/t44-r9/image-proof.py \
 --output /root/t44-r9/campaign-r29-01 --run-id r28p64gen04 \
 --app-ip "$APP_IP" --f-tls-port 22443 --f-http-port 18480 \
 --p-tls-port 22445 --p-http-port 18481 \
 --p-workers 64 --p-pool-size 5 --p-max-overflow 0 \
 --stop-utc 2026-10-29T12:00:00Z
```

逐条保存原始stdout、exit和stderr摘要。用实际prepare的phase/binding：arm→config→infra→probe-budget，infra只有MySQL/RabbitMQ。连接预算384只是规划，必须实际查询；迁移、bootstrap、idle、S1/S2使用本次实际budget路径+SHA，operation lock/核身份+max_connections始终保留。migrate数据库名必须是新实际库。bootstrap在idle/TLS401之前，以免正常auth audit污染空表门禁；明确seed44和04:00锚点。

```sh
python3 /root/t44-r9/p790-r29-01/790_bootstrap.py \
 --phase-dir "$PHASE" --binding-sha256 "$BINDING" \
 --output-name fixture790-r29-01 --anchor-at 2026-10-28T04:00:00Z \
 --manifest-sha256 a5510d962deee65ace91a3fa7cf93d0c720e1cb08e4b841220b75e9cc082e590 \
 --budget-receipt "$BUDGET" --budget-receipt-sha256 "$BUDGET_SHA" \
 --root-grant "$PREP_GRANT" --root-grant-sha256 "$PREP_GRANT_SHA" \
 --scope-bridge-dir /root/t44-r9/scope-bridge-v3-01
```

先用prep模板，实际字段和root明确admitted=true后才能造数；prep不准HTTP压力。bootstrap成功后才GEN idle，再核六角色running/0 restart、scheduler absent、本次CA/原产品53源。随后另签本次pressure grant、nonce；不能复用prep或28日grant。

## 会话之前预置完整传输和执行链

两侧安装/配置、LOAD收件密钥/APP公钥、资源采集与LOAD镜像、relay地址/nonce/CA与读取配置、消费者单次调用命令全部准备完并做无SUT合成传输。部署岗负责自动OPAQUE relay，仍调用原receive与consumer，禁止把非凭据resource marker当会话。

S1需新split名并用新pressure grant+budget。原S1 stdout是JSONL，保存原始字节后逐行解析，选择唯一 `kind=contrast790-s1-host-complete`；不要对多行stdout直接json.loads。即使外层解析失败，也不得重跑已完成的S1。

用templates填实际字段。APP配置里的python_image_id是原S2 host实际使用的官方Python身份；LOAD的python_image必须是原790_load允许的 `t44-official-python:`别名及其实际ID，不要把独立测试ec0镜像塞给开发短测。`transfer_sha256`必须取本次manifest，不能复制28日ba11/f89摘要。

LOAD先等唯一有效密文包，APP再发起一次producer/S2。原接收器CLI不变：

```sh
TOOLS=/root/t44-r9/p790-r29-01
python3 "$TOOLS/790_producer.py" --configuration "$APP_CONFIG" --configuration-sha256 "$APP_CONFIG_SHA"
python3 "$TOOLS/790_receive.py" metadata --configuration "$LOAD_CONFIG" --configuration-sha256 "$LOAD_CONFIG_SHA" --input "$METADATA" --input-sha256 "$METADATA_SHA"
python3 "$TOOLS/790_receive.py" part --configuration "$LOAD_CONFIG" --configuration-sha256 "$LOAD_CONFIG_SHA" --input "$OPAQUE_PART" --input-sha256 "$OPAQUE_PART_SHA"
python3 "$TOOLS/790_consumer.py" --configuration "$LOAD_CONFIG" --configuration-sha256 "$LOAD_CONFIG_SHA"
```

每片按实际part_count至多四片，receiver用JSON原片，不二次整体base64膨胀。S2数据真实session149KB等大小不是常量，不能按旧包猜；只搬ciphertext，不读密钥或密码/token。还原完整hash/尺寸和四角色实际有效期由原消费者检查。

330秒门槛针对control.stop_utc；600秒针对packet.created_at；sessions四个expires_at分别有效。它们与约一小时计算资源预算不是同一个条件。无效/过期停止并保前缀，不续会话/改TTL/悄悄重跑。80/800/8000是短开发诊断，不能替代400并发完整600秒验收。

完成后APP先seal、LOAD确认尾段完整再停镜像；保留原始数值、0/null、错误与SHA。最后GEN stop/status只停owned容器保卷，再经济停两原实例并核自动释放为空。任何成本/库存/失败不允许自动新购或删除旧证据。

## 单次APP预备worker

在安装20件后，根可使用 `app-prep-launch.PUBLIC.sh`（7669B，SHA `828421f6833681ffd0e0a678f2af1778f15d805fb777da0fae74d4f2617360da`），先把开头 `R29_APP_IP` 从空填写本次实测APP内网IP、将 `R29_ROOT_ADMIT_PREP=0` 明确改为1。其完整raw+300=7969、整体base64+300=10528；修改实际IP后根再量完整字节。默认拒绝，不能空IP或默许prep准入。只安装内嵌SHA固定的11117B worker `app-prep-once.py`（9ea78f415e9775efcda0d8f8b2e3aa0d29141fca6828bef15f373c0fbc404737），排他新路径 `/root/t44-r9/r29-app-prep-once.py`，然后异步systemd unit `t44-r29-app-prep-01`，RuntimeMaxSec=1800/KillMode=control-group/UMask=0077。完整worker在后台顺序运行，bootstrap不受GUI单条命令超时中断。

worker先核profile/P64/原e551全逐件pin和旧buildbinding，然后仅原CLI prepare→P arm/config/infra→actual probe-budget→migrate→status实际mysql/rabbit/实际backend image/source53→本次prep-only grant→bootstrap一次→idle/TLS401/六角色0restart/scheduler缺席。source proof SHA、budget、角色容器ID/镜像ID均来自本轮实际输出，seed44/04:00锚点保持，不硬填384。f阶段只准备文件，不启动；没有pressure grant/S1/S2/资源/relay ready声明。

每条原命令argv、stdout、stderr、returncode、双SHA记录在0700 `/root/t44-r9/r29-app-prep-01`（内部原件0600）。unit自身 stdout/stderr为 `/root/t44-r9/r29-app-prep-unit.stdout.private` 和同名stderr。已派发标记不等于ready，根核 `systemctl show t44-r29-app-prep-01.service -p ActiveState -p SubState -p Result -p ExecMainStatus`、`complete.PUBLIC.json`、真实idle metadata后再继续。失败保留prefix，不自动retry/重新seed/删除，不自动S1/S2；根先决策失败处置和停机。全链尚无真实云执行。
