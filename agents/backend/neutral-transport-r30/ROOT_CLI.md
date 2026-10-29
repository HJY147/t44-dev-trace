# 本轮 root 最短搬运页

只搬运已完成的新五件，不签会话、不改producer17/预算/clock。固定本轮C=`2026-10-29T10:40:00Z`，packet cutoff10:17:30；截止不足就停，不改时间。实际云连通性尚未执行。

APP/LOAD运行**相同**`install.PUBLIC.sh`全文作为一个RunCommand；先核全文SHA `f4b3d9dd120e8e948d31e2876a3c9c6cc698255130b64dd36738cc46dd47332e`。它内嵌gzip+base64七PUBLIC原件，固定新目录`/root/t44-r30/neutral-transport-01`；已存在即失败，不覆盖/重试。整个shell13143B，整体base64编码17524B，加256为17780<18000；不是只算gzip层。安装后manifest原SHA仍`2b147bfce49e299337defb6d04e4f0d48ab7e3179ea9588b2f1368aeafe57704`。

以下变量由操作员从**实际**producer/GEN/密钥回执填入；null/TBD不可执行。工具目录固定，数据父目录`/root/t44-r30`已存在；下列所有输出为新目录/新文件。

```sh
R30_TOOLS=/root/t44-r30/neutral-transport-01
R30_C=2026-10-29T10:40:00Z
# APP必填：R30_INPUTS=实际assemble输出的/inputs绝对路径
# R30_GEN_SHA=实际GEN原件SHA；R30_PUB=LOAD公钥在APP的实际绝对路径
# R30_PUB_SHA=该公钥实际SHA。LOAD私钥绝不传APP。
python3 -B "$R30_TOOLS/five_files.py" pack --input-dir "${R30_INPUTS:?}" --output-dir /root/t44-r30/transport-pack-01 --cost-stop-utc "$R30_C" --gen-binding-sha256 "${R30_GEN_SHA:?}"
```

APP从`transport-pack-01/pack.PUBLIC.json`原值取control/reference/CA/mirror SHA，按同目录RUNBOOK的seal完整argv，用公钥和GEN SHA，输出固定新`/root/t44-r30/transport-sealed-01`。seal stdout保存public_record_sha256、transfer_file_bytes、transfer_file_sha256，后三者分别用于原open、relay大小、relay全文件SHA，不混用opaque_sha。

root分别填原`relay.template.PUBLIC.json`到两机新`/root/t44-r30/relay-01.json`：显式`root_admit_transport=true`，实际互异APP/LOAD RFC1918 IPv4和既有允许端口、原GEN文件路径/SHA、实际APP证书路径/leaf SHA及私钥、LOAD原CA路径/SHA。APP source=`/root/t44-r30/transport-sealed-01/transfer.public.jsonl`，LOAD output=`/root/t44-r30/transport-received-01.jsonl`，双方attempt_marker分别为新`/root/t44-r30/transport-app-attempt-01.json`/`transport-load-attempt-01.json`；bytes/sha取seal全文值，cost_stop为本轮C。默认false/null不改成猜测值。普通CA/IP验证，不增加SG/IAM或权限。

```sh
# APP：root外层≤C硬截止监督，看到R30_OPAQUE_LISTENING后LOAD只请求一次。
python3 -B "$R30_TOOLS/opaque_tls.py" serve --config /root/t44-r30/relay-01.json
# LOAD：单次拉取。失败保marker/prefix，不自动重试。
python3 -B "$R30_TOOLS/opaque_tls.py" fetch --config /root/t44-r30/relay-01.json
# LOAD：R30_KEY是实际仅本机私钥；R30_RECORD_SHA为seal原public_record_sha256。
python3 -B "$R30_TOOLS/policy_790.py" --cost-stop-utc "$R30_C" open --private-key "${R30_KEY:?}" --transfer-file /root/t44-r30/transport-received-01.jsonl --public-record-sha256 "${R30_RECORD_SHA:?}" --output-dir /root/t44-r30/transport-open790-01
# R30_NEUTRAL_SHA为APP pack.PUBLIC.json记载原始中性包binding，不是GEN rawSHA。
python3 -B "$R30_TOOLS/five_files.py" extract --input-dir /root/t44-r30/transport-open790-01 --output-dir /root/t44-r30/transport-neutral-01 --cost-stop-utc "$R30_C" --gen-binding-sha256 "${R30_GEN_SHA:?}" --neutral-binding-sha256 "${R30_NEUTRAL_SHA:?}"
```

只将`/root/t44-r30/transport-neutral-01`交既有0b ENTRY的`prepare --neutral-opened-dir`；其中inputs才是原五件：session、CA、source-manifest、bundle-manifest、actual import receipt。不要把790的小reference传QA。grant仍由root按真实剩余TTL/窗口另决；此页、安装器和本地往返不证明SUT/QA执行成功。
