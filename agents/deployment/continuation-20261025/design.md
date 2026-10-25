# 新一轮部署准备器设计（未执行云操作）

部署 AI，基线 `ade5e4c1998b4c2f014afde8c011645c6c5a7412`。2026-10-25 新授权继续开发，原累计费用上限100元保持；本岗不购买、连接或操作云，不发布账号余额。源码规模与云性能均未由本阶段解决。

旧 bootstrap、TLS、fixture、资源采样与导出有10月24日的源和绝对时间。不得改原文件或在进程中覆盖其全局常量继续运行。本阶段新增只做本地文本物化的 `deployment/round-prepare.py`：输入根审定的精确源、本轮ID、部署/采样/恢复/释放窗口和进程连接预算；从固定基线的七个公开Git blob按明列位置生成新文件，每个原模板SHA、变更位置及生成SHA留在派生清单。没有执行器、网络、Docker或账号API。

七件包括 bootstrap、ECR BuildKit来源策略、AliPyPI外置Dockerfile生成器、TLS逐阶段控制器、应用七服务采样、负载机主机采样、资源文件导出。原摘要、严格CA/IP验证、固定七服务、只读采样、O_EXCL/NOFOLLOW、私有模式、阶段cap及source-clean校验保留。新TLS overlay仅增加明确worker命令与MySQL max_connections配置，新增进程预算可见，不修改生产Compose默认4worker。

本轮ID衍生唯一 `/opt/t44-<id>`、`/run/t44-<id>/app`、`/run/t44-<id>/load` 和Compose project。物化器要求原模板hash逐字一致、所有允许替换次数准确、生成Python可编译、生成Bash语法由本模块合成检查覆盖。输出目录必须是私有本地所有者0700父目录下的新目录；文件排他0600，失败不覆盖或自动清理，清单只在全部完成后写出。

时间：本轮issued不晚于当前60秒，所有时间均UTC秒级；`now < operation_deadline <= sample_end`，采样→资源恢复至少10分钟，恢复→释放至少10分钟，释放在issued后不超过4小时。生成器不会替根延长任何操作；新文件仍保留绝对截止与最多120秒/原阶段时间预算。采样最大时长显式600～10800秒，绝对截止优先。新增UTC/perf/monotonic anchor为非原子取点，不证明跨主机时钟误差已知。

源 `MySQLSettings` 当前默认每engine5+10，运行值必须另观察；声明上界为`15*(worker+2)`（consumer/scheduler），另预留30给两个临时operations进程。W=32时最低540，建议选640；W=64时最低1020，建议选1280。仅提高连接上限不证明内存或吞吐足够，也不证明当前用了全部连接。实际机器CPU/内存、worker argv、pool、MySQL max_connections/连接峰值、镜像ID/RepoDigests须由root在运行前后取得。资源扩容与软件收益分开，性能报告写真实硬件，不猜旧502原因。

供应链：原三个FROM和MySQL/RabbitMQ/nginx摘要固定不变；ECR只映射同摘要的官方镜像，拒绝其他DockerHub来源。AliPyPI仅HTTPS channel变更、require-hashes与完整lock不变；所选新源如改变Dockerfile/lock则原生成器会拒绝，须另做来源审查，不自动改pin。

凭据夹具：旧launcher包含旧receiver证书指纹与worker SHA，并有10月24日expiry断言，本准备器**不生成/不执行它们**。下一轮须由root取得fresh独立实例的公开recipient材料与backend责任岗确认的worker/admin SHA，再做单独绑定审核；旧密钥、Token、目录和密文不得沿用标签。

根在购买前录入当次真实实例/盘/流量报价并分配本轮预算（不能超过剩余额度）；按`(app+load+盘)小时价*最长时长 + 两机公网出站上界 + 余量`核算，实际账单再核，不把计划数字当厂商自动封顶。根需事先保存计划释放时间/系统盘随释放的成功回执。采样结束后每台仅将显式路径和完成SHA交给新exporter，生成单文件tar.gz，用官方云助手单文件下载，再本地全包/成员SHA复核；20分钟恢复余量不能被新测试挤占。

本阶段测试仅本地临时文本、AST、路径/时钟/连接预算及排他写入边界；不执行生成的main、不读本机proc、Docker、SUT或旧独立私件。原正式400客户端/600秒/零错/270ms门槛与独立测试准入均不改变。
