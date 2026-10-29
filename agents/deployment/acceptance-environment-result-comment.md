Agent-Role: deployment
Prompt-Ref: ROLE-deployment-INDEPENDENT-LINUX-HARNESS-v1

中性环境能力必要复核真实成功：[run39961035953](https://github.com/HJY147/t44-dev-trace/actions/runs/39961035953)。环境脚本源 `68b3bb2c532db8b14ddc57e0a219657ec026cad0` 与产品源 `4c20f32b71635016815420472b9d4bb4fa850df0` 分开记录。harness_ref=null/harness_started=false/profile=false，没有独立用例或验收结论。

真实固定镜像build/完整服务/迁移/空synthetic项目及账号已起。先观测MySQL2003、TCP111、Docker ports={}、仅本project Internal网络，才在验收override增client bridge；产品Compose不改。随后只读SQL/AMQP连通、真实CLI限定service bearer(session元数据、显式项目、escalation:write、TTL300、0600)、Rabbit stop→recover、恢复后客户端与finally恢复通过。初始观测失败仍保留，没有称所有步骤首次通过。

CMS AES256-GCM/RSA-OAEP合成输出加密/解密roundtrip实际验证，公开artifact只有环境/控制元数据和密文，不含.env/Token/上下文/私钥/coverage/独立案例。未来由tester自持私钥、冻结接收证书，14天内取回密文审查脱敏再主动发布。只读SQL不能冒充可用bearer；实际service-credential控制入口已经提供，Token不入公开ledger或原始命令日志。

协议：deployment/acceptance/README.md；workflow acceptance-environment.yml提供严格branch/request.json push入口，dispatch仍需正常default branch准入，不改main保护。953本岗37guard/Ruff/actionlint通过。首败39958418657、原始公共execution/回执/gzip+SHA分别归档在agents/deployment/acceptance-environment-validation/run-*。不联系/读取独立私有资料，不重复本轮check；独立harness/真实证书/独立fault覆盖和正式性能仍待隔离流程。
