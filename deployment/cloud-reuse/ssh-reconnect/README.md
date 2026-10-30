# 原两机开机后的SSH地址更新

此目录只准备本地连接文件，不连接、开机、安装凭据或执行准备/压测。开机后原两台公网IP可能改变，主机身份继续固定为原实例尾号0mt/0mu的既有ED25519 key；仅有新IP不能证明机器身份。旧临时公钥是否过期须实际认证才能判断，改IP不延长授权。

## 已有原始信任锚时仅更新地址

由协调者收到用户本次确认的当前APP与LOAD公网IPv4后执行，`APP_CURRENT_IPV4`、`LOAD_CURRENT_IPV4`必须替换为本次实际值，不能复用历史IP。`NEW_WINDOW_PINS`替换为尚不存在的绝对目录，其父目录必须存在。原known_hosts与identity使用原授权目录，脚本仅stat identity，不读取其字节。

```sh
python3 -B update_ssh_addresses.py \
  --known-hosts /Users/yang/Desktop/nothing/软件开发大作业/.submission-private/cloud-access/FINAL-20261030/manual-pins/known_hosts \
  --identity /Users/yang/Desktop/nothing/软件开发大作业/.submission-private/cloud-access/FINAL-20261030/id_ed25519 \
  --app-ip APP_CURRENT_IPV4 \
  --load-ip LOAD_CURRENT_IPV4 \
  --output-dir NEW_WINDOW_PINS
```

输出两份`<完整实例ID>.sshconfig`、原两件信任锚的`known_hosts`及`reconnect.PUBLIC.json`。必须使用该新目录的`-F`配置，别再使用旧地址配置。可先纯本地`ssh -G -F CONFIG ALIAS`确认解析，无连接。实际用户开机后由协调者使用：

```sh
ssh -F NEW_WINDOW_PINS/i-bp13uag4r4u9r2hge0mt.sshconfig t44-manual-app 'id -u'
ssh -F NEW_WINDOW_PINS/i-bp13uag4r4u9r2hge0mu.sshconfig t44-manual-load 'id -u'
```

上面两条是真实连接，仅未来开机后执行。SCP同样传`-F`和原alias。严格hostkey失败即停，不删除known_hosts、不用accept-new/no、不改到另一台新机器；必须经云助手等原实例中性事实核实。超时不等于已停机。只变公网IP时不需再次安装公钥。

## 临时授权过期

若准确原主机匹配后返回publickey拒绝，再用保留的`01_INSTALL_TEMP_SSH.USER_ONLY.sh`在**原两机**云助手执行。此脚本原字节复制，继续同一公钥、2小时、restrict及禁止转发，不更改密码/防火墙/安全组；到期格式为OpenSSH8.9接受的本地`YYYYMMDDHHMMSS`，无尾Z。此交付没有执行脚本或申请新权限。

保留的`pin_ssh_host.py`可根据云助手真实PUBLIC回执生成配置，但回执授权必须仍有效。应复用包含原pins的可信目录检查host key；不要拿空新目录当作允许更换原主机指纹的手段。优先继续用上面的地址更新器和原锚；实际连接仍须匹配原key。

## 与新恢复包的衔接

SSH连接确认后，后续只传新修订包，不覆盖原`/root/t44-manual12-kit`。应用机恢复入口由协调者打包现有continuation的`run/manual12-resume-prepare.py`及其已冻结的backend/deployment/maintenance源；material为`r30materialresume05`、新独占输出。该链停止原owned writer、恢复原800 ID中的合法阻塞任务、读回，再调用一次原prepare完整链。SSH工具不调用这条链、不签发QA grant。原正式QA run仍`r30manualp12`；正式入口、断言和准入保持原样。

本次8项离线测试覆盖原锚守恒/不读key、真实OpenSSH仅解析、旧目录不覆盖、非法地址、缺/重复pin、非法key wire、权限/符号链接、原恢复脚本语法与时间格式。只证明本地连接配置准备，不证明现场SSH、任务恢复或性能通过。
