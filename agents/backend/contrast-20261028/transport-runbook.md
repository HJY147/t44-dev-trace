# 私包传输操作单（独立新helper）

后端AI，ROOT唯一云操作者。本岗没有读取实际私包。helper源a5524aa1，SHA `4508b92f1f9106b112cc0e9f0a9e5c4e8445f5e276ad12184570a15450996db2`，12574B。公开投递 `transport-delivery.json` 5467字符；两宿主各自解gzip+base64到 `/root/t44-r9/resume-20261028-01/790_transfer.py` 并核SHA。只新增此文件，不更改冻结tools790-v2七件/manifest。

1. LOAD先执行，下列输出仅公钥及公开hash。私钥只在LOAD新目录，600，勿输出或搬运。

```sh
python3 -B /root/t44-r9/resume-20261028-01/790_transfer.py keygen --output-dir /root/t44-r9/resume-20261028-01/transport790-p7-key01
```

2. root把PUBLIC-790-KEY行的 `public_key_b64` 解base64成APP新600文件 `/root/t44-r9/resume-20261028-01/transport790-p7-load-public.pem`（公钥可经控制台），保留同一行 `public_key_sha256` 为下面 `PUBLIC_KEY_SHA`。先安装helper/公钥，再跑实际S2以保600s会话。S2成功后只用它公开的control/packet SHA替换下面 `CONTROL_SHA` 和 `PACKET_SHA`；不可从私包正文/账号/env读取。

```sh
python3 -B /root/t44-r9/resume-20261028-01/790_transfer.py seal \
  --public-key-file /root/t44-r9/resume-20261028-01/transport790-p7-load-public.pem \
  --public-key-sha256 PUBLIC_KEY_SHA \
  --binding-sha256 eac4f526cc742b8c71393cf3af819092e59abd5deeefdc375d1a5e51fc0cfcf6 \
  --control /root/t44-r9/campaign-r28p7-01/p/fixture790-01/split790-v2-01/inputs/control.private.json \
  --control-sha256 CONTROL_SHA \
  --session /root/t44-r9/campaign-r28p7-01/p/fixture790-01/split790-v2-01/s2/session-01/session.private.json \
  --packet-sha256 PACKET_SHA \
  --ca /root/t44-r9/campaign-r28p7-01/p/fixture790-01/split790-v2-01/inputs/ca.pem \
  --ca-sha256 05fcac0d76b79bdb7ed27634490dcfcc31effa4740c6b0cd9a7352e8a927a1ab \
  --mirror /root/t44-r9/resource-r28p7-01/private-mirror-handoff.json \
  --mirror-sha256 5410a28a6c231f10259dfffb9a04f47b1125c72e2fa714777f574acad2ac224b \
  --output-dir /root/t44-r9/resume-20261028-01/transport790-p7-sealed01
```

3. APP只输出一行PUBLIC（含三/四文件SHA，公钥hash，密文字符数和分段总数），随后逐行OPAQUE。每段data最多16000字符，若总长>18000则分多段；整个PUBLIC+全部OPAQUE行按序复制到LOAD新 `transport790-p7.public.jsonl`（仅密文+公开hash，无私包）。root保留APP原PUBLIC里的 `public_record_sha256` 作为 `APP_PUBLIC_RECORD_SHA`，不要从未知来源重算后自认可信。

```sh
python3 -B /root/t44-r9/resume-20261028-01/790_transfer.py open \
  --private-key /root/t44-r9/resume-20261028-01/transport790-p7-key01/load-only-private.pem \
  --transfer-file /root/t44-r9/resume-20261028-01/transport790-p7.public.jsonl \
  --public-record-sha256 APP_PUBLIC_RECORD_SHA \
  --output-dir /root/t44-r9/resume-20261028-01/transport790-p7-open01
```

成功后仅打印公开receipt。LOAD输入为 `.../transport790-p7-open01/inputs`，只含control/session/ca，三个均600；可选mirror独立为 `.../transport790-p7-open01/mirror/private-mirror-handoff.json`，600。root核receipt四件hash分别等APP原PUBLIC，binding等真实eac；再原790_load以原controlSHA/packetSHA启动，且资源collector原工具消费mirror。不打印或cat任何private文件内容。

失败不重试登录/重seed/续包；先保留实际错误前缀交root判断。helper错误只输出通用PUBLIC失败（退出1），不输出包含密钥的openssl argv/stderr/异常值。HMAC先验再AES解密；root可信控制台搬运公钥与PUBLIC pin，不能把RSA+HMAC当APP身份签名。宿主实际OpenSSL/Python3.10由root执行核，本岗仅Python3.12+LibreSSL3.3.6合成验证和3.10 AST检查。私钥后续由root按证据/安全策略保留或删除，本工具不自动删现有数据。
