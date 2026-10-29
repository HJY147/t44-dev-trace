# 中性验收控制 stdout 分流修订（实现前）

作者：协调 AI。范围仅 deployment/acceptance/control.py 的环境适配，不修改产品 bc5a、独立案例、冻结规格或预期。

## 原因与证据边界

独立岗已明确发表 stage02-driver-binding.md/json：五个 H2 环境均在 init-user 控制返回 exit0、stdout70字节但非JSON处停止，未进入业务或正式稳态。开发侧只读这两份发表文件，没有读取原始密文/用例。源码静态核实：产品 init-user 成功输出单个 {user_id: 整数} JSON；Controls.compose 将 Docker stderr 合入 stdout，污染机器读取通道。

## 输入、输出和失败

保留同一白名单命令、stdin口令、同一项目/超时/恢复/权限。compose 捕获 stdout 和 stderr 两路；两路仅写现有私有环境日志，返回的 stdout 不包含 Docker 进度 stderr。CalledProcessError 与 TimeoutExpired 均保留真实退出码和两路输出，非零仍失败。

init-user 成功返回且仅返回一个 JSON 对象，唯一字段 user_id，类型须实际 int（拒绝 bool），范围1..4294967295。不从混合文本提取最后一行，不忽略歧义、不将非零解释为成功。

scheduler-scope 仍返回真实 credential-admin JSON；其字段为 session_id、expires_at、credential_written、rotated、previous_session_revoked、previous_session_already_inactive。broker queues/connections 仍为 RabbitMQ 原生文本；fault 成功无stdout；recover、audit-sql、service-credential 保持各自已公开格式。README 逐命令明确，不能假设全部控制均JSON。

## 验证与后续

使用已有 tmp/deployment/953_acceptance_environment.py 增加合成边界回归，覆盖进度分流、真实失败和超时、ID类型/范围及stdout歧义。先保存原实现红，再修复绿。此验证是部署工具自测，不是独立业务通过。正式托管实际能力仍待独立岗使用同一冻结业务入口验证；先前失败永久保留。
