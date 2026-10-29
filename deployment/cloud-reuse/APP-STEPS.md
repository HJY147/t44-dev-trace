# App baseline935：逐段新环境，先诊断不冒验收

root已从真实双机proof summary确认7镜像OCI descriptor→原archive config/layer全链。原v1 helper/CI manifest/ZIP不改，不重load或改daemon。image-bundle-v2.py只是已导入集合的强验证/新overlay，并不再次import。app-campaign.py在任何新环境写入前fresh核原V1完整文件和13guard的proof全7实链；source来自实际manifest935，不能随意填未来产品SHA。

三个新脚本需按SHA在root/t44-r9中O_EXCL上传（不覆盖旧0a1/47b50）：image-bundle-v2.py可单独接受已载入集合，app-campaign.py为31415bytes/SHAdaaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea；实际代码见同目录。root通过已有官方命令工具准备后：

```sh
python3 /root/t44-r9/image-bundle-v2.py \
  --bundle /root/t44-r9/bundle-935 \
  --manifest-sha256 3c599b31922d55822cb845abc768ea8c2db668d469d6d6bf330378bcb1ac7ec4 \
  --v1-helper /root/t44-r9/image-bundle.py --image-proof /root/t44-r9/image-proof.py \
  --output /root/t44-r9/transport-acceptance-935-NEWNONCE
```

新app配置双phase（APP_PRIVATE_IP由root私有节点资料填，不放公开报告）：

```sh
python3 /root/t44-r9/app-campaign.py prepare \
  --bundle /root/t44-r9/bundle-935 --bundle-helper /root/t44-r9/image-bundle.py \
  --image-proof /root/t44-r9/image-proof.py \
  --manifest-sha256 3c599b31922d55822cb845abc768ea8c2db668d469d6d6bf330378bcb1ac7ec4 \
  --output /root/t44-r9/campaign-935 --run-id r9diag935 --app-ip APP_PRIVATE_IP \
  --p-workers 7 --stop-utc 2026-10-25T21:00:00Z
```

此步仅新private配置/F与P独立root/app数据库凭据、新schema/vhost/CA和Compose；不seed human/project，不启动服务。F t44c_r9diag935_f/P t44c_r9diag935_p，MYSQL_USER另_app且仅新容器内目标；P TLS18445/F18443只私网映射，web18081/18080只loopback，DB/MQ/API无host端口。CA私钥不挂载/不传load，server.key仅nginxUID101可读。每个phase独立MySQL/Rabbit卷，不能同时发负载；P正式前停F所有owned容器保卷。

以下以P短诊断为例，**每条独立云助手检查点**，不是粘为一键运行：

```sh
python3 /root/t44-r9/campaign-935/p/controller.py arm --phase-dir /root/t44-r9/campaign-935/p
```

arm新建独立systemd timer/service并enable，OnCalendar21:00UTC+Persistent，ExecStart固定controller和bindingSHA，reboot后过期也会触发。没有active timer，后续config/infra/migrate/idle不会执行。

```sh
python3 /root/t44-r9/campaign-935/p/controller.py config --phase-dir /root/t44-r9/campaign-935/p
```

只quiet config，不能在stdout打印展开的Compose/Env。

```sh
python3 /root/t44-r9/campaign-935/p/controller.py infra --phase-dir /root/t44-r9/campaign-935/p
```

只启动已proven image aliases的MySQL/Rabbit，neverpull/no-build，最长300s。

```sh
python3 /root/t44-r9/campaign-935/p/controller.py migrate --phase-dir /root/t44-r9/campaign-935/p --database t44c_r9diag935_p
```

只调用原Python3.12产品镜像backend migrate CLI（host3.10只包装Docker）。目标库必须完全相同；不连127.0.0.1:13306，不接旧schema。初始官方MySQL entrypoint应用用户为该独立schema的DDL/CRUD权限，正式CRUD权限收窄/测试RO账号由root数据库阶段显式处理，不冒称本工具已创建最小CRUD账户。

```sh
python3 /root/t44-r9/campaign-935/p/controller.py idle --phase-dir /root/t44-r9/campaign-935/p
```

只启动API/consumer/web/TLS，scheduler仍pending，健康不等于业务验收。root可随后在明确数据环境调用原admin CLI/实际fixture，不由部署猜ID/人类口令。取得实际projectID才运行：

```sh
python3 /root/t44-r9/campaign-935/p/controller.py scheduler-token --phase-dir /root/t44-r9/campaign-935/p --project-id ACTUAL_ID
python3 /root/t44-r9/campaign-935/p/controller.py scheduler-start --phase-dir /root/t44-r9/campaign-935/p
```

上述仍逐条，token原CLI签发/3600s/专属目录10001/0700，scheduler只读挂载与共享锁，未实现通配或自动续签。

```sh
python3 /root/t44-r9/campaign-935/p/controller.py status --phase-dir /root/t44-r9/campaign-935/p
python3 /root/t44-r9/campaign-935/p/controller.py stop --phase-dir /root/t44-r9/campaign-935/p
```

stop只按精确project+service+两种同内容cryptoproven image/configID限定容器，30秒grace后Docker可能kill，实际Running/ExitCode/OOM保留，**不由ExitCode宣称forced=false**；不down-v/prune/DDL/drop/关VM/释放。hardstop只依赖冻结binding/controller，root后续env变化不能让timer失效；新业务操作仍拒未审核配置变更。原服务数据/证据留同机。异常完整stdout/stderr只在phase/receipts/stage-failure-UUID.json0600，stdout只报路径；prepare失败留partial新目录不自动reset。

资源候选：P7或16，MySQLmax384（oneengine5+10假设下含2ops upper165/300，需实际观测）；P bufferpool8GiB/MySQLmem12GiB/API10GiB/MQ2GiB/consumer与scheduler各1GiB/web与TLS各256MiB，共26.5GiB cap，按实际MemTotal30.19GiB为OS留约3.69GiB，非同时实际使用保证。F4/API2GiB/MySQL2GiB与512MiBbuffer、max128。不同worker/硬件收益不能写为软件优化，16档必须新profile/generation/实际argv记录，不回写7档记录或在未结束phase中换参数。

后续backend快照升级是另一明确接口：root提供fullsourceSHA/实际全backend/t44 archive bytes/hash及全文件清单，验证依赖锁和规格未变，从已proven935base构建新tag；镜像内真正rm-rf旧/app/backend/t44后COPY新集合，重写source/revision/archive labels，启动容器只读导出全文件集合hash拒残留commands.py。保持旧archive/image/grants；不重下513MB、不给935绿套新source，不在本阶段搬候选。
