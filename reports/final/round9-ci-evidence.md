# Round9 官方 CI 原件证据

Agent-Role: documentation；实际操作者：AI `/root/ci_evidence_round9`；Prompt-Ref: ROLE-documentation-CI-ROUND9-20261025-v1；Refs: #9。范围是下列两对官方 Actions 原件，非第三轮、独立验收或正式压测。

修正源 `f4bd382d4668130793fc553df9ce6363c4656ea6` 的产品与 Docker 官方 run 均 SUCCESS。后端全套 JUnit 实际 695 tests / 695 PASS / 0 FAIL / 0 ERROR / 0 SKIP；行覆盖率 2478/2760＝89.7826087%。首次 `a16238b9eb3b47473c0332989d6b3dcc1d95d1f4` 的 E731 原始失败与 coverage 取消完整保留。

| 源 SHA | 官方 push run | attempt | run 结论 | job 结论 |
| --- | --- | --- | --- | --- |
| `a16238b9eb3b47473c0332989d6b3dcc1d95d1f4` | [产品40200930857](https://github.com/HJY147/t44-dev-trace/actions/runs/40200930857) | 1 | CANCELLED | static FAILURE；coverage CANCELLED；contracts/frontend SUCCESS |
| 同上 | [Docker40200930957](https://github.com/HJY147/t44-dev-trace/actions/runs/40200930957) | 1 | SUCCESS | docker-application SUCCESS |
| `f4bd382d4668130793fc553df9ce6363c4656ea6` | [产品40201584671](https://github.com/HJY147/t44-dev-trace/actions/runs/40201584671) | 1 | SUCCESS | static/contracts/coverage/frontend SUCCESS |
| 同上 | [Docker40201584699](https://github.com/HJY147/t44-dev-trace/actions/runs/40201584699) | 1 | SUCCESS | docker-application SUCCESS |

四个主 run 均为 `push` / `codex/integration`。已核每个 job 的 run ID、attempt、head SHA，与每个 artifact 的 workflow_run/head/名称后缀一致；原始 run 日志中 10 个 checkout 的实际 `git log -1 --format=%H` 均等于对应源 SHA。封档分支的新文档提交不被当作这些 CI 已测试的应用源。

首次 static job121191761720 的 ZIP 原件 `static-3.log`、`static-console.log` 记录 `tmp/backend/messaging/806_newscope.py:34` 的 E731，`static.json` 记录 Ruff exit1。[阶段1封条](../../records/ci/40200930857/archive-binding.phase1.json) 保留其原时点。coverage job121191761821 CANCELLED，7377bytes artifact 只有六个准备/依赖日志，无 JUnit、coverage JSON/XML；完整后端测试数与覆盖率不可得，不能写0 tests或PASS。contracts的183/102/19子套件和前端89通过不消除该首次失败。

| f4bd 实际测试证据 | tests | PASS | FAIL | ERROR | SKIP |
| --- | ---: | ---: | ---: | ---: | ---: |
| coverage/junit.xml 全套 | 695 | 695 | 0 | 0 | 0 |
| contracts/contract.xml | 183 | 183 | 0 | 0 | 0 |
| contracts/integration.xml | 102 | 102 | 0 | 0 | 0 |
| contracts/fault.xml | 19 | 19 | 0 | 0 | 0 |

上述 XML 的声明计数均与实际 testcase 及 outcome 子节点逐项相符。三子套件按 `(classname,name)` 去重共245身份，全部出现在全套695中；不将183+102+19再累加到695。前端两源均89 tests / 89 passed / 0 failed / 0 pending / 0 todo，summary 与89个 assertionResults 相符。

| f4bd 覆盖率指标 | 分子/分母 | 百分比 | 原件 |
| --- | ---: | ---: | --- |
| 后端行 | 2478/2760 | 89.7826087% | coverage.json/XML/gate.json |
| 后端分支 | 693/836 | 82.8947368% | coverage.json/XML |
| coverage.py 行与分支混合 | 3171/3596 | 88.1813126% | coverage.json 的 percent_covered |
| 前端行 | 364/390 | 93.33% | coverage-summary.json 的 lines |
| 前端语句 | 631/712 | 88.62% | 同上 statements |
| 前端函数 | 206/240 | 85.83% | 同上 functions |
| 前端分支 | 821/932 | 88.09% | 同上 branches |

后端43个报告文件的 executed_lines 总数及 num_statements 总数与2478/2760一致，XML lines-covered/lines-valid一致；80%行门禁成功，无未测生产文件。88.18%包含分支，不能当作line%。这些可执行行分母不能替代应用规模的物理行计数。

两次 Docker 的 `result.json.source_sha` 与各自源一致，scope均为 synthetic hosted-Linux Compose integration；passed=true、4 workers、seed version2/40 tasks、19表恢复 counts/checksums匹配。`shared-flock-rejects-second-scanner` 的 exit1 是既定第二持有者拒绝结果，已保留，不改成exit0；不是独立验收或负载/性能通过。

10个官方 artifact ZIP 共616448bytes，分别与 GitHub artifact 服务端 size_in_bytes 和 sha256 digest 全部一致。4个官方 run 日志 ZIP 共325158bytes，API不提供服务端digest，因此只记录本地SHA256，不宣称服务端digest已比对。共14个ZIP、354成员均CRC通过，无重复成员、绝对/父级/反斜线路径或symlink。两个副PR的静态job原始日志另存、记本地SHA，未纳入10个主要artifact的服务端校验数量。

| 主要封档入口 | 内容 |
| --- | --- |
| [40200930857 binding](../../records/ci/40200930857/archive-binding.json) | 首次产品四artifact、四job、原run日志与每成员SHA/CRC |
| [40200930957 binding](../../records/ci/40200930957/archive-binding.json) | 首次Docker原件及结果 |
| [40201584671 binding](../../records/ci/40201584671/archive-binding.json) | 修正后产品四artifact及695项、覆盖率原件 |
| [40201584699 binding](../../records/ci/40201584699/archive-binding.json) | 修正后Docker原件及结果 |
| [解析结果](../../docs/reports/round9-ci-analysis.json) | 精确计数、覆盖率算术、checkout及副PR区别 |
| [收集器](../../docs/reports/round9-ci-collector.py) / [解析器](../../docs/reports/round9-ci-analyze.py) | 本岗实际执行的归档与分析，不运行SUT |

同head的 pull_request 副run不作为主要准确源验收证据：[40200935848](https://github.com/HJY147/t44-dev-trace/actions/runs/40200935848) metadata head=a162、overall CANCELLED，静态job原日志实际checkout `refs/remotes/pull/21/merge` → `00c1278bec48b21d5a7387da27ca879c7ec3999a`；[40201588604](https://github.com/HJY147/t44-dev-trace/actions/runs/40201588604) metadata head=f4bd、SUCCESS，实际静态checkout同merge ref → `c6b140fcbc8316768009fb53394a11b5cb0ac2eb`。旧run返回的nested pull_requests.head.sha还可显示PR较新的head，不能拿它回推历史checkout；本报告以原checkout日志核对。

先用 GitHub connector 取得官方元数据和检查下载能力；下载仅返回远程文件引用，无本地路径，继而以 `gh api .../artifacts/<id>/zip` 原bytes直接落盘，未用解包文件假定原ZIP正确、未重新压包。run/job/artifact JSON为官方API表示，非HTTP传输原字节。签名下载URL不留存。一次frontend下载EOF留下0bytes，已保留 `.failed-attempt1` 和[失败记录](../../docs/reports/round9-ci-download-failure.json)，再取原端点成功。副PR job日志首次0bytes失败，重试说明CLI拒绝终端转义，使用 `--allow-escape-sequences` 后保存原bytes；[失败回执](../../records/ci/40200935848/static-job-download-failure.json)与空失败件保留。本岗解析门禁JSON时曾将list当dict产生TypeError，修正读取方式后解析通过，未改任何产品或测试。

阶段1 commit `14be82a3` 已先push封E731；后续只补齐本报告和原件。派工“三轮”经总协调更正为两对run，旧40195832268只曾读binding格式、未重下或复用结论。worktree误建根外后依更正以git worktree move原样搬进项目内自身专属目录。

本岗只做Git、官方API下载、ZIP/hash/JSON/XML证据核对，没有运行产品测试、SQL、HTTP、负载、云或浏览器，没有取消/重跑CI、改workflow/应用/测试/计数口径，也没有发GitHub评论。CI/Docker不代表独立验收、正式性能、规模达标或账单完成。总协调提供的当前应用物理5862行，上限5100，超762，规模门禁仍FAIL，本岗未重算。未触学生亲写研究正文、学号/账号/财务签名或原始课堂附件，未读取任何独立PRIVATE/冷包/用例/keys或其他岗私件。

封档检查：作者文档/脚本的diff-check、JSON、10个本地链接和责任路径检查通过。全量diff-check exit2，仅两份副PR原始job日志19行保留上游行尾空白；原bytes未改写，例外已记validation。完整原件阶段commit为 `fccf5c82`。
