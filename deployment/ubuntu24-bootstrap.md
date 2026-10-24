# Ubuntu24.04应用机分步准备（待root审查/执行）

准确产品C固定`0dfb55c2191200d947c5423fd9ee74bb0812cc5a`；今天北京时间2026-10-24 17:00（UTC09:00）自动释放/20元预算不变。本次权限修订脚本仅本地验证，尚未在云机执行；原8f版已由root执行，历史及真实失败/修复见下文。仅面向新t44-app，不在发压机安装应用栈，不使用阿里云key/token。

当前实际通路为用户已授权的云助手root执行，不要求Workbench SSH连接成功。将审查后的`ubuntu24-bootstrap.sh`作为文件上传/粘贴保存，核对本岗交付SHA后逐阶段调用，**不要将下载内容直接管道给shell，也不要把下面阶段串为一键执行**：

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

该阶段以匿名公开HTTPS、禁交互凭据，fresh init/fetch单一完整SHA并detached检出（等效最小精确克隆），Git下载上限360秒，低速窗口30秒；验证HEAD及tracked字节未改。目标`/opt/t44-c-0dfb55c`已存在时不覆盖或reset，复核后同样规范公开tracked模式。保留umask077；source新增60秒内嵌Python，只按Git index stage0的100644/100755 regular文件设0644/0755、它们的父目录0755、源码根0750，确保Docker COPY后的非root读取。整体预检无symlink/hardlink且所有对象归本root所有，以O_NOFOLLOW文件描述符fchmod，不walk .git/.env/其他untracked。已存在.env仅lstat检查regular/root-owned0600并核前后元数据不变，不读取秘密、不自动修私有权限。规范后再次核HEAD/tracked clean；失败可能留下部分公开模式修改，先观察，不自动回滚或重试。失败后部分目录保留，不自动删除重拉。打印仅工具版本、源SHA与固定目录，没有凭据。它不会自动执行产品目录里的任何脚本。

## root逐步审查后再运行的产品准备命令

以下由root经云助手在新应用机root环境逐段执行，先确认Docker daemon可用。各云助手任务不共享上一任务工作目录，因此每个产品块都重新cd并校验准确HEAD。每个代码块是独立检查点；不运行账号初始化、seed、调度签发或正式压力。绝对截止不延长，剩余时间不足相应上限时不开始新步骤。

```sh
cd /opt/t44-c-0dfb55c
[ "$(git rev-parse HEAD)" = 0dfb55c2191200d947c5423fd9ee74bb0812cc5a ]
timeout --foreground --kill-after=10s 20s docker --context default info --format '{{.ServerVersion}}'
python3.12 deployment/ops.py init-env
python3.12 deployment/ops.py config-check
```

`.env`为0600且排他创建；如果已存在，不重建或输出它。`config-check`只quiet，不打印完整解析配置。下一步下载/构建固定镜像和锁依赖：

```sh
cd /opt/t44-c-0dfb55c
[ "$(git rev-parse HEAD)" = 0dfb55c2191200d947c5423fd9ee74bb0812cc5a ]
timeout --foreground --kill-after=10s 600s python3.12 deployment/ops.py build
```

build超时/失败就停，并核实daemon中的该构建状态；不能以client退出推定Docker后台已清理。成功后才启动MySQL/RabbitMQ：

```sh
cd /opt/t44-c-0dfb55c
[ "$(git rev-parse HEAD)" = 0dfb55c2191200d947c5423fd9ee74bb0812cc5a ]
timeout --foreground --kill-after=10s 300s python3.12 deployment/ops.py infra
python3.12 deployment/ops.py migrate --database t44
```

上条迁移只显示计划。root核明确切项目库及实际infra健康、源/冻结版本之后，才单独执行：

```sh
cd /opt/t44-c-0dfb55c
[ "$(git rev-parse HEAD)" = 0dfb55c2191200d947c5423fd9ee74bb0812cc5a ]
timeout --foreground --kill-after=10s 180s python3.12 deployment/ops.py migrate --database t44 --execute
python3.12 deployment/ops.py status
```

此处停止，保留每步实际退出/版本/耗时，失败不自动重试或清库。账号/口令、seed、scheduler token、API完整启动、跨机私网入口、正式复测均不在本阶段。没有修改产品C/网络开放/凭据/自动释放设置；现有Compose默认web仅loopback、DB/MQ无宿主端口。历史Docker实跑不是本次C云成功证明。

