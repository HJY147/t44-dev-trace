# 仅补这两处resource ready-race缺失回执

root转交APP resource-r28p16-02原start拒绝`EXACT_OWNED_SYSTEMD_PROCESS_REQUIRED`，原e5 controller/binding不改。此helper不start/restart/stop服务，只核原失败及真实owned身份后独占补`start-result.json`，明确`late=true`、`not_original_start_success=true`；原拒绝与全部原件保留。

root先审 `deployment/cloud-reuse/resource-operator-completion.py` 和metadata。APP可一次执行 `agents/deployment/resume-20261028/operator-completion-install-and-app.sh` 原文：新路径安装后调用限定APP补录。完整命令已实算raw/encoded+描述小于13000/18000；若helper已安装用operator-completion-app.sh，不覆盖重装。安装和补录都不是原start通过。

APP固定目录、binding f76269ff54bd74bc762e98a2d1a41273b659f50c48eeaa7888bbcd7318988e97、原failure-23c53697a08f4e84aedef94c3bc953e0.json。只允许另外一个未来LOAD目录 `/root/t44-r9/resource-mirror-r28p16-02`；LOAD同helper可先独占安装，再在原start出现**同一精确reason**后用其实际回执：

```sh
python3 /root/t44-r9/resource-operator-completion-20261028.py \
  --directory /root/t44-r9/resource-mirror-r28p16-02 \
  --binding-sha256 ROOT_ACTUAL_MIRROR_BINDING_SHA \
  --failure /root/t44-r9/resource-mirror-r28p16-02/failure-ROOT_ACTUAL_32HEX.json
```

消费方仅在原start返回该目录内原failure、且确为此ValueError ready-race时调用；其他错误、已有start-result、目录不符一律停止，不做通用catch或重启。helper本身还会重新检查原文件，不能只依赖消费方传来的字符串。

保护包括：精确e5 controller、绑定固定文件集合SHA、原plan/严格argv、unit路径和完整原模板/原SHA；真实systemd MainPID/active/running/cgroup，proc目录owner与Uid四值0、starttick、argv、cgroupv2归属和成员。最多5秒只等argv匹配，任何PID/starttick/cgroup切换立即拒绝；两次稳定观察再重核所有输入后O_EXCL/NOFOLLOW/0600/fsync。

补录后调用**原**controller status（另限10秒）并再次核PID/starttick/cgroup/argv；失败返回失败并保留已写late回执，不能冒原start成功或删除重试。内核重启与写文件不能完全原子化，末次原status及再探测是额外门禁；只信active或单次argv不够。

5组本地守卫通过：APP/LOAD正例真实文件独占补录/不覆盖；其他错误、外部目录、unit变化拒绝；PID切换/5秒argv拒绝；真实fixture文件的UID/cgroup/member校验；原status失败保留late/原拒绝。systemd/proc观察明确模拟，不是云执行结论。首轮4个夹具失败因项目Unicode路径不被原unit生成器接受，改为仅替换动态fixture目录，不改冻结代码，原XML逐字gzip保留。
