# 同两实例复用：root逐段执行

本岗不控制UI/云账户；以下脚本准备完成不表示云执行成功。原节点仅角色代称，ID/IP存在忽略的0600 nodes.json。每条脚本目前均小于32KiB，实际云助手编辑器仍核全文/字节SHA，不把“已复制”当执行。

## 只读和Ubuntu官方包

官方云助手对正确app或load实例粘贴对应完整脚本前加：

```sh
export T44_NODE_ROLE=app
# 此处接01-probe.sh原全文；load改为load。建议任务timeout120s。
```

若已通过官方文件上传，等价精确命令：

```sh
bash /ABSOLUTE/01-probe.sh app
```

确认probe后单独包安装。root已实核两机延期06:00后，可用新的operation deadline05:30BJT（UTC21:30，仍需脚本当时15min..12h内）；未延期时不能用这个时间。

```sh
export T44_NODE_ROLE=app
export T44_OPERATION_DEADLINE_UTC=2026-10-25T21:30:00Z
# 此处接02-ubuntu-packages.sh原全文，load改为load。云助手任务timeout至少1500s且约束进程树。
```

上传版等价：

```sh
bash /ABSOLUTE/02-ubuntu-packages.sh app 2026-10-25T21:30:00Z
```

每次仅一阶段，APT失败/timeout保留真实输出后观察dpkg/daemon，不自动repair/重试/卸载。留原安全组件，未改SSH/云助手/ufw/安全组/账户权限。Docker daemon启动不等于产品启动。

## 官方CI离线镜像（可先935开发baseline，未来V2另明确SHA）

新workflow初次可能尚不在default branch；从已有docker-integration.yml workflow的manual桥接调用同ref的新reusable job，不需要把未审产品改到main才能打包。root本机精确命令：

```sh
gh workflow run docker-integration.yml --repo HJY147/t44-dev-trace \
  --ref codex/deployment-continuation-20261025 \
  -f bundle_source_sha=935ab5b93bea788672c2b4a088c79cfeed848954
gh run list --repo HJY147/t44-dev-trace --workflow docker-integration.yml --limit 3
```

填写bundle_source_sha时只跑cloud-bundle，不跑原integration。未来新V2产品完整SHA需新dispatch、新archive和imageID，不能给935镜像重贴V2标签。私有.env/数据/token/DSN都不进入CI；构建context为显式公开子集。固定5官方base digest（Python/Node/Nginx/MySQL/Rabbit）及app/web；只从官方registry拉，再save/gzip到官方GitHubartifact，不加第三方镜像/下载凭据。仅本地guard不是镜像构建绿，真实run结果另核。

成功artifact名cloud-images-<fullproductsha>-<runid>，三个文件：bundle-manifest.json、images.tar.gz、source-runtime-context.tar.gz。先从真实成功job输出记manifest_sha256，再官方artifact下载并核SHA；使用官方云助手/Workbench上传两机的新private目录（不可覆盖旧包），受限门户单文件大小由root实看，不杜撰限制或换未知跳板。失败artifact只保存该job实际命令退出/stdout/stderr，不把partial当成功bundle。

上传前/后verify，root把真实manifest SHA替换占位（不能直接信任同一不明下载包里附的校验值）：

```sh
python3 /ABSOLUTE/image-bundle.py verify --bundle /ABSOLUTE/NEW_BUNDLE \
  --manifest-sha256 ROOT_VERIFIED_64_HEX_SHA
python3 /ABSOLUTE/image-bundle.py load --bundle /ABSOLUTE/NEW_BUNDLE \
  --manifest-sha256 ROOT_VERIFIED_64_HEX_SHA
```

load需要Linuxamd64、12GiB空闲、上传文件当前owner/单link/regular；先验已有alias不同ID则拒覆盖。load后实核configID/平台/source及archive labels，输出images-overlay.json只含镜像映射/neverpull，不启动服务或删卷。RepoDigests可能不随save/load保留：CI实核上游固定摘要，传输/加载实核configID，两个含义不混淆。app实际Compose后续需显式组合此overlay与新TLS/worker配置，用--no-build --pull never，不能误触云端pull/build。

此Python脚本兼容Ubuntu22 Python3.10，只依赖标准库；冻结Linux工具如需Python3.12，后续用bundle里官方Python3.12 alias容器运行它们，不改冻结工具、不装PPA。

## 下一阶段

新run private plan、严格CA/IP TLS、六业务服务+第七TLS、参数/连接预算、持久owned停止timer继续分阶段交付，未有明确plan/真实source/配置/截止不能直接启动产品。服务器stop保卷/缓存以便同实例复用，不停机/释放/重买；根负责成本与已实核06:00释放计划及提前收证，不把停止容器当停止计费。
