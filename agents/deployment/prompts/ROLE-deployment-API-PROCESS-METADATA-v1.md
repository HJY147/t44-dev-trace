# ROLE-deployment-API-PROCESS-METADATA-v1

本岗为实际派工设立归档ID，不称用户迭代版本。

## 实际派工原文

继续你已收到的 API process metadata 单项问题。主区当前5148733，实际 stage05 两次观测 api-processes OBSERVATION_UNAVAILABLE，不能断言真实原因。仅用既有 tmp/deployment/953... 的 fake /proc 构造 init/tini wrapper argv 同含 uvicorn 命令 + 真正 python -m uvicorn t44.api:app --workers4 +4 spawn 的反例；先设计记录再 red→最小 collector fix→green。若复现则只匹配明确 Python module argv，不能放宽数量容忍。不要 Docker/真实进程/旧故障重测/改产品或资源；保留 b3ee/H11 incomplete历史。现原三正式压力均已封存失败，勿读取私密材料。遵循自有worktree/提交/Issue7实际GET/报告。若假设不成立如实停止该假设，检查其他纯静态可验证原因。

## 对应产物

仅中性metadata API_SCRIPT、既有953中的fake /proc能力守卫及本岗设计/红绿原件/日志/报告/交接；不触native/application.py、产品、资源、真实负载或独立材料。
