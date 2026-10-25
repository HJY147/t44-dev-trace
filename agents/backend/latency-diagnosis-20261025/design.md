# 935 / round8 离线延迟诊断范围

作者与执行者：后端 AI。产品准确935ab5b93bea788672c2b4a088c79cfeed848954，独立worktree/branch codex/backend-latency-diagnosis-20261025；主树不改。只读/轻量离线计算，不启动应用/数据库客户端/负载/重测试/云，不派agent、不联系独立operator。

唯一验收事实输入为主树 records/acceptance/814-performance-v8-20261025/performance-result.round8.PUBLIC.json；不跟receipt_path或私有引用。允许部署岗round8公开native-build/interval-interface/metadata；仅沿该interface给出的interval-final.json核声明后读取其完整root中性JSONL。禁止tmp814/817/818/829/private/keys和冻结case源码，禁止app访问日志；不读凭据、活动数据或旧独立mirror。保留独立mirror缺尾77秒的NOT_PROVEN原判，root完整原件仅补充诊断，不能修验收。

离线资源统计按PUBLIC steady窗内的采样端点筛选，不填空/插值/改值：记录每资源样本/空值/状态/首尾/间隔，CPU以interval_seconds加权及nearest-rank描述分位，100%=1核，API含9PID（7worker+parent/tracker），MySQL是共享全进程。不能把API400%说成整机100%，不能把组RSS相加当独占内存，不能把1Hz稳定PID当32ms复位原因证明。reset前后单独列中性样本。

旧Linux/MySQL sequential证据仅作有来源的历史阶段CPU预算，不泛化为935根因；比较api/contracts/runtime/workflow/engine准确Git字节。区分endpoint响应Schema/wire/JSON render、DB锁/连接等待、发压及证据记录开销、连接复位四假设。先给可执行最小隔离顺序和双机复测控制参数；只有纯源码可证明且独立离线microbenchmark足够有意义的补丁才候选实施，否则明确不改产品、先定位。

所有脚本放既有tmp/834_backend_performance，报告/日志/handoff/prompt/commit/Issue3留痕。纯离线输出不是新验收或正式性能通过；原formal0组、400→386/14reset及P95超270保持。
