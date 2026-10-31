# DIRECT_PRESSURE r30directp16

当前仅本地准备。下次由用户启动Mac单入口后，自动运输/启动既有服务、APP一次fast_bootstrap、CMS五件运输、LOAD调用本入口。没有原profile/approval/scan/grant人工轮次，也不执行maintenance、改计划、工期阈值或额外资格读取。永久SSH连通不改变生产业务鉴权或token实际有效性。

新workspace `/root/t44-final-20261031/QA753_DIRECT_P16`。新run `r30directp16`；原p15保留不覆盖。工具core与functional原字节SHA分别为9cf747e308969ceba37e2cfcfa6591def45e118ad928c4f310f57b6ecf37542a和0e9245fc9cbc1f801907a47ec0aa8a00695358f09f5332f661fa13742c0b4b64。原ENTRY/adapter随安装bootstrap兼容保存，其prepare/execute不用于DIRECT模式。

## LOAD自动安装与调用

总协调只搬本PUBLIC目录，不能搬独立岗本地PRIVATE。按DELIVERY_MANIFEST全成员SHA核包是离线工具身份保证，不是追加业务准入。W必须新建、不能覆盖。已存在run marker或结果目录即拒绝重复发压，不会删除重试。

```sh
W=/root/t44-final-20261031/QA753_DIRECT_P16
mkdir -p /root/t44-final-20261031
mkdir -m 700 "$W"
cp -R /root/t44-direct-p16-public-staging "$W/public"
sh "$W/public/INSTALL_DIRECT.sh" "$W" /root/t44-r9/r29-load-key-01/load-only-private.pem
# ROOT Mac自动bootstrap/CMS seal5件→LOAD open到全新目录之后：
sh "$W/public/DIRECT_PRESSURE.sh" "$W" "$NEW_OPENED/inputs/session.private.json"
```

LOAD收件RSA仅原LOAD保管，公钥DER SHA=385f2632f9c82260639db1c0994ebf951a9c1e9efa97a2cd5249b190220f5e66。原CMS cert下次按原cert子命令使用同key自动更新，仅PUBLIC证书经Mac至APP；不新建RSA、不导出私钥。本工具胶囊包含全新backup.key，和p15 key不同；外部运输密钥单独OAEP-SHA256封装。无旧grant消费/复用。

`DIRECT_PRESSURE.sh`自动运行8CPU/8GiB/2048pids容器，调用密封BOOT的 `--workspace /private --inputs /direct-inputs/session.private.json`。输入必须原DIRECT_INPUTS_V1（producer_schema=T44_FAST_BOOTSTRAP_V1）：environment.origin/connect_ip、四sessions、inventory.clients完整400份、每份原transition_task/escalation_task/escalation_event当前快照、rule_version、identity、counts/fixture等保持真实生产者字段。同目录ca.pem用于真实TLS验证，原五件会保存在本run私密inputs以便封存。输入额外字段照原件留存。current event为null或任务缺失则明确BOOT_FAILURE，绝不虚构事件/修复生产。CAS/真实业务返回不符合原断言仍失败。

接口生产者依据53acbb28指定INTERFACE与MANIFEST；bootstrap SHA ba0c8ab216dd643ed83a27d2ce4479b459ad998451c9530238f2134658dbd72d，runtime_support SHA bec01e4038ef4ca5d6ba6d048e96fb8c7cb32933f705fd65a6995d24d9753170。独立岗只读了这两份中性接口，不读开发测试/讨论。

## 真实测量与明确豁免

BOOT直接实例化原runtime.Run.execute；没有调用旧preflight/grant/profile。保留400客户端栅栏、60秒warmup、600秒steady、四类P95各≤270ms、原10个完成分钟各≥1000、零错误、HTTP/schema/业务/审计/后置与完整raw/wire/响应headers、加密认证/footer及producer/writer生命周期。技术性15s单请求、40s后置、900s执行监督仍存在，用于失败退出；它们不是取消的业务工期阈值。

用户取消的原额外准入：人工身份/一次grant轮次、完整prerequisite scan、maintenance/horizon修复、planned_end准备阈值、旧会话最小TTL准备阈值。未运行这些就不具备原全验收证据。因此外层固定 `DIAGNOSTIC_PRESSURE_NOT_FORMAL_ACCEPTANCE`、formal_acceptance=false，即使原metrics显示PASS也不能当原正式全验收通过。生产真实token到期/业务工期等仍由原服务执行；不改响应、不降HTTP错误或延迟指标。

BOOT的读取是工作负载构造（400client/800互异task IDs及Task/event存在），不额外访问生产做资格检查。current snapshot/fixture/count来源由新生产者如实记录；历史import/config/source provenance不冒充本次完整在线源审计。

## 自动收尾与封存

测量容器退出后，入口自动在本项目独立 `/root/t44-sealed-directp16-tmpfs` 恢复14GiB tmpfs，随后调用SEAL_DIRECT.sh。它强制所有owned测量容器退出、真实MemAvailable≥29GiB、6树文件数/大小守卫与cipher上界≤13.1GiB；后处理容器28GiB/2CPU/64pids。运行测量仍8GiB。无writer的BOOT初始化失败可按明确未启动producer标记封存，其他情况必须真实writer_finalized。

产物 `/root/t44-sealed-directp16-tmpfs/r30directp16.753backup` 及同名.receipt.json；tmpfs易失，Mac单入口必须**无论测量exit是否非零，先自动回收密文+receipt并核大小/SHA**。测量FAIL/NP不得跳过回收；不自动重跑。然后独立岗本地用新key核原backup认证/全文件hash/raw/footer/原指标，完成后通知用户停机，不调用VM stop。资源守卫失败保留原rootfs raw，不删除旧数据。

本DIRECT入口没有云控制/关机/自动重试/继任run。实际生产Linux安装、真实APP bootstrap、真实测量及云侧峰值尚未执行；本地loopback演练只证明工具可执行，不是产品性能结果。
