# P13正式复测 / 新材料07离线准备

当前仅离线包。用户保留原两机停止，准备冻结/审核完成再由协调者通知用户开机。无云/SSH/SUT操作；不安排额外AB。产品source90b、原七镜像和已应用schema不变，存储唯一候选PL1 40GiB3800IOPS来自用户控制台报告；上轮guest确认MySQL卷→nvme0n1p3→唯一40G nvme0n1(259:0)，guest未读取PL等级。

## 历史06与新07边界

原maintenance06成功恢复156个，400全state2、原800守恒；material06真实新材料生成/进程退出成功，但APP-ready未产生，编排被用户中断。原目录continuation06-NEW、全部会话/凭据/rotation/scan原件保持；不得改06输出、旧grant、旧时间或重发UNKNOWN。材料07/维护07是新的用户请求，绝非06自动重试。正式QA p13没有触发，但现场必须检查原W下p13 runs/results/operator等新输出均不存在，任一消费迹象即停止并保留。

新wrapper强绑定r30materialresume07/r30restoretransition07，并要求本轮已回收STOPPED06公开前缀精确SHA=e485eabd7cc3c436e60545dba885c0e235e0bed3d69c7dd5eb5d4617255a6f7f。前缀是历史，不证明当前状态。包内provenance/STOPPED06-PREFIX.PUBLIC.json为已回收原件精确字节；只置受限runtime和原主机，不提交公开Git（含内网拓扑，不含明文账号token私钥或PRIVATE stdout）；不改它、不公开其内网地址。

## 开机后一次准备入口

工具包全新安装至/root/t44-p13-material07-kit（由协调者最终包校验器核SHA），不覆盖旧kit。当前APP/LOAD真实公钥余量≥3600s、严格原hostkey；真实recipient/CA有效且绑定LOAD既有受保护私钥，只公开证书不得传私钥。不要启动旧controller。

```sh
python3 -B /root/t44-p13-material07-kit/run/manual13-resume07-prepare.py \
 --backend-tools /root/t44-p13-material07-kit/backend \
 --deployment-tools /root/t44-p13-material07-kit/deployment \
 --helper-dir /root/t44-p13-material07-kit/maintenance \
 --previous-prefix /root/t44-p13-material07-kit/provenance/STOPPED06-PREFIX.PUBLIC.json \
 --packet /root/t44-final-20261029/P09/P-packet/output/packet/inputs/session.private.json \
 --accounts /root/t44-final-20261029/P09/P-accounts/output/accounts.initialized.private.json \
 --ca /root/t44-final-20261029/P09/P-packet/output/packet/inputs/ca.pem \
 --load-cert ACTUAL_PUBLIC_RECIPIENT_CERT \
 --load-cert-sha256 ACTUAL64HEX \
 --maintenance-id r30restoretransition07 --material-id r30materialresume07 \
 --output /root/t44-final-20261029/manual-material/continuation07-NEW \
 --authorize-existing-task-restoration --authorize-owned-worker-stop \
 --ack-exclusive-no-benchmark-or-other-writer --openssl openssl
```

工具先查原工具/7容器/当前schema/800IDs/五表counts/active service，再停止原consumer/scheduler并稳定读回。若当前400确为state2且blocked_from_state全空，只记只读跳过恢复回执，不发维护HTTP；全当前scope/owner/role/version/time/window/fixture仍由原材料资格校验，不以06成功豁免。若当前确需合法恢复则由原helper全批门禁后原UNBLOCK，部分/未知保留不重试。后端契约da484fd8支持，未改runtime。

原链实际新发四会话、原CLI service凭据、DB读回、轮换精确scheduler目录绑定token、恢复原workers，再等待原持久扫描成功。必须是rotation后新started且新finished、status2、errorNone、scanned>0；旧scan92恢复进度/heartbeat不能替代。唯一部署变化：准备观察等待150→900秒，有界只读观察，不新增scanner或造业务事件，不改正式测量/原断言。此工具字节SHA已更新，wrapper必须匹配新pin。

当前编排自开始共享单调1800秒准备总预算，所有子流程/导入工具subprocess.run/直接wait受剩余时间约束；内部900秒扫描预算不能重启或延长总预算。超时只停止本次子流程并保留prefix，**绝不关闭实例，不设置自动停机任务**。原已有owned stop timer只按精确退休机制处理，禁止创建替代定时任务。

## 必要耗时与仍未知项

实测上轮维护1642请求约86.94秒，本轮当前400已就绪时可省；材料606请求/退出证明约34.07秒是历史测量，不保证新现场相同。旧完整scan历史约55.2/180.6/302秒，另有旧scan剩余与最多60秒调度等待，因此新scan现场可能仍需数分钟；900是准备等待上界，不是性能合格保证。真实SSH/安装、当前状态差异、QA当前身份审阅/零SUT prepare/一次grant耗时未知；不得向用户承诺开机即发压。

APP-ready须生成当前五件CMS密文+公开receipt，精确当前source/bundle/import/schema supplement/资源/排他/session/TLS事实交全新隔离QA；外部writer不存在不能由容器列表单独证明。没有当前身份、prepare和grant不能发压。触发前复核四会话有效期/输入/目标/排他，原400并发/60秒预热/600秒稳态/P95≤270ms/每分钟≥1000吞吐/零业务错误和全部断言不动。

正式测试退出后按原密封工具备份，下载cipher+receipt核SHA/字节，立即告诉用户由其手动节省停机；本地解密分析不需要让服务器等待。没有任何新增强制关机/guest shutdown/自动云stop动作。
