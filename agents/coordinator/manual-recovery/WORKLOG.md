# ROOT manual recovery worklog

2026-10-30：接收用户已停机确认，不再查询云端停止状态。仅检查本机路由和SSH配置，未联系云服务器。准备当次用户执行的临时公钥授权脚本、严格hostkey pin配置工具；保留旧authorized_keys，不修改SG/firewall/password/sshd配置。执行9项mock、本地bash-n/Python AST；独立审核限定PASS，补记认证到期与已有会话边界。未声明远程SSH/SCP或正式压测完成。Prompt ROOT-MANUAL-RECOVERY-20261030，用户新指令关闭TUN后默认直连。
