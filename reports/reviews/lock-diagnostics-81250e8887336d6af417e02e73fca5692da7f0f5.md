# Fresh MySQL 锁诊断工作流窄审：准入一次执行

## 1. 对象

固定AI审核岗，精确工作流HEAD`81250e8887336d6af417e02e73fca5692da7f0f5`；根协调独立worktree`lock-diagnostics-20261025`实际HEAD相同且干净。范围为workflow、825 admission/setup、固定request、设计、两个已选工具的源绑定与执行边界。不运行数据库、SUT或既有8项guard；不读829或其他独立材料。不是独立验收或生产合并审。

## 2. 设计与实际身份

三个matrix job各获独立鲜建固定digest MySQL8.4 service：baseline/candidate各用自己service的`t44_diagnostics`，HTTP用独立`t44_gate_http`；不是三个job共享现存库。baseline明确从ade5恢复Runtime，候选/HTTP对应c8c；checkout仍报告真实工作流HEAD，admission另报application_reference，不能把工作流SHA或原Runtime内容hash充作基线应用提交。

## 3. 源检查

5个入口实际字节同HEAD。每mode的76项显式应用清单与各自参考逐字同；baseline恢复只在本岗内存比较，没有改任何工作树。额外核完整backend、frontend、database、specs/contracts、specs/database、CI依赖锁及HTTP依赖986文件，当前HEAD相对c8c无差量。ROOTS是显式清单，不宣称每个仓库文件都属于该清单。两个工具实际/提交hash同：DB `bf9bbedd1dd09196c99ca986a3072a3a506b5b9ffda38f48fc1e5dcd11af37a4`，HTTP `f77f2872fe6dfb8230fec6edb24be5fdcbfe048bf83c4ed319e1a6c7e713caff`。本阶段不改变生产Runtime；该C的源码窄审另有报告。

## 4. 环境与权限

825准入在依赖安装/迁移之前，绑定CI=true、精确仓库/ref、checkout=GITHUB_SHA、固定本地DSN/user/port/schema、文件清单/工具hash和固定request。setup复用精确环境检查；只用一次性root迁移命名鲜建库，再撤销镜像为t44创建的schema ALL，授schema SELECT/INSERT/UPDATE/DELETE，以及仅P_S data_locks/data_lock_waits/threads三表SELECT。库名来自固定mode allowlist，不接受任意拼接输入。没有PROCESS、全局grant、13306、本机旧env、云账号或生产库路径。实际root登录、migrate与P_S readiness没有执行，失败应作为环境阶段原样记录，不叫竞争失败。

## 5. 时间、并行与原件

fail-fast=false保留baseline失败时candidate/HTTP继续取得各自证据。DB有120秒内部alarm与150秒GNU timeout，HTTP外限180秒，强杀宽限5秒；job10分钟。HTTP诊断连接会话innodb_lock_wait_timeout=5是测试局部设置，不改生产pool或隔离级别。显式bash步骤使用runner的失败/pipefail执行规则，tee不应把被测退出值冒绿。admission及两个case输出排他写，日志目录由准入先创建；always保存服务日志与artifact，异常/超时仍留原件。没有正式性能负载、Rabbit链或资源开通。

## 6. 固定nonce澄清与实际验证

首次读到root提议“只改nonce正常后继触发”时，已指出admission把nonce01纳入精确dict比较，改02会必拒。root随后明确这是全新branch/workflow/request路径首次push，只推精确审阅HEAD、request任何字节不变，撤回nonce-only后继计划；因此当前固定01契约无源缺陷。不能把这次澄清写成代码已修过或当前接受任意nonce。任何源修订须给新SHA再审。

本岗只执行只读字节/Git/AST/JSON核验；baseline恢复仅在内存模拟。root报告8无网guard绿，本岗没有读取其原件或重跑，不把它们记成本岗执行。真实SQL、HTTP、权限或并发次数均0。机械原件为`agents/reviewer/evidence/shared-project-point-c8c/workflow-81250e8-audit.json`。

## 7. 十项检查

| 项 | 判定 | 依据 |
|---|---|---|
| 1 HEAD与身份 | 通过 | 精确812及5入口实际bytes核对 |
| 2 范围 | 通过 | 有限开发锁验证，非正式性能 |
| 3 输入 | 通过限定范围 | mode、固定request/nonce01、工具SHA |
| 4 库隔离 | 静态通过 | 三job/service；精确两个本地库名，无13306 |
| 5 产品语义 | 本报告不重复判定 | 精确c8c源码另审；基线只恢复原Runtime |
| 6 权限 | 静态通过，实际待证 | disposable root setup；app CRUD+三表SELECT，无PROCESS |
| 7 时间及竞争 | 静态通过，实际待证 | 独立服务/限时/fail-fast=false；未跑真实锁 |
| 8 故障原件 | 静态通过 | 外限、排他输出、always服务日志/artifact |
| 9 执行真实性 | 通过限定范围 | 0本岗DB/HTTP/CI；8guard仅root报告 |
| 10 执行准入 | 通过限定范围 | 精确812固定request首次push一次；无合并/全局放行 |

## 8. 结论

精确`81250e8887336d6af417e02e73fca5692da7f0f5`可首次push执行一次本有限fresh MySQL开发工作流，request01保持不变。已先给root技术结论，再办报告/Issue。未见当前源和权限编排的实质执行阻断；环境、权限readiness、完整锁和HTTP结果仍须真实CI归档后判断。失败不能改成通过或挪用旧绿证据；新HEAD、工具、环境、grant或request变化重新核受影响范围。没有APPROVE、main/global成功状态、正式性能/规模/产品通过或合并许可。

封档前的后续事实（root转述，本岗未独立读日志/artifact）：首次run `40171891410`三job已迁移成功，但全在setup REVOKE处以MySQL1141停止，锁/HTTP/业务case执行0。这是准备脚本对已有grant形式的错误假设暴露，不是候选锁竞争失败；执行前静态准入不等于这次实际执行成功。没有观察SHOW GRANTS，不推断确切厂商grant转义内容。旧source/nonce01/红run保留，不覆盖为绿；修正新源6738的单独复审见同目录新报告。
