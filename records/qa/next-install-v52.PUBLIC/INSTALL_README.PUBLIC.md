# v5.2 新独立工具包：仅离线交付

状态：密文与安装入口已离线自检；现场身份/资源/安装/prepare/业务/性能全部未验证。没有allow=true、没有当前环境批准、没有负载。原p13及所有旧工作区保留，不得覆盖。

本目录全部可由总协调读取或搬运；其中tools.753capsule为密文，transport-key.rsa-oaep-sha256为对旧LOAD公开RSA收件公钥加密的全新运输密钥。backup.key在密文内，全新原件只留本独立测试岗本地；本目录没有明文backup key/运输密钥/收件私钥/测试源码或旧结果。公开ADAPTER/ENTRY/capsule_tool/INSTALL均属于中性工具。

收件PUBLIC公钥来源：主树tmp/753_independent_final_20261029/PUBLIC/load-public.pem；DER SHA256=385f2632f9c82260639db1c0994ebf951a9c1e9efa97a2cd5249b190220f5e66，与旧冻结INSTALL指纹吻合。没有读取旧私钥或实际执行LOAD解密；对应私钥在LOAD是否仍存在需以后中性现场核实。丢失时阻塞，不生成替代批准或读取旧key。

精确包：74721 bytes；SHA256=f4ac699408a3c00d8cd547cde90be547279c009dda4a94360f8fb0ef3e5d7939。tool-manifest精确SHA=b74a36dc706fca25f78bfca12a9025b158457e851a3e1dd17c1f29639bc59026。INSTALL SHA=53ee527b30cd0d09e830c368e6655bf7397a2b1cca3b95c9b956ebf9edd852a0。manifest绑定exact13acb43a804e717e7485091895378511fe3d9b76、v1.2规格freeze SHA及v5.2 release SHA、runtime/adapter/ENTRY和每个密文成员。

## 以后获准开机/运输时的命令（本轮未执行）

总协调仅搬本PUBLIC目录，不能打包或读取private-next-tools。LOAD_HOST及LOAD_RSA_PRIVATE必须以后使用真实中性事实设置；不要猜旧私钥路径。W必须为从未存在的新目录，示例独立名称与旧W不同。

本机：
```sh
LOCAL_PUBLIC='/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/independent-next-offline-20261031/records/qa/next-install-v52.PUBLIC'
# LOAD_HOST由以后获准的中性连接信息填写；此处不进行连接。
scp -r "$LOCAL_PUBLIC" "$LOAD_HOST:/root/t44-next-v52-public-staging"
```

LOAD本机（以后独立授权下执行；不是当前准入）：
```sh
W=/root/t44-final-20261031/QA753_NEXT_V52
mkdir -p /root/t44-final-20261031
mkdir "$W"
cp -R /root/t44-next-v52-public-staging "$W/public"
[ "$(sha256sum "$W/public/INSTALL_753.sh" | cut -d ' ' -f 1)" = 53ee527b30cd0d09e830c368e6655bf7397a2b1cca3b95c9b956ebf9edd852a0 ] || exit 2
sh "$W/public/INSTALL_753.sh" "$W" "$LOAD_RSA_PRIVATE"
```

mkdir不得加-p到W本身；若新W或staging已有内容，停止检查，不覆盖或自动清理重试。原安装器也拒绝已有private_tools或.transport.key。新INSTALL先核公开manifest/胶囊/运输密钥/解包器/adapter/ENTRY的精确SHA，再核固定LOAD镜像和RSA公钥指纹，OAEP-SHA256解密后在network none容器解封新工具。CPU1/256MiB/32pids、无拉取、只读容器根、W绑定仍沿用原冻结安装接口。成功仅OPAQUE_INSTALLED_NO_SUT_CONTACT；不是身份、prepare或性能通过。任何失败保留部分输出并由独立测试岗决定，禁止自动重试。

新workspace没有TARGET_PROFILE/APPROVAL或真实packet；这是刻意的未批准状态。以后必须由新中性事实核审，再提供绑定本新adapter/runtime hash的身份、全新material/run/nonce、新default-false与一次审核。旧p12 PREPARE_REUSE及旧身份/grant不能用于此包。现场工具版本独立批准、资源和磁盘/封存预算核验完成之前不发allow=true。

## 离线验证证据与边界

本机21项logger/raw测试、1项合成default-false prepare、8项安装运输测试通过。安装测试用本轮自己生成的运输密钥核实际胶囊，并核所有成员SHA/新backup.key一致；合成RSA生成于临时目录且不涉及旧收件私钥。实际收件OAEP仅用公开LOAD公钥加密，未能也未尝试在本机使用其私钥解密。bootstrap篡改与重复目录在任何Docker/私钥使用之前拒绝；没有执行真正Docker成功路径、网络或SUT。

安装额外预算：原capsule_tool MAX8MiB，当前密文约73KiB；安装容器256MiB/32pids。运行仍8CPU/8GiB/2048pids与原10/11/12GiB记录上限。整个新W密文/工具、原始记录、备份及运输副本须以后按真实盘容量测算，不以小包大小冒充正式记录空间充分。
