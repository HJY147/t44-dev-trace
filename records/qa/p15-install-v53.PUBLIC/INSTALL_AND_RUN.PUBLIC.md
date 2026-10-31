# p15 / v5.3 独立离线工具交付

离线工具已实际打包、自检；真实安装、身份、会话、资源与正式性能尚未执行。当前没有allow=true。只运行一轮400 clients /60s warmup /600s steady，四类P95各≤270ms、每个完成分钟≥1000、零错误及全部原业务/审计/后置断言原字节保留。无自动关机、重跑或AB授权。

候选 bcec3326b40814fdb1922bbfea7c29473b47ba47。138945d1仅后续证据，不能替代准确产品身份。run=r30manualp15，material=r30materialresume09，maintenance=r30restoretransition09，W=/root/t44-final-20261031/QA753_NEXT_V53。本地Git可达公开记录未见此W/run使用；云端不存在与未消费仍须开机实证，不宣称已经核实。

PUBLIC安装目录和控制目录可搬运；密钥/测试源码不交总协调。全新backup.key与运输key只在独立私密目录及新胶囊；运输key用原冻结LOAD公开RSA公钥OAEP-SHA256封装，未读旧私钥或旧backup.key。LOAD私钥存在性须现场核实。新manifest的release_freeze_sha256是原测量实现v5.2 provenance；准确本轮source/包字节以本新manifest及本目录OFFLINE_CHECKS为准。

## 安装及入口

LOAD_HOST、LOAD_RSA_PRIVATE必须来自当前中性连接事实；先核目标W与staging完全不存在，禁止覆盖。复制两个PUBLIC目录到全新staging。LOAD执行：
```sh
W=/root/t44-final-20261031/QA753_NEXT_V53
mkdir -p /root/t44-final-20261031
mkdir "$W"
cp -R /root/t44-p15-install-staging "$W/public"
sh "$W/public/INSTALL_753.sh" "$W" "$LOAD_RSA_PRIVATE"
```
先按DELIVERY_MANIFEST逐项核SHA。INSTALL固定本新manifest/capsule/运输key SHA及LOAD镜像与收件公钥指纹。成功仅OPAQUE_INSTALLED_NO_SUT_CONTACT。旧工具/旧grant/旧PRIVATE结果不可装入。

ENTRY_MANUAL_753.sh保持原字节SHA d15874c477fef0d92bc68ab77802a5354d15be237c853621b56467005c20d43e；ADAPTER SHA 44451456d63d94b612924d215ece822dfce127f4cc67926294f33b643fd14cf3；runtime SHA 9cf747e308969ceba37e2cfcfa6591def45e118ad928c4f310f57b6ecf37542a。

## 当前身份与会话接口

模板均默认false/DRAFT/null，不可直接当作批准。新独立审核必须产生TARGET_PROFILE_753.json与APPROVAL_753.json：前者git_commit绑定准确bcec、source/bundle/import原件SHA、当前APP config、固定LOAD config/OpenAPI/runtime；后者approved只在真实审核后允许true，scope=IDENTITY_ONLY_FOR_ZERO_SUT_PREPARE，绑定profile精确字节SHA与adapter SHA，functional_authorized/benchmark_authorized/grant_allow仍false。

五原件为opened/inputs/session.private.json、ca.pem、source-manifest.json、backend-bundle-manifest.json、backend-import-receipt.json。session schema=NEUTRAL_753_INPUTS_V1，run_id为material09。identity.git_commit为准确bcec；identity.runtime_sha256仍为运输历史常量81e04666cf05c2932397c5d39521ef881602f3046342e2d4d5605a694e5829bf，不能误填新runtime；实际profile/grant runtime为新9cf747。source/bundle/import均需当前准确原件，receipt.source_sha=bcec，实际七角色image映射单独核实。binding_sha256按去掉自身字段后的canonical UTF8 JSON(sort_keys, compact, ensure_ascii=False, allow_nan=False)+换行计算。

