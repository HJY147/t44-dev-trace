# 显式新轮次准备与执行清单

本文件是部署AI提供给总协调的可审操作方案，**未创建云资源，未执行生成脚本**。原10月24日文件、期限、失败与回执保持不变；不允许给旧进程改全局变量后续跑。

## 1. 生成前的具体输入

`round-prepare.py`只读取本地Git对象和本人0700父目录下的0600计划，排他产生新工具包。计划必须由root填写真实值，不能将下面的历史示例直接当新准入；过期/顺序不正确会拒绝：

```json
{
  "round_id": "r20261025a1",
  "source_sha": "ade5e4c1998b4c2f014afde8c011645c6c5a7412",
  "issued_utc": "2026-10-25T06:00:00Z",
  "operation_deadline_utc": "2026-10-25T07:30:00Z",
  "sample_end_utc": "2026-10-25T08:00:00Z",
  "evidence_deadline_utc": "2026-10-25T08:20:00Z",
  "release_utc": "2026-10-25T08:40:00Z",
  "api_workers": 32,
  "mysql_max_connections": 640,
  "sample_max_seconds": 5400,
  "run_budget_cny": 40
}
```

唯一源提交必须在本地仓库中存在。工具包包含七件新副本和`derivation.json`：每件模板来自固定ade5 Git blob、旧SHA、每个允许替换的old/new/次数、最终SHA/bytes都可核。`source_policy_output_sha256`仍是原四规则JSON的f910…，不是新helper自身SHA。三个FROM、数据库/消息/代理镜像摘要不改变。所选新源如改变Dockerfile/ignore/requirements.lock，原严格生成器会拒绝，不能自动更新pin。

在项目内忽略的私有runtime新目录保存计划后，root可本地物化；此命令不需要云账号或Docker：

```sh
python3 deployment/round-prepare.py --plan /absolute/private700/round-plan.json \
  --repository /absolute/project/repository --output /absolute/private700/new-bundle
```

只有新的本模块源码及其生成差量通过审核后，才将包按SHA复制到新主机的`/run/t44-<round_id>/app/tools`；load上仅需主机采样器和资源exporter。新目录逐级root-owned0700，文件0600，不覆盖旧轮次目录。root复核目标Ubuntu24.04 amd64、CPU/内存、现有同VPC/安全组，使用已授权云助手/Workbench；不新建AK/SSH密码/权限或公网业务入口。

## 2. 配置预算和环境实际回执

当前源每engine pool5+overflow10只是源码默认，须实际观察。worker W时，API+consumer+scheduler上界为`15*(W+2)`，另给两个临时operations进程30连接；因此W32最低540、示例640；W64最低1020、可选1280。两组都需要实际内存与连接峰值验证，不假定把max_connections提高就自动有相应内存/吞吐。提高硬件或worker后，报告写新硬件与配置；不能以旧8CPU的成绩当同环境前像。

运行前后用准确选定DB的本机管理通道取得并私有保存`SELECT VERSION(), @@max_connections, @@transaction_isolation`及`SHOW GLOBAL STATUS`中的`Threads_connected`、`Max_used_connections`，不要在终端输出DSN/密码。另存API容器实际Cmd、运行进程数、每进程pool设置、镜像ID与RepoDigests/构建来源回执。声明字段和实际观察分开；没有观测则NOT_PROVEN。不得通过减少认证、审计、锁或提高超时掩盖失败。

价格必须由root当次购买页读取，按实例/盘小时价、最长存续、公网出站上界与余量计算并分配本轮预算，**不超过原累计授权的剩余额度**；本工具不读取余额，不下单，不认为run_budget是厂商自动封顶。创建时即选择按量、不自动续费、系统盘随实例释放，确认自动释放成功的实际页面字段；保留计划和最终资源不存在的两个证据，账单另核。

## 3. root逐阶段执行，不自动串起

