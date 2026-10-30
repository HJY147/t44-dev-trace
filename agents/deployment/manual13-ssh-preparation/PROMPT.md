# ROLE-deployment-MANUAL13-SSH-v1

原始用户请求：继续修改、修改完成后我再开启服务器，ssh应该需要修改连接

实际派工：部署岗在独立worktree离线检查原SSH两工具，补当前公网IPv4更新并保留原信任锚与禁转发，不连接/开机/扩权；复用既有continuation恢复链，不重复改prepare；记录本地测试和未现场验证边界。

改进理由：把“换IP”与“临时授权过期”分开处理。已有原实例pins可直接用于严格新地址连接；报告的旧到期时间不应迫使每次改IP重新装公钥，也不能被更新地址工具误记为已恢复授权。

实际操作者：AI deployment岗；不是用户亲自改代码。产物为deployment/cloud-reuse/ssh-reconnect/*，测试在本目录。没有独立验收或性能结论。
