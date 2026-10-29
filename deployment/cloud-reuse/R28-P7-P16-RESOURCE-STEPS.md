# 本轮P7/P16资源与新代际：仅命令计划

本岗未执行以下云命令。已知P7运行事实来自root回执，不是本岗云探测；源a12e9e70b963bacafda3242bb6d82e53ee912ff1、07:30Z绝对停止（北京时间15:30）不变。原两机继续复用，不买新机、不删旧卷。

完整27项argv、host、helper SHA、最小余窗及未填写字段在 `agents/deployment/resume-20261028/p7-p16-command-plan.PUBLIC.json`。文件名含PUBLIC不代表命令已执行。`ROOT_ACTUAL_*`必须取当前步骤真实回执；私网IP按root当次节点核验填写，nonce私有handoff绝不打印或入Git。

## 先核时间与工具

每次**新建/启动**前计算当前UTC至07:30Z的秒数，打印给root观察；剩余不足本步就停留现状收尾，不改旧窗口。下列只读代码可作为每个新建/启动任务的前缀，`MIN_SECONDS`替换为表中值，随后才运行该一步：

```sh
python3 - MIN_SECONDS <<'PYCLOCK'
import sys,time,datetime
remaining=datetime.datetime.fromisoformat('2026-10-28T07:30:00+00:00').timestamp()-time.time()
print({'remaining_seconds':remaining,'minimum_seconds':int(sys.argv[1])})
if remaining<int(sys.argv[1]): raise SystemExit('INSUFFICIENT_FROZEN_WINDOW')
PYCLOCK
```

同一shell任务需`set -eu`保证前缀失败后不继续。**status/seal/stop收尾不设未来余窗门禁**，过期后仍按原owned身份收尾，不能因超时阻止停机。

| 动作 | 至07:30Z至少剩余 | 原工具的真实约束 |
| --- | ---: | --- |
| P7/P16 collector prepare | 240秒 | sample=07:28:30须至少未来120秒，serve=07:29:30，比sample多60秒且在hardstop内 |
| collector/mirror start与mirror prepare | 120秒 | serve必须未来>30秒；本计划额外留余量 |
| 新P16 generation prepare | 1200秒（计划） | 原工具实际至少600秒；计划额外留infra/seed/对照预算 |
| P16 arm | 120秒（计划） | 原工具至少60秒；后续SUT启动仍需600秒 |
| config/infra/migrate/idle/scheduler相关非停止动作 | 600秒 | 07:20Z后原controller拒绝，不能延长或绕开 |
| status/seal/owned stop | 无未来限制 | 精确binding、controller、PID/image/unit身份校验仍必须满足 |

派生工具目录 `/root/t44-r9/resume-20261028-01/resume-profile`。generation.py27199B/SHA `fd7d8ccef1968a424618ed7493f7a6c0b5a676b85cd22189c3e13f248b9d87c8`；resource-stream.py44079B/SHA `3d9f096f8d51d2c46994089c437650fb6e710887739abe1d9a1fc81b3bdb44cd`。root先核实际原字节，不用新repo app-campaign.py覆盖旧daaf factory。

## P7先采集，LOAD从offset0跟上

APP（余窗≥240秒；IP由root填写）：

```sh
python3 /root/t44-r9/resume-20261028-01/resume-profile/resource-stream.py prepare-app \
  --phase-dir /root/t44-r9/campaign-r28p7-01/p \
  --phase-binding-sha256 eac4f526cc742b8c71393cf3af819092e59abd5deeefdc375d1a5e51fc0cfcf6 \
  --app-ip ROOT_APP_PRIVATE_IP --load-ip ROOT_LOAD_PRIVATE_IP \
  --port 18446 --run-id r28p7metrics01 --output /root/t44-r9/resource-r28p7-01 \
  --sample-until 2026-10-28T07:28:30Z --serve-until 2026-10-28T07:29:30Z \
  --interval 1 --byte-cap 268435456
```

记下其真实bindingSHA；APP start（余窗≥120秒）：

```sh
python3 /root/t44-r9/resource-r28p7-01/controller.py start \
  --directory /root/t44-r9/resource-r28p7-01 --binding-sha256 ROOT_ACTUAL_P7_RESOURCE_APP_BINDING_SHA
```

root用已批准私有受限运输将`private-mirror-handoff.json`原字节交LOAD新0600路径并核公布SHA，不在UI/聊天显示nonce。LOAD装相同SHA的resource helper，再prepare与start（各≥120秒）：

```sh
python3 /root/t44-r9/resume-20261028-01/resume-profile/resource-stream.py prepare-mirror \
  --handoff /root/t44-r9/inbound/r28p7-resource-handoff.private.json \
  --handoff-sha256 ROOT_ACTUAL_P7_RESOURCE_HANDOFF_SHA \
  --run-id r28p7mirror01 --output /root/t44-r9/resource-mirror-r28p7-01
python3 /root/t44-r9/resource-mirror-r28p7-01/controller.py start \
  --directory /root/t44-r9/resource-mirror-r28p7-01 --binding-sha256 ROOT_ACTUAL_P7_RESOURCE_MIRROR_BINDING_SHA
```

