# R30 0b 有限窗口 runbook

deployment AI；本文件是可审查准备，不是开机授权。root 在制品及QA准入后决定是否启原两机。本岗没有任何云生命周期、SSH、账号/session读取或SUT操作。

## 已完成的静态/免费制品出口

- 产品源：`0bffe0c535e5897890aebf30879fdd3839dc52d6`。构建工具提交：`61179fca68f09e89b3f8de24b910dd42ae78a434`。免费标准 `ubuntu-24.04` 构建 [40833943007](https://github.com/HJY147/t44-dev-trace/actions/runs/40833943007)，不是云验收。
- artifact `12880320744`，官方 ZIP 94895161B，SHA256 `69b2522744b9b9c4d0bd2845c04aeb4bb570c2efe1f8c84645950cc595fd7b4e`；官方API digest与完整下载bytes相等。2026-11-05T07:13Z过期，届时不能用旧短链或跳过来源检查。
- backend bundle manifest SHA256 `b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345`；source manifest `0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b`；Git source tar SHA `275970aa18117751e3a4fc8c404d0750cb9698310a70146d64061a634c37bf09`。
- 一个新backend：`t44-backend-r30:src-0bffe0c535e5897890aebf30879fdd3839dc52d6-r30ci40833943007`；保存的config `sha256:8e3e2a9d1f2d4706072eb0502b041d3db49d32b7a2fc48ac6b39fc2162336845`；压缩镜像94620657B、SHA `650ad1a2782396bdebfb05d722685d7ba9a65e519786447972612f0a1c407656`。源上下文62件（完整53backend），真实CI非root/read-only/network-none文件探针匹配全部60运行件。
- 官方Python pin、CI实际RepoDigest和四层有序DiffID前缀单列；新backend每层归档SHA/DiffID、config/labels/platform/ordered-rootfs单列。APP Docker29 containerd的实际 `inspect.Id` 可是descriptor，必须用原 `image-proof.prove_role` 从保存的原字节证明descriptor→config→各层，不能只比较 `.Id==8e...`，也不能跳过检查。
- 新 `r30-window.py` 只适配该backend-only manifest。旧v4预算模块305f9e原字节继承；原arm/infra/actual-budget/migrate/idle/scheduler/stop等函数不变，只有verified_images接口和prepare新run-id约束改变。旧935/f4/f7 builder、grant、截止、成绩不动。

## boot 前 ready 清单（root逐项打勾）

1. [x] 官方artifact已完整本地回收；7对象集、每件bytes/hash、全部源文件、官方层与backend配置证明通过。本地路径 `tmp/761_deployment_preparation_r30/official-artifact-12880320744/`（镜像/ZIP未入Git）。
2. [x] 部署20项离线边界、独立于产品CI的真实镜像文件探针和新window adapter验证完成；证据分别存档。没有新Linux加载、跨VM或完整工具接受事实。
3. [ ] root完成新适配代码准确HEAD审阅；QA只看其独立方法/已公开中性资料，开发不接触其PRIVATE。完整Linux工具执行器8CPU/原官方Python3.12.15适配仍由QA另出公开准入，不拿generic subset代替。
4. [ ] root确认新 run-id、四新端口、T0、绝对 `WORKLOAD_STOP_UTC`、`COST_STOP_UTC` 与T0+45min最终复核界限。建议 workload=T0+35min、cost-stop=T0+40min；不在无窗口时预签任何真实日期。
5. [ ] root/后端责任岗为准确0b另冻结真实seed/四角色/sessionTTL/中性包与新run/source/window接口。现有790 f7/旧16Z/20Z包不可改字重放；旧账号/grant/session不能复用。本岗已单向报root，不接触测试岗。
6. [ ] root准备官方ZIP的新短时签名下载来源或已核本地上传渠道；云端绝不放GitHub PAT。95MB仅给APP；LOAD只给所需PUBLIC工具/新密文中性包，不传backend或原500MB全七镜像。
7. [ ] root核定原APP/LOAD、保存盘和已取消自动释放的复核步骤，准备失败即封存/停机的执行人。当前OFF状态只来自root明确回执，本岗未重新登录云核验。

当前清单仍有root/QA/跨owner门禁，不能把本文件写成“已准许boot”。

## 开机前最后本地绑定（不需要云）

由root填真实run和两个UTC后执行；当前未执行此真实窗口派生。源和镜像固定，窗口工具全新输出、拒覆盖；派生器只接受未来30分钟至12小时截止。

```bash
R30_PACKAGE="$PWD/tmp/761_deployment_preparation_r30/official-artifact-12880320744"
R30_RUN_ID=r30window01
# 由root按真实T0选择；不能粘贴旧2026-10-28日期。
R30_STOP_UTC='<root selected absolute UTC Z>'
R30_PROFILE="$PWD/agents/deployment/preparation-r30/window-$R30_RUN_ID"
python3 deployment/cloud-reuse/r30-window.py derive \
  --package "$R30_PACKAGE" \
  --manifest-sha256 b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345 \
  --run-id "$R30_RUN_ID" --stop-utc "$R30_STOP_UTC" --output "$R30_PROFILE"
```

先核新profile七份代码完整bytes/SHA（含从公开commit8784ba2279ec82834fc967f56b756ed708e20bed取的原factory.py），压缩传输时保留manifest；所有UI完整命令必须实算 `base64(whole command)+description<18000`，不是只算内层payload。公开代码可按本分支最终固定commit通过GitHub Contents API取回（raw/JSON两形状都核bytes/SHA）；不取可变分支。正式deadline包由这一步新生成，测试里两小时future fixture已删除，不可当真实窗口使用。

root本地获取官方artifact：`gh api repos/HJY147/t44-dev-trace/actions/artifacts/12880320744/zip`，排他写新文件并核完整ZIP SHA。传输前取得新的官方短期下载位置只在新私有运维输入中保存。APP HTTPS下载使用正常证书验证、`--proto '=https' --proto-redir '=https' --connect-timeout 10 --max-time 180 --fail`，失败保留part/原stderr，不重用旧链接。先整ZIP exact bytes/SHA，再只允许下面七个普通唯一成员，排他写新目录，禁止 `extractall`：

`backend-image.tar.gz`, `backend-bundle-manifest.json`, `source-runtime-context.tar.gz`, `source-manifest.json`, `frozen-comparison.json`, `actual-runtime-files.json`, `build-metadata.json`。

下载、解包和所有PUBLIC/opaque传输必须在新session签发前完成。不因为180s网络上限失败延长45min费用边界；走封存停止。

## 预计云步骤与硬时间（本岗均未执行）

| T0起 | 实际操作与通过依据 | 失败处理 |
|---|---|---|
| 0–5min | root只启动保留的两原机；核实例ID/私网IP/磁盘/时钟/空闲磁盘/实际配额，核旧timer/receipt只作用旧namespace。不得覆盖或改旧timer和卷。 | 身份、盘、auto-release或资源不符即封存并节省停机。 |
| 5–12min | APP收新95MB ZIP及新profile，核完整SHA/七件；LOAD只收PUBLIC工具。新backend import，六旧cache身份只读复核。 | 缺层/标签/bytes/hash、老tag变化或alias已存在均拒绝，无pull/relabel fallback。 |
| 12–18min | 全新run/数据库/CA/端口/namespace；新Persistent guest停止timer先arm再infra，实际MySQL预算probe通过才migrate/idle；P64、pool5/overflow0保持原方案，384只配置不是实测。 | 未arm、预算或CPU来源不符不进入业务；封存后owned stop。 |
| 18–20min | 完成全部传输/解封、根核公开preflight，完整Linux工具适配及SUT中性材料到位；此后才真实签发四角色/TTL。 | 不足时间或前置未过，不发session，不发业务grant。 |
| 20–30min | root按独立准入另发新run业务授权；执行需要的600s稳定段（若准入要求），连续APP资源＋LOAD完整镜像/尾部；不自动重试/续轮。 | 首错保prefix、撤销本轮执行；不改case/结果/时钟或延TTL。 |
| 30–35min | 主动seal APP原资源、追完整LOAD尾/最终摘要；收PUBLIC结论及opaque证据，不打开QA私包。 | missing明确标缺，不等待拖过费用边界。 |
| 35–40min | 新generation owned stop保卷、collector stop；核本轮无运行容器与资源进程。root provider分别执行原两机节省停机。 | 仍停费优先，保存已落盘prefix；不down-v、不rm、不释放实例/盘。 |
| 40–45min | 分别核STOP/节省停机、自动释放时间 `-`、原云盘保留；记录时间与回执。 | guest停止不等于云停费，provider复核缺失明确未完成，立刻处理而不另开测试。 |

任何新SUT动作必须满足原600秒余量保护；workload硬截止到时仅允许stop/status/封存。root外部cost-stop监督不依赖SSH/guest脚本正常；35分钟后不派业务，40分钟前发出节省停机，45分钟完成状态/auto-release/盘复核。

## APP新制品/缓存/代际命令接口

以下变量由新PUBLIC路径回执填入，不读取`.runtime`旧账号/密钥/session。`R30_ORIGINAL_PUBLIC_PROOF`必须是完整50297B公开镜像证明、hash30b1ca...；`R30_FROZEN_FACTORY="$R30_PROFILE/factory.py"`是派生器直接从精确公开Git对象携带的31415B原操作库，hash `daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea`。当前仓库app-campaign.py已不同，不能把它代入冒原hash；profile任何缺项即停，不读旧私件找答案。

```bash
# R30_HOSTROOT=/root/t44-r30/<new run>; 目录必须新建0700。
# R30_PACKAGE/R30_PROFILE 均为本轮已核传输的云路径。
python3 "$R30_PROFILE/r30-backend-artifact.py" verify-bundle \
  --package "$R30_PACKAGE" --manifest-sha256 b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345
python3 "$R30_PROFILE/r30-window.py" import-backend \
  --package "$R30_PACKAGE" --manifest-sha256 b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345 \
  --receipt "$R30_HOSTROOT/import-receipt.json"
python3 "$R30_PROFILE/r30-window.py" verify-cache --original-proof "$R30_ORIGINAL_PUBLIC_PROOF"
python3 "$R30_PROFILE/generation.py" prepare \
  --factory "$R30_FROZEN_FACTORY" --source-package "$R30_PACKAGE" \
  --upgrade-binding "$R30_PACKAGE/backend-bundle-manifest.json" \
  --upgrade-binding-sha256 b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345 \
  --source-manifest-sha256 0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b \
  --original-proof "$R30_ORIGINAL_PUBLIC_PROOF" --image-proof "$R30_PROFILE/image-proof.py" \
  --run-id "$R30_RUN_ID" --app-ip "$R30_APP_PRIVATE_IP" --stop-utc "$R30_STOP_UTC" \
  --f-tls-port 26443 --f-http-port 18580 --p-tls-port 26445 --p-http-port 18581 \
  --p-workers 64 --p-pool-size 5 --p-max-overflow 0 --output "$R30_HOSTROOT/campaign"
```

端口只是新的候选，prepare实际bind检查；发生占用拒绝，不擅改旧端口映射。CLI保留`upgrade-binding`参数名为旧操作方法兼容槽，其值现在必须是**新backend-bundle-manifest**，新适配器拒绝旧upgrade-binding路径，不能混淆两种manifest。prepare只生成配置，未开业务。

实际prepare返回F/P新phase路径及绑定SHA后，root对获准phase逐条 `generation.py arm`、`config`、`infra`、`probe-budget`、`migrate`、`idle`。每条带`--phase-dir`与完整`--binding-sha256`；migrate/idle另给probe实际输出的`--budget-receipt`及`--budget-receipt-sha256`，不猜路径/数字。scheduler仅获准项目明确scope后独立启动。F/P不并行启动，不把未启phase记已测。

结束时对本轮已启动phase执行 `generation.py stop --phase-dir ... --binding-sha256 ...`，保留卷；新resource-stream按实际binding seal/stop和mirror尾部回执收全。收到真实PID/unit结果后核进程停止，不预写success。provider节省停机和取消自动释放仍由root执行，guest工具不会声称云费已停。

首次build、接收、加载、预检、调度各层证据独立保留；它们都不等于系统性能达标。原f7短测P95与QA772旧NP保持原结论，0b新SUT结果必须另有实际窗口证据。
