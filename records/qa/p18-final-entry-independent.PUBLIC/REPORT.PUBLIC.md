# P18 独立最终入口及工具身份审核

职责：独立冻结入口、身份、依赖、初始化、连接保护、控制与回收检查；仅本地离线。未 SSH、云调用、HTTP、SUT、解开私钥，未使用作者内部测试脚本或日志。先向总协调冻结清单，然后读许可源。源码参考 32e0d935。

当前结论：临时物料限定本地审核通过，最终包补核待完成；READY 必须保持 PREPARING。本报告不证明 660 秒完整本地轮通过，不授权连接，不是 Linux 现场或产品正式验收。

实际执行 `python3 -B records/qa/p18-final-entry-independent.PUBLIC/check.py /tmp/t44-p18-provisional-20261031.tar.gz` 成功。脚本与真实结果分别在 check.py、CHECKS.PUBLIC.json，审核源哈希见 SOURCE_HASHES.PUBLIC.json。

- 临时包 156793 字节，SHA256 `90a26ca56f9d1b99bed59d946a5ad8809a1cc5cefd212598c5cb39a13453b055`，46 个唯一普通成员，路径闭合、每文件长度与 SHA 和 manifest 一致，匹配本地源和运行契约。
- 两个受支持 Mac 入口 after_boot.py/run.py 实际在 PREPARING 期间拒绝，失败发生于 key、归档读取和 SSH 之前。最终 READY 必须绑定本报告列出的全部本地执行源及精确最终包；本次未改 READY 或执行源。
- PRIVATE 非 key 工具源逐一验证 manifest 哈希；runtime/post/compiled/functional/openapi/backup/verifiers 与原 v12 逐字节相同；BOOT 唯一差分为 RUN17→18。有效身份组合 SHA 重新计算一致，涵盖 BOOT 变化。未读取 key，key/capsule 解密真实性不在此次独立证明内。
- 自编 400 混合 mock：200 个 state2 无写；200 个 state3-from2 使用 action3、原 token、CAS 版本、幂等键及 evidence，再权威读回状态2/version+1，原 ID 不变；最后一个非法状态导致全部写入前拒绝。该 mock 证明客户端行为，未证明现场业务接受。
- 自编回收 mock：未证退出时零下载且不宣称可停；非零退出仍下载备份并核验 bytes/SHA，然后产生可停两机通知。

静态独立审核：400/60+600、四类 P95≤270、十分钟桶≥1000、稳态零错误由未变测量源保持；后置400快照/400完整审计和原40s判据未降低。BOOT旧准备豁免显式保留诊断分类，无正式全门禁通过冒称。

入口使用固定 r30posttools18、W=/root/t44-final-20261101/QA753_DIRECT_P18、REMOTE=/root/t44-direct-p18；远端目录/写入独占，不重试初始化/启动写。归档含 backend、readiness、launcher、SSH辅助、观察器、CMS transport、provenance、QA工具胶囊及公开安装/执行/封存入口；依赖现有固定 Docker 镜像、原 CA/账号/导入凭证和 LOAD 解密私钥，这些现场前置不是归档自带，也未声称本机已验证。

TLS代码保留原 hostname SNI/Host、CA证书与主机名校验，JSON UTF8字节传输；SSH配置保留实例 HostKeyAlias、StrictHostKeyChecking=yes、原pins、无 agent/端口转发/ProxyJump，不改服务端 restrict 授权。服务端当前身份与restrict存在性仍属现场待核。

控制器通道在 W 外，退出记录仅在直接shell结束后写；shell等 docker 退出才封存，封存进一步检查容器、writer_finalized/未启producer和资源边界，异常未知状态不强制seal。回收不重跑、不自动关VM。APP在wrapper结束与观察回收后可先通知停；LOAD需备份长度/SHA核验后立即通知双机可停。现场可用性、Linux资源限制和实际 producer 退出链未在此次macOS本地运行证明。

最终交付需要在总协调提供最终包后，重跑归档闭合和源一致检查，保存最终bytes/SHA结果，再由总协调生成绑定全部实际执行源的READY。

## 最终包补核

已按同一独立脚本重跑最终包并成功：`direct18-ready-20261031.tar.gz`，161440 bytes，SHA256 `d010498af9beffdf82e1fd2d39b67d7ad149403447102eac9d645e0b6fb8db0d`，50 payload + MANIFEST。详细限定结论在 FINAL_ARCHIVE.PUBLIC.json，CHECKS.PUBLIC.json更新为此次真实最终包运行结果。

全部9项执行源哈希仍与最初冻结一致；最终包和临时包的执行源、胶囊、密钥封装字节不变，所有成员及三级owner manifest哈希闭合。CLI契约仅 current_preparation_status 元数据更新，执行参数/身份/判据均不变。新增证据仅作归档字节哈希，不读取或采用作者结果预期。READY观察值仍PREPARING_DO_NOT_START_SERVERS。

最终包入口及身份限定审核通过，无本岗新增阻断；总协调应在其他独立职责完成后绑定精确包及完整本地依赖清单再生成READY。本补核不验证新增660秒证据语义、不将离线fixture性能结果转成现场性能结论，不包含SSH/HTTP/Linux现场验证。