官方主源：2026-10-24核对[Ubuntu维护的docker.io](https://ubuntu.com/server/docs/how-to/containers/docker-for-system-admins/)、[Noble docker-compose-v2（universe）](https://packages.ubuntu.com/eu/noble/docker-compose-v2)。Ubuntu仓库版是Canonical维护的发行包，与[Docker公司官方仓库版](https://docs.docker.com/engine/install/ubuntu/)区分，本阶段不混装两套。包页原通用URL一次抓取timeout，已有官方/eu页面搜索结果明确2.24.6及amd64，另以[Ubuntu docker-buildx](https://packages.ubuntu.com/noble/docker-buildx)提供构建插件；实际安装候选版本须在云机记录；没有把本地语法检查写成安装通过。

## 当前执行通路与进展：root UI转述

Workbench服务角色获用户明确批准后，root已点击创建确认；root和ecs-user的临时SSH连接均失败。云助手列表显示两机正常，版本2.2.4.1097；本岗未操作或独立查看云端。

root已通过云助手仅对应用机执行公开主机准备工具`tmp/853_cloud_environment_preflight.sh`：UI核完整命令一致，北京14:21:49开始，耗时小于1秒，实际exit0。root转述结果为root账号、Ubuntu24.04/x86_64、Python3.12.3、git/curl具备，Docker缺失；所查账号列表未出现ecs-user。这是环境预检，不是产品部署或性能验证。

8f479201已由审核岗作只读限定审查，无实质阻断。root在已审脚本中仅加入阶段参数`set -- packages`，完整替换云助手编辑器后全文核对一致，提交`t44-bootstrap-packages-8f47920`；任务上限900秒并约束进程树，正在安装，尚无完成/成功结论。编辑器曾在fill后保留默认`#!/bin/bash`前缀，该次因比对不一致被阻止执行；root改全选粘贴并确认一致后才提交，不能把前一次当已运行。

本仓库已审`ubuntu24-bootstrap.sh`原字节及Git blob保持不变；这里只改通路说明和分块工作目录，不改脚本。脚本直接从文件调用时仍按三阶段参数使用；云助手整段执行时，由root显式选择唯一阶段并核全文，不自动运行后续source/build/infra/migrate。安装结果由root实得回执另行追加，本岗不访问云/CI/服务或私有测试资料。

## 安装/源码/配置已完成，构建待核：root后续UI转述

记录于2026-10-24T06:40:12.811798+00:00；本岗没有访问云端、原UI、日志或私密配置，以下仅据root实际回执转述，保留上节“当时安装中”的历史。

| 检查点 | root看到的实际回执 | 范围 |
| --- | --- | --- |
| packages | 北京14:26:31，23秒，exit0 | Ubuntu5个新包、0升级、0移除；Docker29.1.3/Buildx0.30.1/Compose2.40.3+ds1/Python3.12.3/git2.43.0 |
| source | 北京14:31:42，29秒，exit0 | 同脚本仅set--source，UI全文一致；准确C `0dfb55c2191200d947c5423fd9ee74bb0812cc5a`，HEAD/tracked核对，目录/opt/t44-c-0dfb55c |
| 配置 | 北京14:36:06，小于1秒，exit0 | Docker daemon29.1.3；init-env生成0600配置不输出秘密；config-check标记T44_CONFIG_CHECK_OK |
| build | 新任务已提交，尚无完成回执 | t44-build-C-0dfb55c：HEAD核C/config-check/ops build timeout600s；外层云助手720s并约束进程树 |

只有前三项已有完成回执；构建exit/success仍null。尚无infra、迁移、seed、应用启动、私网连通或正式性能通过；不能以安装/config通过代替它们。17:00自动释放与实际花费20元预算不变，未授权延时/提高预算。已审bootstrap脚本及产品C均未改。本岗公开转述投影见agents/deployment/ubuntu-bootstrap-validation/cloud-preparation-checkpoints.json，没有复制云日志或配置。

## 公开源码权限故障与修补：root实际云回执转述

原bootstrap全局umask077保护了秘密，却让Git公开tracked目录0700/文件0600；Docker COPY保留权限且归root，UID10001/101无法读取Python包/配置。本岗AI实现及此前AI限定审核漏查了这一运行边界，云端由root AI诊断修复，不记作学生发现。原8f源与失败仍在Git/云日志历史，不把原语法检查当运行可读性证明。

- 迁移北京15:53:55，<1秒，exit1，`/usr/local/bin/python: No module named t44.cli`。旧backend2c59d266…/webebbc444…据root保留pre-mode-repair标签（仅有前缀，不补全imageID）。
- root仅按Git tracked100644→644/100755→755及其目录755、根750修公开权限，未遍历.git/.env；3919文件/312目录、tracked diff clean、.env600。此为root实际修复转述，不是本岗重新在云端执行。
- API重建15:59:23，110秒/exit0，image `2f651f9d76189f500d3d8b7336077c12639d711ac88fc0773b1f88309db9116e`。web两个nginx配置旧root600、UID101 UNREADABLE；16:02:34重建82秒/exit0，image `3255b48594e1763b703ccd5a74b205e9d203c6a1cd89ce6b069e3019327b68bd`，实际非root配置可读。C cli hash da883…核验据root通过，仅记录给定前缀。
- 修复后迁移16:03:00，4秒/exit0。镜像构建/可读性/迁移回执不等于完整API/HTTPS/私网/正式性能通过；下载渠道变体也不能写成原Dockerfile逐字构建。原601秒timeout等历史不变，20元/北京17:00不延长。

后续bootstrap工具修补只预防新的精确C源码准备再次出现此问题，未在上述已手工修复云目录重跑。846本地临时Git clone实际复现umask077：旧逻辑cli.py600断言红；修后7项必要guard绿，覆盖公开模式/exec、private.env/.git/untracked不变、错HEAD/dirty/私有env错模式/hardlink/unsupported symlink拒绝。shell与内嵌Python分别语法/CI配置Ruff/compile通过，无安装/镜像/云/服务/CI或独立资料动作。原red/green与root转述投影见agents/deployment/bootstrap-mode-validation。
