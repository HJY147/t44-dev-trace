# a12双臂开发夹具最短运行顺序

**当前工具包版本2**，替代经审核阻断的第一套split/load包。每次HTTP派发及connect后都重核截止/共享abort，socket与host子进程等待按绝对剩余窗收紧；已in-flight可能留下真实响应或部分状态，不重试、不声称全局回滚。

全部由总协调在已授权原双机执行。本岗未操作云。目标固定`a12e9e70b963bacafda3242bb6d82e53ee912ff1`，seed44/anchor2026-10-28T04:00Z，最晚07:30Z停止；过期后不能改旧包时间继续。原任务、原935记录及F空环境不动。

1. 新phase实际prepare→arm/config→infra→migrate；核原入口、P7或P16实际binding与完整源。安装本轮`split-v2-delivery-1/2/3.json`完整包；七脚本加manifest都进入全新tools目录。现bootstrap脚本13626B/SHA34893edc9fa6061b634e22b399d09ae67047d120835f446bc746294dc3f223e5。P7已由root用历史bootstrap-v2.json(9020847f…)真实成功，不要重跑或重置，后续新工具可接其原控制包。
2. `python3 <tools>/790_bootstrap.py --phase-dir <actual-P-phase> --binding-sha256 <actualSHA> --output-name fixture790-01 --anchor-at 2026-10-28T04:00:00Z`。它只建用户/调用原seed_demo并核规模，不起API或负载。输出新phase/fixture790-01，账号/control/identities均0600，根不读正文。
3. root用原controller idle启动API/consumer/web/TLS；**首个配置对照不启动scheduler**，实际scope记开发6-role，不是正式7-role。先启动scheduler会把任务提醒/版本改变，当前S1无事件前提将拒绝；不得删断言求绿。
4. 将split-v2-delivery-1/2/3.json的每文件gzip+b64解码到一个新工具根，核原bytes/SHA，保持data/edge结构；目录0555、工具文件0444，manifest原件不要重排JSON。七文件manifest SHA `640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84`。三个v2投递须全部安装在新tools目录，旧工具根和所有v1投递保持冻结，不混装或覆盖。

```text
python3 <tools>/790_host.py stage1 --phase-dir <actual-P-phase> --binding-sha256 <actualSHA> --fixture-name fixture790-01 --split-name split790-01 --manifest-sha256 640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84
python3 <tools>/790_host.py edge --phase-dir <actual-P-phase> --binding-sha256 <actualSHA> --fixture-name fixture790-01 --split-name split790-01 --manifest-sha256 640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84
```

S1为原data-only admin，441对真实任务、40项目原CLI scope；S2是仅stdlib/edge/严格CA的真实登录及每对提醒create+dedup。完成metadata给出packet/control/CA路径和hash，不输出密码或session。应核S1 selection_sha256与两臂seed_manifest_sha256一致；若前提不同，先保留差异，不能称同夹具对照。

5. LOAD通过既有受限私网TLS或一次性加密运输仅接收control.private.json/session.private.json/ca.pem，逐字核APP公布SHA与CA，保存新私有输入目录0600。不在聊天/UI/日志打印或base64展示私包；不得发送账号/DSN/候选到LOAD。安装相同工具根及`load-delivery.json`，额外load脚本10113B/SHA01b7185a73f5a1a1baa42d78f4a9236dd51c433bd2f1592183c29e97dd08965c，不改变上述七文件manifest。

```text
python3 <tools>/790_load.py --inputs-dir <new-private-inputs> --output-dir <new-absent-results> --control-sha256 <APP-actual-controlSHA> --packet-sha256 <APP-actual-packetSHA> --manifest-sha256 640b3d386a756547d940b638ef6ccfc9bc49adaa2c071a2794aca8464b2edd84 --expected-host <actual-LOAD-hostname> --python-image <proven-official-python-alias> --python-image-id <proven-LOAD-actual-image-Id>
```

先offset0的1客户端20循环80请求，再offset1的40客户端5循环800请求预热；计量用offset41的400组全新任务，5循环8000请求。每客户端四操作GET→contract→block/unblock→existing-reminder-dedup，复用连接、无重试。每轮90s上限，任何失败、deadline或不完整请求都终止、私包不可继续。预热不代表所有16个进程/连接都已完全热身，需真实逐worker/连接数据另证。

6. root保存完整数值资源和终态后保卷停止P7所属环境，再全新P16 namespace重复以上流程，同源/同seed/同anchor/同客户端设置；不并发跑两臂。P7结果不能当P16或新产品通过。正式7-role独立600秒另开namespace及中性准入：真实scheduler token和首轮scan完成后，需专门协议快照既有稳定事件/版本并走dedup-only；当前790要求真实fresh create，因此不能直接挪作正式准备。

P7/P16本轮结束后原云数据仍由root保留；账号、private session及候选不得进Git。不得将本文AI操作写成学生本人亲改/亲测研究经历。
