# 最终新窗口10:30Z：小段运输与两个新namespace

本页为本地交付，root唯一云执行者。source仍a12e9e70b963bacafda3242bb6d82e53ee912ff1/真实53文件，原a12镜像与root01 sourcechecked/buildbinding只读复用，不重建/重买。旧07:30与08:15工具/字节不变；root回传07:30 timer已停旧phase，08:15大运输未提交、未云安装。

## 四条小命令，逐条看真实成功

本地路径前缀 `agents/deployment/resume-20261028/window1030/`：

| 序号 | 文件 | raw字节 | 整条命令base64+256字节描述 |
| --- | --- | ---: | ---: |
| 1 | `01-write-000.sh` | 12023 | 16288 |
| 2 | `02-write-001.sh` | 10880 | 14764 |
| 3 | `03-write-002.sh` | 9188 | 12508 |
| 4 | `04-reassemble-install.sh` | 5180 | 7164 |

这才是官方编码限制的完整测量；旧31595 raw<32KiB并不足够，不能再提交它。每条raw≤13000、encoded+256<18000，前三条opaque片7500/7500/6229字节。逐条复制原文到APP云助手新执行，看index/bytes/SHA真实终态；不要把四件拼成大命令，也不要为了重试覆写已成功片。

1独占创建 `/root/t44-r9/resume-20261028-02`、parts和manifest并写part0；2/3先核manifest原SHA，再各自O_EXCL|NOFOLLOW写新片。4只读严格重组字面连续片集合、片/整包SHA和有界gzip，再核三件完整SHA/source/10:30/53及编译，独占新`resume-profile`目录写0600/fsync。缺片、重复/额外片、篡改、符号链接、目录已存在都拒绝，原前缀留存。运输不含env/账号/nonce/会话或私钥。

manifest SHA256 `52133caf5b77e8e061e8f2c489eff5a32b6bcca80d27c6ae01295a55f7c3b8a4`；整gzip21229字节及其完整SHA、各序号SHA见manifest.PUBLIC.json。最终新hostroot是root02，脚本在 `/root/t44-r9/resume-20261028-02/resume-profile/`：

| 文件 | 字节 | SHA256 |
| --- | ---: | --- |
| profile.json | 1495 | 222c97a1a3711aafcb583f8683009411702f8d91a4cd65a601de631572da0b80 |
| generation.py | 27199 | 4672a5838879ab1fde599c45d464906600373fdb38da654e21879881204d11a8 |
| resource-stream.py | 44079 | e5b0324e1576f901cbacb1ba9b973096c6b575318cc9f336a6f7183ce94ca115 |

sourcea12 builder仍`ebc91ce54ee73a418b9df11c3878ae75e348198b64c25060aeff8462de3949d1`，原daaf factory和sourcechecked中的同源builder不变；不把新repo c0358 factory替换到云旧路径。

## 新P16 gen02 prepare（此前未云prepare）

root每步读实际clock。新prepare/非stop/status SUT动作本身要求余窗≥600秒，建议开始prepare时≥1800秒；10:20Z后不得继续新idle/迁移/轮换/启动。status/stop允许过期后按owned身份收尾。旧phase已停事实须root重新核验，避免P16和F运行时叠加超32GiB；分别prepare不等于启动。

```sh
python3 /root/t44-r9/resume-20261028-02/resume-profile/generation.py prepare \
  --factory /root/t44-r9/campaign-935/p/controller.py \
  --upgrade-binding /root/t44-r9/resume-20261028-01/build-01/upgrade-binding.json \
  --upgrade-binding-sha256 31fc1c8a9cd2162656c8cfc9a42e830e228494d1e644f143921bbb718834cbd8 \
  --source-package /root/t44-r9/resume-20261028-01/source-checked-01 \
  --source-manifest-sha256 68f9db715b4a9d33d1cc70c5f7d08a50fcd51c97dfd4276dceba71e93d9ade00 \
  --original-proof /root/t44-r9/proof-v2-01/proof.jsonl --image-proof /root/t44-r9/image-proof.py \
  --output /root/t44-r9/campaign-r28p16-02 --run-id r28p16gen02 --app-ip ROOT_ACTUAL_APP_PRIVATE_IP \
  --f-tls-port 21443 --f-http-port 18380 --p-tls-port 21445 --p-http-port 18381 \
  --p-workers 16 --stop-utc 2026-10-28T10:30:00Z
```

取真实p回执的bindingSHA，后续仅p：新controller arm/config/infra/migrate，数据库`t44c_r28p16gen02_p`；f不启。新namespace/project=`t44-cloud-r28p16gen02-p`，CA/端口/绑定另冻。端口只是计划，真实bind-free失败时不抢占unknown。

旧790包硬截止07:30且会拒10:30 binding，**不可直接运行**；由后端责任岗另给新窗口冻结包。root核新包的完整身份、same-source/seed/anchor及剩余时间，再走其真实bootstrap/S1/S2/load。部署不改该包前提、不读私包，不把新helper准备等同新cohort结果。

## 独立F功能prepare

同一10:30 helper与相同只读输入，`prepare`参数仅改：

```text
--output /root/t44-r9/campaign-r28functional-01 --run-id r28funcgen01
--f-tls-port 22443 --f-http-port 18480 --p-tls-port 22445 --p-http-port 18481
--p-workers 7 --stop-utc 2026-10-28T10:30:00Z
```

完整两个argv在window1030/prepare-plan.PUBLIC.json；本地已用新generator真实argparse解析并在dispatch前拦截，无云动作。`r28funcgen01`合法12字符。只启动**f**（固定4worker），project=`t44-cloud-r28funcgen01-f`、DB=`t44c_r28funcgen01_f`。p仅prepare不启；F空库原CLI五个不同身份、不用790 P种子或旧会话。独立工具/中性准入须新有效窗口，不能因换了helper就把旧grant延长。

两种运行的resource均使用这套10:30 helper与各自真实phase binding；collector/mirror须warmup前启动，真缺值保持missing/null。合理sampleUntil≤10:28:30、serveUntil≤10:29:30留finaltail，实际由root依完整测试区间确定；不能预填数值/coverage或完成结论。结束依次seal→LOAD全尾/wholeSHA→stop observers→owned SUT stop，保留盘和原始证据，云停机由root预算管理。

本岗10项本地检查通过：整条编码大小、真实本地重组/独占安装、缺/额外/篡改/符号链接/manifest拒绝、旧08:15字节未变、新source/10:30链及两个namespace解析。没有云、产品、792/private、IAM或新购操作。
