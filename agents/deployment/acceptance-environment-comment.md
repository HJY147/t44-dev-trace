Agent-Role: deployment
Prompt-Ref: ROLE-deployment-INDEPENDENT-LINUX-HARNESS-v1

新增可review的中性托管Linux环境（deployment/acceptance、acceptance-environment.yml），为下一轮隔离tester提供真实MySQL/Rabbit/API4worker/consumer/scanner/前端、只读SQL审计和受限服务故障/恢复；只初建synthetic空项目/manager，不含独立用例或预期缺陷，不修改产品门禁/统计口径。

请求使用精确40位产品SHA及tester自己冻结harness SHA/入口/接收证书，分开checkout。凭据仅runner私有/mask；stdout/stderr及固定白名单输出以OpenSSL CMS AES256-GCM/RSA-OAEP加密，公开artifact只有密文和环境/控制/退出元数据。tester自持私钥、14天内取回审查脱敏后主动发布；root/dev不读未发布明文。没有把普通artifact当tester专用私有ACL。

已核实GitHub官方：dispatch要求workflow在default branch。本仓库main无该workflow，故新增严格codex/deployment-acceptance-environment或codex/independent-harness-*分支、仅deployment/acceptance/request.json变动的push入口，不绕main保护。

953部署guard25项/Ruff/actionlint实际通过；新环境一次能力自检尚待精确请求push，独立harness尚未冻结/选择/执行。本轮不接触独立私有资料或联系tester，不声称已覆盖独立fault/性能，不租云或买资源。中性运行/取回约定见deployment/acceptance/README.md。
