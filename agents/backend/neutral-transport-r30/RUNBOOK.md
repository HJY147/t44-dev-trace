# 新中性五件搬运闭环：只操作员运行

不改producer17件/QA core。原790模块SHA `8600110b54f45240a6e45ea62c9be6f567529e374807d0ca593dde3fd7605db7`原字节保留；新policy薄入口只设SOURCE=0b与本轮C，RSA3072/OAEP/AES256-CBC/HMAC、wire、原caps均不变。**禁止直接运行带旧f7/12Z的original副本**。本轮root明确C=`2026-10-29T10:40:00Z`，不是从旧包延时。LOAD私钥只由操作员在LOAD使用，不交root/APP/QA源阅读者。

所有路径均实际绝对/无软链接/新目录；全部新工具用`python3 -B`，不加-I（多文件标准库工具需本目录可导入），无安装包、权限/SG/IAM变化。先完成代码/openssl/CA/IP/端口/公钥指纹预检，不能消耗临时session后再安装。以下是未来命令契约，本岗只做合成本地验证；变量是root实际值而非可直接执行授权。

1. LOAD使用原已授权现有公钥并核实际SHA，或在**新目录**一次生成运维运输钥匙（不是SUT session）。APP仅接收public.pem与SHA，LOAD私钥留在LOAD。

```sh
python3 -B /TRANSPORT/policy_790.py --cost-stop-utc 2026-10-29T10:40:00Z keygen --output-dir /LOAD/NEW-KEY-DIR
```

2. APP producer assemble后的`NEW-PRODUCER/inputs`恰为五件原字节。先pack到新目录，输出`pack.PUBLIC.json`含原五件逐件SHA、archive SHA、neutral binding和4个seal输入SHA。原mirror必须JSON，所以用base64(tar.gz) JSON；原session槽是小archive reference，**不是QA packet**，避免大session重复触发原2MB cap。

```sh
python3 -B /TRANSPORT/five_files.py pack --input-dir /APP/NEW-PRODUCER/inputs --output-dir /APP/NEW-PACK --cost-stop-utc 2026-10-29T10:40:00Z --gen-binding-sha256 ACTUAL_GEN_RAW_SHA
python3 -B /TRANSPORT/policy_790.py --cost-stop-utc 2026-10-29T10:40:00Z seal --public-key-file /APP/NEW-LOAD-public.pem --public-key-sha256 ACTUAL_PUBLIC_KEY_SHA --binding-sha256 ACTUAL_GEN_RAW_SHA --control /APP/NEW-PACK/control.json --control-sha256 PACK_CONTROL_SHA --session /APP/NEW-PACK/session-reference.json --packet-sha256 PACK_REFERENCE_SHA --ca /APP/NEW-PACK/ca.pem --ca-sha256 ACTUAL_CA_SHA --mirror /APP/NEW-PACK/mirror.json --mirror-sha256 PACK_MIRROR_SHA --output-dir /APP/NEW-SEALED
```

3. Root从实际sealed文件核byte数/SHA，填两侧独立`relay.template.PUBLIC.json`，显式root_admit_transport=true，实际新IP/私网既有允许端口、新marker。APP source指向sealed/transfer.public.jsonl；APP cert/private key用本轮真实TLS材料并核leaf SHA；LOAD CA用原actual CA且核SHA。服务端同原GEN binding SHA/source/app IP及G+5=C；客户端普通CA/IP验证，不允许公共IP/loopback或DNS。**测试的loopback只是低层本机TLS harness，生产CLI拒绝loopback。**

```sh
# APP受root外层≤C硬截止监督，看到LISTENING后LOAD只发一次GET。
python3 -B /TRANSPORT/opaque_tls.py serve --config /APP/NEW-RELAY.json
python3 -B /TRANSPORT/opaque_tls.py fetch --config /LOAD/NEW-RELAY.json
```

4. LOAD fetch只写密文、一次尝试marker，失败不重试。原open核public record SHA与HMAC，再操作员抽取。先验大小≤4MiB，保留原790更紧的2MB输入/接收cap；超限拒绝，不调高cap。source/bundle/import经镜像tar携带，逐件SHA与original CA核对；拒路径穿越、重复名、link、额外文件/膨胀；全验证后新目录O_EXCL/0600写。

```sh
python3 -B /TRANSPORT/policy_790.py --cost-stop-utc 2026-10-29T10:40:00Z open --private-key /LOAD/ACTUAL-OWN-KEY/load-only-private.pem --transfer-file /LOAD/NEW-transfer.OPAQUE.jsonl --public-record-sha256 ACTUAL_SEAL_PUBLIC_RECORD_SHA --output-dir /LOAD/NEW-OPEN790
python3 -B /TRANSPORT/five_files.py extract --input-dir /LOAD/NEW-OPEN790 --output-dir /LOAD/NEW-NEUTRAL --cost-stop-utc 2026-10-29T10:40:00Z --gen-binding-sha256 ACTUAL_GEN_RAW_SHA --neutral-binding-sha256 ACTUAL_ORIGINAL_NEUTRAL_BINDING
```

5. 仅把`/LOAD/NEW-NEUTRAL`给既有0b `ENTRY_0B_V24.sh prepare --neutral-opened-dir ...`；它的inputs才是原始`NEUTRAL_772_INPUTS_V2_0B_V24`五件，不能把NEW-OPEN790中的小reference误当QA packet。执行grant仍另由root决定；工具不改created/expires/窗口，不登录或延期，不读QA private core/cases。

本机真实加密+TLS+原open+五件抽取逐字roundtrip、错误CA/peer、篡改、cap/覆盖/一次请求、真实绝对C alarm均测试；只合成材料、local loopback，不证明私网云连通性或真实中性材料就绪。源文件/密文与失败prefix排他保留，今天root有限窗口后保盘停机。
