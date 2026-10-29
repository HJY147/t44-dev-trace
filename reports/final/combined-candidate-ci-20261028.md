# 5d 数据库候选组合：实际开发验证

操作者为总协调 AI。被测完整提交 `5d5e0a15e3b15e2f509c4ae71a927bbc35579be7`；产品相对 a12 只有默认 Table 投影一处和两项显式连接池 ENV 配置入口。原默认 5/10 不变，没有删除安全、审计、幂等、迁移或测试。以下结论不属于独立验收或正式性能通过。

| 运行 | 实际结论 | 范围 |
| --- | --- | --- |
| [product 40682367472](https://github.com/HJY147/t44-dev-trace/actions/runs/40682367472) | 四 job SUCCESS | 后端、真实 MySQL/RabbitMQ 联调、静态、前端 |
| [Docker 40682640278](https://github.com/HJY147/t44-dev-trace/actions/runs/40682640278) | SUCCESS | 真实托管 Linux Compose、4 API worker、调度和备份恢复 |

官方原 ZIP 逐件比对 REST size/digest，并核 CRC、重名、路径和符号链接；另保存两次原 run-log ZIP，它们只有本地 SHA，不伪称服务端提供了 SHA。两个运行的每个实际 checkout 日志都包含上述完整提交。原件和每件绑定在 `records/ci/40682367472/` 与 `records/ci/40682640278/`；逐项解析结果见 [verified-analysis.json](../../records/ci/40682367472/verified-analysis.json)。

后端全套原 JUnit：775 个唯一用例，0 failure/error/skipped。行覆盖 2517/2790=90.21505%，分支 717/852=84.15493%，coverage.py 混合值 88.79736% 另列，excluded_lines=0。contract/integration/fault 为183/102/19，其唯一并集245均属于775，不重复加总。两新增模块已真实接入完整 coverage job；差分测试所需 a12 Git 对象由工作流显式获取，不能以本地完整历史代替浅克隆验证。

前端原结果89项断言全部 passed，未跳过；类型检查、构建和覆盖率出口成功。静态检查成功，Bandit errors/results 均为空。

Docker 原 result.json 的实际 source 为同一5d，passed=true。两项目40任务的合成数据不冒作6000任务压测。演练实际核4 worker、消息/调度、凭据权限和轮换、停写后19表备份及隔离恢复，全部表 counts/checksums 逐字段相等，恢复 schema 18表226列无缺陷。第二个扫描器的共享 flock 拒绝为预期 exit1，保留原件，不能写成所有步骤均 exit0。

固定计量工具在该提交再次运行：**5935 行，超5100上限835行；--require-range 真实 exit1**。非默认池容量、云端新实例总连接预算、独立功能/故障测试、400活跃并发/600秒性能、连续资源证据及本人研究报告仍未由这些 CI 关闭。
