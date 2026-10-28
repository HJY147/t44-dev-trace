# 组件 Call 候选 f7：开发 CI 原件核验

准确被测提交为 `f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f`。本轮开发 CI 和托管 Linux Docker 演练通过；固定源码规模实测 **5898 行，超5100上限798行，范围检查真实 exit1**。这两项结论分别保留。

操作者为文档汇总 AI。本岗只下载、校验和解析公开原件，并执行既有静态计量；没有重跑 CI、产品、数据库、HTTP、云或独立验收，没有接触独立测试私件，也不代写学生本人研究报告。

| 官方运行 | 实际终态 | 精确范围 |
| --- | --- | --- |
| [product 40692462131](https://github.com/HJY147/t44-dev-trace/actions/runs/40692462131) | SUCCESS，attempt1 | coverage、frontend、contracts、static四个实际job全成功 |
| [Docker 40692462380](https://github.com/HJY147/t44-dev-trace/actions/runs/40692462380) | SUCCESS，attempt1 | docker-application实际成功；另外三个运输分支跳过 |

两次 run 的官方 `head_sha` 与五个实际 checkout 中 `git log -1 --format=%H` 的真实输出逐一核同完整 f7。没有用旧5d通过结果替代本轮执行，也没有把跳过的运输 job 当成产品验证。REST `total_count` 与连接器完整集合核同：product四制品/四job，Docker一制品/四job。

五份 artifact 原 ZIP 共470871字节，逐件对齐官方大小和 SHA-256；两份官方原 run-log ZIP 共165268字节，仅有本地 SHA，不伪称服务端提供了摘要。七 ZIP 均核 CRC、重复成员、路径越界和符号链接，字节未改。[product原件目录](../../records/ci/40692462131/)和[Docker原件目录](../../records/ci/40692462380/)分别保留绑定；[解析脚本](../../docs/reports/component-ci-f7-analyze.py)可只读复算[机器结果](../../records/ci/40692462131/verified-analysis.json)。

后端原 JUnit 实得796个唯一用例，0 failure/error/skipped；coverage出口无未测生产文件、excluded_lines=0。行覆盖2509/2780=90.25180%，分支721/856=84.22897%，coverage.py混合值88.83388%单列。contract/integration/fault分别183/102/19，唯一并集245均属于796，不追加到总数。782的14项与780的7项已进入本轮完整 coverage 命令；775→796是两次各自原件的统计，不是把局部测试成绩手工加到总数。

前端89个唯一断言全部 passed，0 failed/pending；类型检查和构建成功。原覆盖率为行364/390=93.33%、分支821/932=88.09%；语句和函数另存机器结果，不混同行口径。静态五条命令全 exit0，Bandit errors/results均为空。

Docker原 `result.json` 的 source 为同一f7，passed=true，实际4个API worker。2项目/40任务合成数据只用于演练；调度有实际进展，凭据权限/轮换与备份恢复记录保留。停写后19表的counts和checksums在隔离恢复前后逐字段相等，恢复schema为18表226列、defects为空。第二扫描器被共享flock拒绝的预期exit1原样保留，没有改写为所有步骤均exit0。

本岗在仍处于准确f7的独立worktree执行固定cloc2.10，工具SHA与既有口径相同，计入前端/CSS、CLI、迁移和验收造数实现；不改分类、阈值或统计脚本。应用65文件实测5898行，`--require-range`失败原件见[source-count.json](../../records/ci/40692462131/source-count.json)。cloc物理代码行与coverage可执行语句分母属于不同指标，不能互换。

首批frontend下载的Promise曾拒绝，未保存详细错误对象；没有据此推断原因。只重新下载该缺件并核官方摘要，原始失败事实另存本岗download-attempts记录，没有重跑已通过CI。源码规模、真实云连接预算、独立业务/故障验收、400活跃并发完整600秒性能、连续资源证据、最终账单及学生本人研究报告均未由本报告关闭。
