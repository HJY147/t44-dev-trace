# 同f7的新20:00Z窗口（新03代码目录）

source仍`f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f`，新截止`2026-10-28T20:00:00Z`。root已核product40692462131四job及Docker40692462380成功；没有改产品，因此此处不重跑完整CI。旧5d/f7-16Z原件不改；root确认旧16Z只有代码安装与backend build，尚无GEN prepare/arm/infra/migrate/idle、F/P grant或业务运行。

新公共代码：

| 对象 | 字节 | SHA-256 |
| --- | ---: | --- |
| profile-f7-2000/profile.json | 2059 | 60660d2a10c6aba9de92bf843270e95ab2014292badc88d6579eac70224e3e66 |
| generation.py | 30497 | 9edafbbff0586b5f77a701bd37f715685fba4169abaae510474343af75a8b427 |
| resource-stream.py | 44082 | 3afd9a0319b5002d0627744df77ae1b642ffc5cc9b0e01276038149154156e9c |
| mysql-budget.py | 21599 | 305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d |
| backend-upgrade.py | 23566 | d2fc28b2f0c19b19a81c2ac10c0712767c6182d8b3e2b5e7f2346da62bf2bbf5 |
| source-artifact-receive.py | 4972 | ce064af587197a9959b6f323d7f4b61fcc1cb2f5560b3e16f551836ec7e1b6b5 |

`delivery-f7-2000/01-part-000.sh`至`05-part-004.sh`依次执行，再`06-verify-install.sh`。manifest SHA`60c234aca7b0eded3382ef209b079d5ac45ebe55d8d93e1ba7d10b7b4d6060f3`。完整命令raw最大11337；包含整个shell/python heredoc后再base64加256描述最大15372，低于18000。不能将多个分片重新套成超限的一条base64命令。目标全新`/root/t44-r9/v4-code-20261028-03/profile`，O_EXCL拒覆盖，无服务启动。

另附固定PUBLIC commit的`install-via-github-api.sh`与完整outer编码证明。它下载并核六条完整脚本SHA/bytes、按序执行同六条原件，无Token和可变分支；root可直接提交这个完整wrapper。原六脚本仍可分别使用，勿再二次套base64而只计算内层长度。

同源镜像可以保留原身份复用，静态差分证明在`source-image-reuse.PUBLIC.json`：builder/receiver/helper与f7-16Z逐字相同，build CLI与binding字段没有stop/deadline；GEN只改HARDSTOP，resource同时换新GEN SHA，source与source-file-set不变。新GEN运行时仍严格检查实际build/source/archive/image证明，不因这个静态结论跳过校验。以下完整官方值来自root实际构建/下载核验，部署岗未读取私有原binding：

- 实际image：`sha256:a7d3dde54efda1405bbd7d9f5f5b7c5a6439f1afd1dc8c50b2ed8b37625fa5da`。
- 原buildbinding：`/root/t44-r9/backend-f7-build-01/upgrade-binding.json`，SHA`df84e9b1dbcf8946209ae6ae0ea868d63dc96b60d01c2bae7f3d621e65b311b0`。
- 官方source已接收目录：`/root/t44-r9/source-f7-checked-01`。
- 官方manifest SHA：`3368534aececbb5441225e7859338aa3079b6e41798e38673bd8f337f8993577`。
- 官方inner ZIP SHA：`70d09d1f99d8a4fced5b4f8c5a5e9174d8a549cdc305dd8fd2689834fe7ad86b`。
- archive SHA：`8f4f6f9275b2f7fdb4cdfbf0f94a3a804fc61c84402446028b07127c04e4b050`。

不重建/重贴a7d，不重复源码运输，不用本地f04/51c75替代上述官方值。新20Z profile没有实际新phase/CA/binding，必须另prepare；旧16Z没有任何需延长的已启动业务绑定。

以下是新namespace/端口的**计划值**，尚未实际创建。prepare会检查全新目录、namespace和端口占用，冲突即拒绝；实际ID/CA/DB身份以root返回的新回执为准。`APP_IP`从root实际实例库存填写，不猜资源ID。

