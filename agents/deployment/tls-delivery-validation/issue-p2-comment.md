补正上一条 TLS delivery checkpoint（原记录保留）：审核发现 P2，OpenSSL3 的 x509 -checkip 在 IP SAN 不匹配时也可能返回0，原实现仅 check=True 不足以拒绝错误IP；旧19项本地guard中以stdlib替代该命令没有覆盖真实退出语义。

已推送修复 6af63a94889692f38f1ad27e240b692328f461fe：deployment/tls-delivery.py 新SHA256 cc6594d0ed18870245df82099f9790e1a425ea8e275e22b9a3b597cef6fd1cd9。只将第一验证命令改为 openssl verify -CAfile ca.crt -verify_ip ip -purpose sslserver server.crt，移除单独x509 -checkip，expiry/keypair/manifest检查保持。请以新实现重新审核，旧版未云执行，无回滚动作。

4项针对性合成guard通过：正确verify_ip/purpose命令、验证非零向外传播、key不匹配拒绝、过期拒绝；CI配置Ruff/compile/stageddiffcheck通过。已实际尝试本机正确和错误SAN命令，但LibreSSL3.3.6均不支持-verify_ip而exit1，因此两项真实SAN语义结果为null，目标Ubuntu OpenSSL3实际正/错SAN仍待核，绝不记为通过。原checkpoint/检查/失败保持，证据 agents/deployment/tls-delivery-validation/p2-verify-ip-fix.json。完整C构建仍无成功结论，无云/CI/服务/性能动作，20元/17:00不变。
