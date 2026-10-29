# 原双机本轮收尾

部署AI仅准备工具，不能以工具安装/本地检查替代实际收尾或云停费。根实观测QA结束后再传 `--root-qa-finished`；工具不读独立QA资料、不查询其unit/case、不与QA通信。原短诊断relay/13件工具/产品代码不改，不开新服务。

两侧运行 `install-close-window.PUBLIC.sh` 排他安装 `/root/t44-r9/close-window-r29-01.py`。新源7921字节（≤8KB），安装器4776字节。固定实际成本截止04:56:19.801Z；子命令最多各自cap且留45秒给provider操作，LOAD追尾最多20秒且停前留90秒。截止不能成为继续租赁充值的理由。

1. APP：`python3 -I -B /root/t44-r9/close-window-r29-01.py app-seal --root-qa-finished`。原collector seal只发送原USR1，核完整sealed.json和实际raw bytes/SHA，输出完整字段（包括0/null/false）。不要在QA仍采样时提前seal。
2. LOAD可先只读：`python3 -I -B /root/t44-r9/close-window-r29-01.py load-status`。从本机原resource-ready.PUBLIC.json取完整mirror绑定SHA，核原文件，不猜9d3699之后的数字。status按原action/unit/PID/progress形状完整保存，不假定success字段。
3. LOAD：`python3 -I -B /root/t44-r9/close-window-r29-01.py load-stop --root-qa-finished --app-raw-bytes ACTUAL_APP_SEALED_RAW_BYTES --app-raw-sha256 ACTUAL_APP_SEALED_RAW_SHA`。明确对照原mirror-final.transport_complete、实际mirror raw bytes/SHA和APP公开封尾值；追尾不完整时先打印missing，随后原stop保留prefix，再核实际final/prefix完整值。若APP封尾值根本没拿到，省略两个参数会明确missing而仍有限停，不伪称完整。
4. APP：`python3 -I -B /root/t44-r9/close-window-r29-01.py app-stop --root-qa-finished`。从原APP prep complete取完整66372开头绑定，核原GEN SHA；原GEN stop保卷，再原collector stop，最后只查询本轮APP compose project的docker ps，完整保存仍running列表。不会停/查独立QA容器。

每个动作一次，日志与PUBLIC receipt在 `/root/t44-r9/r29-closure-APP-01` 或LOAD；receipt stdout包含完整内容及其文件SHA，原stdout/exit另存。超时保留stdout/stderr和明确returncode:null、timed_out:true。错误不覆盖prefix，不自动重试，不创建新压力会话。

Guest里 `cloud_billing_stopped` 固定null，不声称云停费。最后仍由根通过provider经济停机原双机、保留原盘并核自动释放时间“-”，同时核停止状态和费用。若客体收尾不完整也先明确missing、保留前缀，由根按预算及时provider停机。

部署本地只做Python3.10语法/shell语法和3项文件检查：0/null/false保留、空prefix bytes0及完整空SHA、缺失明确null；没有执行真实resource seal/stop、GENstop、Docker、云或QA。实际结果必须由根原件补记。