```bash
GEN=/root/t44-r9/v4-code-20261028-03/profile/generation.py
CAMPAIGN=/root/t44-r9/campaign-f7-2000-01
python3 "$GEN" prepare \
  --factory /root/t44-r9/campaign-935/p/controller.py \
  --upgrade-binding /root/t44-r9/backend-f7-build-01/upgrade-binding.json \
  --upgrade-binding-sha256 df84e9b1dbcf8946209ae6ae0ea868d63dc96b60d01c2bae7f3d621e65b311b0 \
  --source-package /root/t44-r9/source-f7-checked-01 \
  --source-manifest-sha256 3368534aececbb5441225e7859338aa3079b6e41798e38673bd8f337f8993577 \
  --original-proof /root/t44-r9/proof-v2-01/proof.jsonl \
  --image-proof /root/t44-r9/image-proof.py \
  --output "$CAMPAIGN" --run-id r28f720gen01 --app-ip "$APP_IP" \
  --f-tls-port 24443 --f-http-port 18580 --p-tls-port 24445 --p-http-port 18581 \
  --p-workers 64 --p-pool-size 5 --p-max-overflow 0 \
  --stop-utc 2026-10-28T20:00:00Z
```

F4/default5+10与其他Settings角色默认原样；仅P API显式5/0，64 API上限320加reserve64=384；384仍是配置先验，实际MySQL必须查询。profile准备不等于业务准入，root按新授权分别选F/P，业务不同时运行。尚无新F/52/P授权，不因包就绪越过独立保护证据核验。

每个新phase先用实际prepare返回的`PHASE_DIR`与`PHASE_BINDING_SHA256`：

```bash
python3 "$GEN" arm --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$GEN" config --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$GEN" infra --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$GEN" probe-budget --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
```

infra只MySQL/RabbitMQ；probe只读实际CID/hostPID-starttick/StartedAt/image/项目/数据库/serverUUID/@@max_connections。使用其实际PUBLIC回执path和完整SHA，所有迁移/业务/scheduler动作前再核同一实例；缺回执/不足384等均拒绝，不能拿其他实例或planned384补空。

```bash
python3 "$GEN" migrate --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256" \
  --database "$ACTUAL_PHASE_DATABASE" \
  --budget-receipt "$ACTUAL_BUDGET_RECEIPT" --budget-receipt-sha256 "$ACTUAL_BUDGET_RECEIPT_SHA256"
python3 "$GEN" idle --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256" \
  --budget-receipt "$ACTUAL_BUDGET_RECEIPT" --budget-receipt-sha256 "$ACTUAL_BUDGET_RECEIPT_SHA256"
```

operation锁仍是`<phase>/.v4-operation.lock`，0600、NOFOLLOW/CLOEXEC、flock EX|NB/50ms poll/默认10秒上限30；backend直接SQL每步同锁内admit至输出读取，调用GEN前释放。observer独立1槽，health4、单admin15和consumer/scheduler各15仍明列。实际Config.Env只筛池容量并核consumer/scheduler默认，不打印其他ENV。P bootstrap沿原seed44/04:00Z anchor显式producer，不能改默认now；诊断不启动scheduler，凭据scope也只能实际IDs。

资源collector/mirror也须使用新03的resource helper与新的phase/stream绑定，deadline不得越过20Z；不能直接复用16Z controller/grant延时。观察器只读、缺值标缺；旧270/active400/600及LOC门禁不变。新SUT动作须剩600秒，因此19:50Z后不新启动；cleanup/status不受预算锁阻塞：

```bash
python3 "$GEN" stop --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
python3 "$GEN" status --phase-dir "$PHASE_DIR" --binding-sha256 "$PHASE_BINDING_SHA256"
```

stop只owned容器、保卷；VM费用/最终停机由root负责，不自动删除或释放。此交付仅本地派生/差分/完整运输验证，实际云安装/准入仍由root完成并留原回执。
