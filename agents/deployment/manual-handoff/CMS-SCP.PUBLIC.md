最小 CMS/SCP 五件运输（用户执行，本地已测，云端未测）

本工具只运输 backend 提供的 **host五件目录**，不读QA PRIVATE、不改90b/ManualV4或原packet时间，不运行QA。Mac只经过公开cert、cipher和公开SHA回执，不经过明文五件/令牌/私钥。工具 `cms_five_transport.py` 应作为PUBLIC脚本复制到APP/LOAD；SSH/SCP使用root现有已审核的hostpin/有效临时key/禁转发配置，不另加访问权。父任务新现场为关TUN后en0直连，不默认代理。本任务未再次探测网络。

用户先仅开原LOAD16核做SSH短验证；SSH/SCP成功后再由用户开APP，不让64核计费等网络。以下占位值由真实现场填，命令均由用户执行。

LOAD生成仅文件接收用途的一日自签证书（不是TLS服务证书，不变更网络/访问权；原key仅由LOAD本机openssl打开、不导出）：

```sh
python3 /root/t44-final-20261029/cms_five_transport.py cert --key /root/t44-r9/r29-load-key-01/load-only-private.pem --output /root/t44-final-20261029/manual-UNIQUE-recipient.PUBLIC.pem
```

用户经已有hostpin认证的SCP将该PUBLIC cert由LOAD→Mac→APP；将LOAD原输出cert_sha256与APP使用的证书pin逐字匹配，防证书替换。原key不复制到Mac或APP。APP对backend实际host五件目录密封：

```sh
python3 /root/t44-final-20261029/cms_five_transport.py seal --inputs /绝对/实际/backend-host-five --cert /root/t44-final-20261029/manual-UNIQUE-recipient.PUBLIC.pem --cert-sha256 ACTUAL_LOAD_CERT_SHA256 --output /root/t44-final-20261029/manual-UNIQUE.cms
```

APP只输出公开原五件SHA/原tarSHA/cipherSHA和证书pin，不输出文件内容。原文件逐字保留；明文tar仅在APP进程内存，不落Mac/ stdout。用户用已有SCP将 `manual-UNIQUE.cms` 和 `manual-UNIQUE.cms.PUBLIC.json` 由APP→Mac→LOAD；公开回执应与APP经已验hostpin SSH取得的原SHA一致。

LOAD本机使用同一原key解封至全新opened目录（不得是既有W/输出）：

```sh
python3 /root/t44-final-20261029/cms_five_transport.py open --cipher /root/t44-final-20261029/manual-UNIQUE.cms --receipt /root/t44-final-20261029/manual-UNIQUE.cms.PUBLIC.json --cert /root/t44-final-20261029/manual-UNIQUE-recipient.PUBLIC.pem --cert-sha256 ACTUAL_LOAD_CERT_SHA256 --key /root/t44-r9/r29-load-key-01/load-only-private.pem --output /root/t44-final-20261029/manual-UNIQUE-opened
```

原PUBLIC `ADAPTER_MANUAL_753.py` 实际读取 `opened/inputs/` 下全部五件，因此本工具将五件都放 `manual-UNIQUE-opened/inputs/`，不是只将session放inputs。CMS/GCM及每件SHA完全验证后才创建opened；符号链接/额外成员/路径穿越/覆盖均拒绝。此opened作为原 `ENTRY_MANUAL_753.sh prepare W NEW_RUN OPENED` 的输入，仍需原ManualV4 defaultfalse→独立QA一次grant→用户manual execute；运输成功不等于资格、授权或压测通过。

标准封装是OpenSSL3 `cms -encrypt -binary -aes-256-gcm -outform DER -recip CERT -keyopt rsa_padding_mode:oaep -keyopt rsa_oaep_md:sha256`；GCM使用标准CMS AuthEnvelopedData，无自造加密。参考：https://docs.openssl.org/3.6/man3/CMS_encrypt/ 。本机实际使用 `/Users/yang/miniconda3/bin/openssl` **OpenSSL3.5.7** 完成合成五件/临时RSAkey/cert往返。Mac默认 `/usr/bin/openssl` 是LibreSSL3.3.6，工具拒绝而不降级CBC；本地测试明确指定OpenSSL3路径，云端使用实际已安装的OpenSSL3，未证明远程支持。

测试：`python3 -B tmp/748_manual_transport/test_cms_five.py`。原五件SHA/字节一致，cert/cipher/opened防覆盖，cipher变化、GCM tag变化（即使外部SHA同时改成匹配）以及cert pin替换均拒绝；认证失败不写opened。全部使用临时合成数据和测试key，未读真实五件/原LOADkey，未执行SSH/云端/QA。原790和旧C完全不参与此用户授权运输；不改原packet时间、grant或ManualV4门禁。
