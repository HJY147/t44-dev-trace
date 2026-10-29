# 同实例复用云阶段：执行前设计

本岗只准备本地可审脚本/配置/CI打包，不操作云UI/浏览器、实例生命周期、网络或账户权限。root独占官方云助手/Workbench，实际两节点属性/地址仅按root转述放忽略目录0600 nodes.json，公开只用app/load代称；本岗未云端实核。用户要复用同两实例，不在失败后释放重买。产品935只准开发profiling；未来backendDomainV2明确新SHA再构建新镜像，旧935绿不得套用。

## 顺序和最低回执

1. deployment/cloud-reuse/01-probe.sh：app/load各一次只读inventory，uname/UTC/monotonic、逻辑及affinityCPU、内存/FD/cgroup/disk、NTP、包版本、Docker/云助手/原安全组件状态、Ubuntu源host、接口/路由/监听/DNS。stdout JSONL，原网络身份属于私有回执，存.runtime，不公发。末mutation=false只说明此probe不改系统。
2. 02-ubuntu-packages.sh：显式role和未来15min..12h内operation UTC deadline，root/Ubuntu22.04/amd64、dpkg无中断先验；仅该命令的临时sourceslist指向Ubuntu官方HTTPS jammy/update/security并使用已有Ubuntu archive keyring，原全局源不改，无新key/第三方源。安装docker.io/Composev2/buildx及CA/curl/OpenSSL/Python3/git/gzip/tar，分update240/download600/install480，保留最后120秒，不自动upgrade/remove/repair/全局清理，不停安全组件。只启动Docker daemon，可能由官方包postinst建立标准bridge/iptables，未启动产品/拉镜像/开公网端口。记录actual候选和安装版本、Docker server及Compose>=2.24。Ubuntu22系统Python3.10不假称3.12；通用Linux TLS canary/冻结工具后续可用已固定官方Python3.12容器，不改冻结工具、不引PPA。
3. 官方GitHub CI按完整source_sha单独打包。固定官方Python/Node/Nginx/MySQL/Rabbit摘要先pull linux/amd64，再从准确Git archive的明确构建子集构建app/web，save+gzip+artifact。实际archivebytes、镜像configID/上游RepoDigest/平台/构建label/依赖锁/工具SHA/包bytes/hash一起留manifest。没有运行DSN/token/数据/私钥。华东若DockerHub受阻，只传这个官方artifact，经root官方云助手/Workbench上传并核manifest SHA与完整archive hash后dockerload；不用第三方未知镜像。load后验证configID/标签，不假定RepoDigest必随save/load保留；新alias只指原官方bytes，不换镜像。
4. app独立newrun/project/schema/CA/vhost/credentials，TLS仅监听app私网地址，load按新CA+私网IP严格校验，MySQL/Rabbit/API均不映射公网。保留六业务服务，TLS明确为第七服务；服务进程仍产品原CLI，单真实项目scope/TTL3600/root签发，不通配、不替独立fixture造数据、不接本机7980或旧schema。runtime overlay仅明确worker/pool预算和新source镜像绑定，Docker/Compose实际参数必须回执，不降低认证/审计/锁。
5. 独立phase另准入，部署只canary/idle/资源身份，不预填400并发600秒、覆盖、功能/性能。原始资源UTC+monotonic对齐并完整闭合SHA一键官方单文件回收；不改旧10月24日工具常量或把旧证据改标签。

## 持久窗口和费用责任

root转述本次两机合计约6.281元/h，示例10h约62.81元，公网0.8元/GB另计，非本岗实读报价、非最终账单。root必须先核累计实际花费/盘流量/下载预算和原100元剩额；不能把100当厂商自动封顶。自动释放由原23:30BJT拟调明早06:00是root计划，本岗不操作/不声称保存成功。每一轮测试有新的绝对UTC+单调时钟时限，不延长旧grant。

服务器端后续明确安装持久systemd timer（UTC OnCalendar、Persistent=true），只stop本run已绑定的container IDs及精确owned generator unit，正常停止保留卷/镜像/日志；不dockerprune/down-v/drop/关机/释放ECS。服务器timer防本机/agent失联，不等于账单停费。root本机另保有预算/释放页面核对和原始证据下载责任，不能只依靠会话活跃。计划停止前留至少30min完整回收窗口；根实际核自动释放、最终账单，收费与资源存在单列。

## 未执行/待下阶段

当前仅probe/packages脚本、bash -n及probe内嵌Python语法验证，无云执行/安装/镜像构建/部署/业务/独立/600s结果。CI打包、校验加载、新TLS/overlay与stop materializer仍待实现/审核后单阶段交root，不把设计当运行。

主源：Ubuntu官方jammy-updates docker-compose-v2 https://packages.ubuntu.com/jammy-updates/docker-compose-v2 （2026-10-25浏览，版本2.40.3但真实安装另记）；Docker save https://docs.docker.com/reference/cli/docker/image/save/ 与load https://docs.docker.com/reference/cli/docker/image/load/ 。Docker厂商仓库版与Ubuntu维护docker.io区分，本阶段不混装。两个Ubuntu docker.io/buildx通用页抓取timeout已发生，不编造版本，真实candidate由脚本观测。
