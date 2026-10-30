# 本地准备交接

本轮仅离线准备。用户自行启动原应用机0mt（64核）与压力机0mu（16核）。开机后提供两个**当前公网IP**，由本地SSH更新工具生成新的配置；保留原主机指纹校验。地址变更不等于授权有效；若2小时临时公钥已过期，仍需在云助手恢复原公钥一次。

准备入口使用包内run/manual12-resume-prepare.py；其参数和真实步骤见CONTINUATION_RUNBOOK.md。保留未实际发压的r30manualp12；新材料r30materialresume05、新维护r30restoretransition05。所有远程输出必须全新。若任一新路径已存在则停下保留证据，不能删除或原地重跑。

恢复仅通过原业务接口对原800个任务中属于开发者的400个流转任务检查，并解除合法state3/from2的阻塞；原state2任务跳过。先检查完整批次、三角色项目范围、归属、空依赖、计划时间、版本、冻结升级规则及原升级事件稳定时间窗，并核原业务计数与服务账号有效性，保留实际审计。原消费者和调度器在恢复期间按原入口优雅停止，避免并发修改；失败或UNKNOWN不能自动重试或继续发压。

既有索引在上轮已应用；本次只读核实际布局与原迁移证据，不重做DDL。新材料仍使用原90b产品镜像，需独立岗核索引补充证据和新材料。包内QA PUBLIC接口和原ENTRY哈希保持不变；协调者不能替独立岗生成实际许可。

开机后仍需完成：严格SSH主机与授权验证、原7容器/资源及排他核验、实际任务恢复、新四会话、TLS和五件材料、独立零请求prepare与一次许可。planned_end必须满足原资格时间门禁；不满足将明确报阻塞，不通过延长时间或降低断言放行。本地通过不能代替这些现场检查，也不能证明云P95达标。

证据在进程退出且全部writer停止后密封回收并核SHA/字节，再通知用户可节省停机。分析在本地进行。

SSH地址更新命令（此处仅模板，当前不执行）：

```sh
python3 -B ssh/update_ssh_addresses.py \
  --known-hosts /Users/yang/Desktop/nothing/软件开发大作业/.submission-private/cloud-access/FINAL-20261030/manual-pins/known_hosts \
  --identity /Users/yang/Desktop/nothing/软件开发大作业/.submission-private/cloud-access/FINAL-20261030/id_ed25519 \
  --app-ip APP_CURRENT_IPV4 --load-ip LOAD_CURRENT_IPV4 \
  --output-dir NEW_ABSOLUTE_LOCAL_DIRECTORY
```

输入本次开机后的实际地址。配置保留HostKeyAlias、StrictHostKeyChecking=yes、禁转发并禁旧连接复用；不读取私钥、不联网、不延长临时授权。详见ssh/README.md。

本次现场恢复、材料生成均可能因时间流逝而安全拒绝。预检时间窗与原工具最终packet时间窗分别检查，预检通过不保证后验仍有效。任何阻塞将保存精确原件后停止，不自动放宽条件、改计划时间、改升级事件或继任重试。
