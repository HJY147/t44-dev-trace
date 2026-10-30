# P13 SSH原信任锚

本目录三份程序原字节来自上一已核验SSH包，SHA在总manifest中。不含私钥/真实账号，不连接或启动主机。

使用update_ssh_addresses.py的--help查看纯本地参数，以当前公网IP和原known_hosts/identity创建全新配置；IP更新不延长原2h临时公钥授权。pin_ssh_host.py供真实云助手公开回执校验原主机指纹；禁止忽略或替换原hostkey。01_INSTALL_TEMP_SSH.USER_ONLY.sh仅由用户在原实例云助手按原流程执行，不能在本机运行，也不代表程序已安装凭据。

运行ssh -G仅解析配置，实际SSH认证仍须开机后验证。长准备前按RUNBOOK.md执行check_ssh_window.py，至少3600秒授权余量；不足时先处理授权，避免服务器等待。

新的APP入口为run/manual13-resume-prepare.py；material=r30materialresume06，maintenance=r30restoretransition06，正式run=r30manualp13。全部旧p12/05输出只保留历史，不再执行或覆盖。正式准入及唯一一次grant另由独立岗基于当前事实审核。