在warmup前双方status，核APP已有真实numeric row且LOAD已从offset0持续取得前缀。不能在测试结束后补一次snapshot并称全时段采样。当前只有6-role，scheduler缺失必须missing/null；CPU第一样无delta也是null，不能补0。RSS进程求和与cgroup memory/cache分别解释，CPU单核100%可>100%，不能直接当host百分比。

本轮短窗后APP `seal`→LOAD status实际确认`mirror-final.json`的完整tail/transport_complete/wholeSHA/bytes→LOAD stop→APP resource stop→P7 controller owned stop，所有动作按PUBLIC计划对应精确argv；先停APP exporter会丢LOAD收尾窗口。若mirror未收全明确partial，不伪填成功。最后P7 stop：

```sh
python3 /root/t44-r9/campaign-r28p7-01/p/controller.py stop \
  --phase-dir /root/t44-r9/campaign-r28p7-01/p \
  --binding-sha256 eac4f526cc742b8c71393cf3af819092e59abd5deeefdc375d1a5e51fc0cfcf6
```

## 新P16使用独立命名空间

不并发运行双臂：旧P7封存且owned stop后才执行P16 infra。两代limits合计可能超过32GiB，limits不是预留容量。prepare只生成环境/证书并核实际源，不启动P16，原空F也不启动。root先核四个新端口真实未占（原工具也会拒绝占用）；这些仅是建议，不代表本岗已探测端口。

APP新P16 prepare（计划余窗≥1200秒）：

```sh
python3 /root/t44-r9/resume-20261028-01/resume-profile/generation.py prepare \
  --factory /root/t44-r9/campaign-935/p/controller.py \
  --upgrade-binding /root/t44-r9/resume-20261028-01/build-01/upgrade-binding.json \
  --upgrade-binding-sha256 31fc1c8a9cd2162656c8cfc9a42e830e228494d1e644f143921bbb718834cbd8 \
  --source-package /root/t44-r9/resume-20261028-01/source-checked-01 \
  --source-manifest-sha256 68f9db715b4a9d33d1cc70c5f7d08a50fcd51c97dfd4276dceba71e93d9ade00 \
  --original-proof /root/t44-r9/proof-v2-01/proof.jsonl --image-proof /root/t44-r9/image-proof.py \
  --output /root/t44-r9/campaign-r28p16-01 --run-id r28p16gen01 --app-ip ROOT_APP_PRIVATE_IP \
  --f-tls-port 20443 --f-http-port 18280 --p-tls-port 20445 --p-http-port 18281 \
  --p-workers 16 --stop-utc 2026-10-28T07:30:00Z
```

取真实**p**回执的bindingSHA，不取f。依次P16 controller arm→config→infra→migrate；每次都给`--phase-dir /root/t44-r9/campaign-r28p16-01/p --binding-sha256 ROOT_ACTUAL_P16_BINDING_SHA`，migrate另加`--database t44c_r28p16gen01_p`。每步余窗见上表，失败保留原件，不重seed或覆盖输出。

migrate后使用后端岗已审**完整v2七脚本包**的790_bootstrap，仅对空新P16按seed44/anchor2026-10-28T04:00Z生成40/6000/9000/15000；P7不可重跑bootstrap。对照两臂seed_manifest/selection SHA和实际原入口16workers，再controller idle；仍不启动scheduler。具体790阶段和LOAD参数由后端岗runbook/真实回执负责，本页不改其前提或读取私包。

P16采集同上：phase换campaign-r28p16-01/p及真实P16 binding；collector port18448/runid r28p16metrics01/output resource-r28p16-01；LOAD mirror runid r28p16mirror01/output resource-mirror-r28p16-01。准确argv已列PUBLIC计划。先collector+mirror，再同一客户端矩阵；P7结果不能替代P16，未实际7vs16结果前不宣称根因或达标。

## 正式7-role/600秒：未执行方案

待root根据真实7vs16结果决定。需新namespace和独立中性准入，真实五类角色/自然TTL过期/可撤销会话；原CLI按40个真实项目scope签发scheduler token，启动并证真实首轮scan，collector/mirror覆盖warmup、600秒steady及后置条件。当前790要求fresh提醒创建，scanner会改变其事件/版本前提；不能删断言把6-role诊断改名正式7-role测试。

只余600秒不足以准备＋warmup＋完整steady＋收尾。07:20Z后controller已拒新的idle/轮换/启动；若现窗口不足就封存原数据并保留原实例，向root说明缺口，不延长旧freeze或直接套旧成绩。CPU/RSS/缺样/错误、独立判定及全部进程owned stop都应真实记录，不能预填。
