# P13 storage-only direct formal retest

仅存储候选改变：用户报告原APP盘ESSD PL1 40GiB3800IOPS，尚未独立现场读回。source90b、七镜像及已应用索引不变。不采用pool reset/redo修改，不新增AB。原400/60/600及全部阈值/断言不变。当前manifest精确SHA覆盖新wrapper与冻结原工具；仅离线检查，不代表真实准入。

## 现场前提

用户开启原0mt/0mu并提供当前公网IP后，用ssh目录工具生成新本地配置，实际认证且原hostkey相符才连接。工具包须解压到两机全新/root/t44-p13-storage-ready-kit，并以verify_bundle.py核全部源SHA。旧kit和历史输出不覆盖。动态recipient证书放包外；原LOAD独立收件私钥继续受保护，不能进入公共包。

原qa run r30manualp13只可在未prepare/execute/消费/输出的前提继续；存在任何相关输出即停止。本次material为r30materialresume06，maintenance为r30restoretransition06。以下输出父目录须存在、最终目录须全新；证书路径与SHA必须用现场实际值。

## APP准备入口（未来执行一次）

```sh
python3 -B /root/t44-p13-storage-ready-kit/run/manual13-resume-prepare.py \
  --backend-tools /root/t44-p13-storage-ready-kit/backend \
  --deployment-tools /root/t44-p13-storage-ready-kit/deployment \
  --helper-dir /root/t44-p13-storage-ready-kit/maintenance \
  --packet /root/t44-final-20261029/P09/P-packet/output/packet/inputs/session.private.json \
  --accounts /root/t44-final-20261029/P09/P-accounts/output/accounts.initialized.private.json \
  --ca /root/t44-final-20261029/P09/P-packet/output/packet/inputs/ca.pem \
  --load-cert /root/NEW-PUBLIC-RECIPIENT.pem \
  --load-cert-sha256 ACTUAL64HEX \
  --maintenance-id r30restoretransition06 \
  --material-id r30materialresume06 \
  --output /root/t44-final-20261029/manual-material/continuation06-NEW \
  --authorize-existing-task-restoration \
  --authorize-owned-worker-stop \
  --ack-exclusive-no-benchmark-or-other-writer \
  --openssl openssl
```

## 实际顺序

1. 核所有工具SHA、原五件绑定、原800 ID、三账户、当前CA与recipient至少1800秒；不读取独立测试PRIVATE。
2. 严格核原七容器的ID/镜像/角色/资源。备份原旧unit，只停用准确旧timer。仅优雅停止原consumer/scheduler，其他五角色按原规则start/wait；不得recreate/build/pull/seed/DDL。
3. 只读核已应用索引完整布局、原800 ID及五项业务总量与旧packet一致；核原service账号active且namespace匹配。这些失败时不调用维护HTTP。
4. 维护helper真实登录三个人类角色，检查原40项目scope/my_roles、开发者成员有效、全400 task归属/状态/版本/原空依赖及计划时间。核原400升级事件、冻结规则和now至+900秒稳定时间窗。全批通过才开始解除合法state3/from2；原state2跳过。仅用原业务UNBLOCK接口，持久化请求/审计元数据，400读回、800及计数守恒。凭据只在RAM，PUBLIC/PRIVATE维护日志均不落登录token/password。
5. 恢复完整成功再调用一次原prepare完整链：四真实会话、原CLI service token及持久读回、材料、scheduler token轮换、启动原worker、新持久scan与CMS。新材料资格在最终时刻再次严格验证。全批预检不保证时间流逝后的最终资格仍有效。
6. 核原七容器全部running及已有healthcheck，保存原件。成功只为PREPARATION_COMPLETE_NOT_FORMAL_ADMISSION，不是正式压测授权。

## 失败与后续

任何失败、超时或中断均保留前缀；可能已提交但响应未知归UNKNOWN，不自动重发、清理或继任。维护UNKNOWN只能用helper inspect+previous只读调查，再由协调者决定下一步；不得直接重跑整个入口。失败时不会自动启动先前停止的writer。

恢复成功后，由独立岗核新schema supplement、资源排他、四会话、TLS/原五件与实际身份，按qa/READY_INTERFACE.PUBLIC.md零请求prepare并签本轮一次性许可。协调者不得自签实际grant。原400客户端、60秒预热、600秒稳态、P95≤270ms、吞吐≥1000/min、0业务错误及原工具断言不变。

正式进程退出且全部writer停止后，按原PUBLIC密封接口回收cipher/receipt，核SHA与字节，再告知用户可节省停机。现场完整恢复、SSH、云端TLS/MySQL和性能本轮均未执行。

## 本地验证

后端14项离线、16项真实source90b FastAPI/冻结schema/SQLite联接，以及24个规则边界组合的1项对照通过；部署18项离线通过；SSH8项离线通过，含真实ssh -G纯解析。上述组分别记录，不合并冒称云验收。最终代码审核另绑定精确SHA，原缺陷记录保留。

## 启动前最小只读存储映射

原mysql容器ID由包内deployment/P09-existing-containers.PUBLIC.json中role=mysql读取并核对，不能只按名称猜测。先执行docker --context default inspect --format '{{json .Mounts}}' EXACT_MYSQL_ID，只保留Destination=/var/lib/mysql条目；如Type=volume，对其Name做docker --context default volume inspect --format '{{.Mountpoint}}' EXACT_VOLUME_NAME。对得到的实际绝对挂载源执行findmnt -T ACTUAL_MOUNT_SOURCE -o SOURCE,TARGET,FSTYPE,MAJ:MIN --json，再执行lsblk --json -o NAME,KNAME,TYPE,MAJ:MIN,SIZE,PKNAME。限制留存相关设备/父盘，不能把259:0直接解释为某个云盘ID。通过控制台当前应用机唯一附盘ID/容量/PL1与设备链核对，缺失映射如实报告。以上无SQL/业务请求/写入，也不证明PL1升级有效或性能达标。

SSH余量本地入口：python3 -B deployment/manual13-retest/check_ssh_window.py --known-hosts ORIGINAL_KNOWN_HOSTS --app-report CURRENT_APP_PUBLIC_REPORT --load-report CURRENT_LOAD_PUBLIC_REPORT。此入口依赖同包deployment/ssh-reconnect下两原文件，原2h授权不延长。当前两实例IP/公钥有效期须现场取得。普通本地检查无法证明真实SSH登录。

r30manualp12已消费，绝不可重启。P13输出存在即保留并阻塞，不自动删除或重试。正式执行必须使用新中性事实与独立p13身份、原零SUT prepare和一次grant，不能使用本部署包制造批准。
