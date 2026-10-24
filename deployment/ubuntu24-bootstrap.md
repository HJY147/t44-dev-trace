# Ubuntu24.04应用机分步准备（待root审查/执行）

准确产品C固定`0dfb55c2191200d947c5423fd9ee74bb0812cc5a`；今天北京时间2026-10-24 17:00（UTC09:00）自动释放/20元预算不变。此文件及脚本只在本地编写，未在云机执行。仅面向新t44-app，不在发压机安装应用栈，不使用阿里云key/token。

先经官方Workbench取得root终端；将审查后的`ubuntu24-bootstrap.sh`作为文件上传/粘贴保存，核对本岗交付SHA后逐阶段调用，**不要将下载内容直接管道给shell，也不要把下面阶段串为一键执行**：

```sh
bash ubuntu24-bootstrap.sh inspect
```

核对确为新应用机、Ubuntu24.04 amd64、截止前，APT源仍是Ubuntu签名发行仓库/官方镜像且universe可用；无第三方候选替换。随后单独执行：

```sh
bash ubuntu24-bootstrap.sh packages
```

只补缺失python3.12/git/CA与Ubuntu仓库docker.io/docker-compose-v2/docker-buildx，不升级已满足项、不换已有DockerCE、不加仓库/公钥、不关闭APT签名。APT update180秒、下载300秒、离线安装240秒，各网络请求30秒/重试1，锁等待60秒；各阶段还扣除17:00前120秒余量。包安装可能由包维护脚本启动Docker服务；脚本不改防火墙/安全组/登录凭据、不开放Docker TCP、不启用收费产品。安装或timeout失败立即停，保留实际错误；若dpkg被中断，root先核包状态，不自动repair/重试/续时。无包候选（如universe未启用）或已有不兼容Docker时交root核实，脚本不替换源/卸载组件。

```sh
bash ubuntu24-bootstrap.sh source
```

该阶段以匿名公开HTTPS、禁交互凭据，fresh init/fetch单一完整SHA并detached检出（等效最小精确克隆），Git下载上限360秒，低速窗口30秒；验证HEAD及tracked字节未改。目标`/opt/t44-c-0dfb55c`已存在时仅复核，不覆盖或reset。失败后部分目录保留，不自动删除重拉。打印仅工具版本、源SHA与固定目录，没有凭据。它不会自动执行产品目录里的任何脚本。

## root逐步审查后再运行的产品准备命令

以下均在新应用机root终端，先确认Docker daemon可用。每个代码块是独立检查点；不运行账号初始化、seed、调度签发或正式压力。绝对截止不延长，剩余时间不足相应上限时不开始新步骤。

```sh
cd /opt/t44-c-0dfb55c
[ "$(git rev-parse HEAD)" = 0dfb55c2191200d947c5423fd9ee74bb0812cc5a ]
timeout --foreground --kill-after=10s 20s docker --context default info --format '{{.ServerVersion}}'
python3.12 deployment/ops.py init-env
python3.12 deployment/ops.py config-check
```

`.env`为0600且排他创建；如果已存在，不重建或输出它。`config-check`只quiet，不打印完整解析配置。下一步下载/构建固定镜像和锁依赖：

```sh
timeout --foreground --kill-after=10s 600s python3.12 deployment/ops.py build
```

build超时/失败就停，并核实daemon中的该构建状态；不能以client退出推定Docker后台已清理。成功后才启动MySQL/RabbitMQ：

```sh
timeout --foreground --kill-after=10s 300s python3.12 deployment/ops.py infra
python3.12 deployment/ops.py migrate --database t44
```

上条迁移只显示计划。root核明确切项目库及实际infra健康、源/冻结版本之后，才单独执行：

```sh
timeout --foreground --kill-after=10s 180s python3.12 deployment/ops.py migrate --database t44 --execute
python3.12 deployment/ops.py status
```

此处停止，保留每步实际退出/版本/耗时，失败不自动重试或清库。账号/口令、seed、scheduler token、API完整启动、跨机私网入口、正式复测均不在本阶段。没有修改产品C/网络开放/凭据/自动释放设置；现有Compose默认web仅loopback、DB/MQ无宿主端口。历史Docker实跑不是本次C云成功证明。

官方主源：2026-10-24核对[Ubuntu维护的docker.io](https://ubuntu.com/server/docs/how-to/containers/docker-for-system-admins/)、[Noble docker-compose-v2（universe）](https://packages.ubuntu.com/eu/noble/docker-compose-v2)。Ubuntu仓库版是Canonical维护的发行包，与[Docker公司官方仓库版](https://docs.docker.com/engine/install/ubuntu/)区分，本阶段不混装两套。包页原通用URL一次抓取timeout，已有官方/eu页面搜索结果明确2.24.6及amd64，另以[Ubuntu docker-buildx](https://packages.ubuntu.com/noble/docker-buildx)提供构建插件；实际安装候选版本须在云机记录；没有把本地语法检查写成安装通过。