1. 先校验生成脚本SHA，运行新bootstrap的`inspect`，再分别`packages`、`source`；不执行旧10月24日脚本。source得到计划衍生的`/opt/t44-<round_id>`，HEAD必须是精确source，tracked clean，公开tracked文件644/755、目录755、根750；私有.env保持600。
2. 在启动任何服务前生成新配置。现有`ops.py init-env --output <app-runtime>/fresh-defaults.env`仅生成随机256bit凭据；root在同一受控Python进程用本源`load_env`读取这份私有文件，仅将COMPOSE_PROJECT_NAME改为derivation.plan.project、MYSQL_DATABASE改为derivation.plan.database、RABBITMQ_DEFAULT_VHOST改为该project，再以`O_EXCL|O_NOFOLLOW`/0600写入source/.env。不得打印字典、覆写已有.env或复用旧密码。生成器新TLS明确拒绝project/DB不匹配；fresh-defaults.env保留在私有目录而不提交。
3. 新ECR helper生成新policy文件并核实际f910…JSON hash；新AliPyPI helper只产生外置Dockerfile及同名ignore。构建使用`EXPERIMENTAL_BUILDKIT_SOURCE_POLICY`和固定linux/amd64、原FROM摘要/require-hashes。API用外置Dockerfile+本源context，web用本源Dockerfile；这是渠道变更后的构建，不能说原Dockerfile字节构建。每次独立build的外层/内层界限需在operation_deadline前保留120秒；保留完整私有stdout/stderr和实际退出码，timeout后先观察daemon是否仍有任务，不盲重试。
4. 将本轮私网IP以唯一`T44_APP_PRIVATE_IPV4=...`行保存在app-runtime/private-network.env（root600）；新TLS helper的`prepare`使用`--source-root <source>`、`--runtime <app-runtime>/tls-round`和该private-env。验证CA/IP/server用途/expiry/keypair；CA私钥不挂载。随后分别config-check、pull、infra。新overlay唯一覆写API worker命令和MySQL max-connections，其余安全/镜像/服务定义继承固定模板。
5. 明确`--database <derivation.plan.database>`先plan后`migrate --execute`，然后按已核数据口径seed（40项目/6000任务/9000依赖/15000评审决定）；实际计数另观察。原seed CLI/业务语义未改，失败不清空未知DB、不用seed成功当验收。
6. 初次scheduler凭据与独立测试凭据分别处理。旧fixture launcher硬绑旧recipient证书/worker/source/expiry，本包**不生成它们**。root应从fresh独立实例仅取公开recipient材料，要求后端责任岗基准确source生成新中性夹具worker与专属服务凭据封装，再独立审核；不得转递明文密码/token、复用旧私钥或让开发读私有用例。原token阶段只在scheduler停止时首次发行，不自动轮换。
7. 再用新TLS helper的start启动六业务服务+第七TLS gateway，逐个healthy不等于业务验收。取得严格CA+IP的私网连通回执及实际配置/镜像身份，交root做中性环境包；独立tester另冻结/准入，未准入不得发正式负载。
8. 容器与源码身份核验后，在app运行生成的七服务sampler，在load运行host sampler。两者新context含UTC、perf与monotonic anchor、固定五/proc；是非原子约10秒离散样本，NTP/跨机误差仍须另观测。高CPU、重传等不直接归因502；container_content_attestation=false仍保留，必须和构建回执一起理解。若需要逐个502归因，应另审不记query/auth/body的request-ID/upstream定时日志方案，不能用这些10秒采样代替。

## 4. 收证与释放

绝对sample_end之后，只将各采样器完成摘要给出的**显式raw路径+完成SHA**交给新resource exporter，host分别app/load；不扫描私有目录。新恢复窗从sample_end到evidence_deadline，exporter仍仅允许固定前缀/完整七服务五proc，并以原字节raw+manifest生成每台单一tar.gz。

用阿里云官方云助手的单文件下载任务下载该tar.gz；本地核whole size/SHA、内部raw/manifest的SHA与字节数。浏览器“复制成功”不等于下载完成，若剪贴板不同步可用已审固定文件只读分段传输，但不得读未知私有目录或用非官方跳板。原始私有遥测、证书/Token、签名URL不入公开Git。独立测试结果另按其公开运输协议只搬运不透明密文，不解密用例。

到evidence_deadline仍有未回收文件时，停止新测试，先保全已完成证据；不能借新manifest悄悄延长已运行脚本或既有计划释放。root核自动释放成功字段，并在release后实际核ECS与盘不存在；实际费用/账单状态单独记录。新helper本身不删除、释放、停服务或联系云API。