四角色manager/developer/reviewer/service真session、真实scope/项目、400 clients恰0..399、800互异任务、至少35项目及完整任务/event快照，原协议所有资格检查不变。新随机nonce、maintenance09、schema/campaign、七角色映射、fixture/load_receipt、资源排他、CA/TLS、磁盘及整个W封存峰值均需当前独立中性审核，不能用adapter成功替代。

```sh
sh "$W/public/ENTRY_MANUAL_753.sh" prepare "$W" r30manualp15 "$FRESH_PACKET_OPENED"
```
prepare仅network none核文件，输出environment及grant.default-false。之后独立岗核环境精确SHA/default-false原字节/五输入与binding/当前事实，最短真实会话expiry严格覆盖实际触发后900秒，签发前重新核。新decision模板九项均false，不由协调者填写为审核完成。

```sh
python3 ISSUE_ONCE_P15.py "$W/runs/r30manualp15/grant.default-false.json" independent-decision.json
# 只有当前独立审核完成且用户授权有效，独立测试岗才运行：
python3 ISSUE_ONCE_P15.py "$W/runs/r30manualp15/grant.default-false.json" independent-decision.json --issue-after-current-review "$NEW_ONCE_GRANT"
sh "$W/public/ENTRY_MANUAL_753.sh" execute "$W" r30manualp15 "$NEW_ONCE_GRANT"
python3 OBSERVE_PHASE_PUBLIC_753.py "$W" r30manualp15
```
issuer只允许原default-false的allow字段变化；execute拒绝同run消费及已有结果。任一身份/输入/资源/排他变化使审核失效。RUNNING400只表示栅栏释放。

## 诊断与证据

诊断Server-Timing有2048字符输出上限，含incomplete标记；仍须按每次真实响应完整headers/wire留存纳入原3MiB记录上限、12GiB raw及备份/复制峰值预算，不能为省空间删headers/慢请求。APP诊断指标数量有界，缺失不得推断为0。

实际source中T44_REQUEST_DIAGNOSTICS==1在APP启用，默认off；不改变任何负载请求headers、路径、业务或测量纳入。原raw每请求保存start/end/elapsed、status、完整response_headers及wire，包含原app基准和diag。所有慢请求及无诊断请求完整计入原验收。新增密封diagnostics_projection仅事后解析原Server-Timing，worker pid/incomplete缺失为null/unknown，不补0、不剔除样本，不改变测量。

退出且所有producer/writer及外部operator/evidence写者真实停止后：
```sh
sh SEAL_P15_V53.sh "$W" r30manualp15 /root/t44-sealed-p15/r30manualp15.753backup EXITED_ALL_PRODUCERS_AND_WRITERS_STOPPED
```
输出父目录须预先存在、位于W外且目标不存在。独立岗私下用新key核backup认证/逐文件hash及raw完整性/全部原断言；root仅搬密文与receipt。封存失败留证不覆盖不自动重试。

## 实际离线证据与阻塞

21/21原logger/raw单元通过；4/4新增合成测试通过（新胶囊完整解包及重复目录拒绝、diag缺失unknown与原基准保留、默认DRAFT拒绝、准确bcec/material09合成prepare/defaultfalse及重复run拒绝）。CA仅明确替身，无网络/云/SSH/Docker/SUT。PUBLIC Python AST与shell语法通过。旧test_prepare_offline.py与其公开release SHA不符，因此未读取复用，使用新写合成测试。

准确bcec中14个冻结files及frontend兼容输入共15/16匹配；唯一AGENTS.md当前SHA与历史freeze不符，历史source_commit的AGENTS blob精确匹配原freeze。diff仅过程/状态/用户交接说明，包含开发语境句，未作为测试预期或证据；所有冻结业务/契约/DDL和原断言未改变。当前不能说15+1全部匹配。保留差异由总协调依用户后续指令及历史freeze原件另记，未回写清单、未自动豁免准入。

现场尚缺：新W未使用证据、LOAD私钥/镜像、实际Linux安装与prepare、准确APP七角色/导入/会话/证书/库存、CPU/RAM/pids/排他、12GiB raw及整个W备份/复制峰值磁盘容量、当前工具独立批准与once审核。不得将离线准备当正式性能/业务/投递接受。
