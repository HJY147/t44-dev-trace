# 935 round8：先隔离公共延迟，再决定优化和容量

作者与离线执行者：后端 AI。准确产品935ab5b93bea788672c2b4a088c79cfeed848954；本岗仅新诊断脚本/报告，产品和主树零改动，未启动任何应用/数据库客户端/负载/重测试/云，没有新agent或operator联络。本阶段不是再次验收。

## 快速结论

公开事实仍为400启动、386持续末、14次ConnectionResetError集中10:51:31.748048–.780287UTC，核心窗600秒，P95 contract3212/transition3499/escalation3468ms，完整formal组0。吞吐13367.4/min只满足该数值门槛；不补终态、不改原P95或零错结果。

root完整中性资源原件补充显示：API组平均约4核，发压进程约0.78核、共享MySQL约0.74核，不能说整机8核已满，不能凭秒级PID稳定解释32ms集中复位。优先定位**公共等待**：框架/线程与连接池排队、DB锁导致连接占满、客户端/证据记录或传输。四操作同量级P95不是这些原因的证明，却使仅优化某一小函数不足以解释整体秒级差距。

最先可做的现有证据观测是逐请求配对 Server-Timing 与冻结latency的匿名quantiles；随后通用strictTLS快响应canary隔离HTTP+证据writer，再用source935新开发schema的stage harness拆服务内阶段。所需接口已列harness-interface.json，尚未实现或运行；root负责机器/新库和明确执行准入。

## 输入与资源方法

只读认证PUBLIC副本，不跟其receipt_path等私有链接。部署公开interval-interface给出final路径；先核final声明，才读取其output_path：root原件8,301,045 bytes、16,284行、SHA3821564cd1d160cd79f9c66dbdf0facf1907de44e152a750e6a8fee8cc6036f9，与final完全匹配。独立mirror原6,550,785bytes/SHAe96d21…尾缺约77秒的NOT_PROVEN保持；本岗未读或重判其mirror。完整root原件只补诊断，不修独立验收证据。

resource-summary.json按PUBLIC steady窗内**采样端点**取值，各资源600行/600唯一key/0null，未填空、去值或插值；首10:46:39.736986、末10:56:38.733320。边界CPU区间没有重建，统计不能称连续每瞬间覆盖。加权均值=sum(cpu_percent×原interval_seconds)/sum(interval_seconds)，分位为资源CPU nearest-rank，非请求延迟分位。100%=1核，API组含7workers+parent/tracker共9PID；MySQL是共享进程7980，非项目schema独占归因；RSS为进程组采样和，共享页可能重复。

| 资源 | 加权CPU%（100=一核） | CPU中位/P95/max | 采样RSS最大MiB |
|---|---:|---:|---:|
| API组 | 398.62 | 439.38/491.30/527.07 | 1454.30 |
| generator单PID | 78.48 | 81.03/110.00/129.66 | 154.06 |
| 共享MySQL | 74.03 | 77.11/87.65/99.71 | 438.94 |
| consumer | 9.74 | 9.39/17.98/23.03 | 57.97 |
| scheduler | 11.77 | 13.97/22.96/50.97 | 142.22 |
| broker组 | 2.17 | 2.00/4.02/5.02 | 43.27 |

这六组近似CPU均值和约5.75核，不是整机CPU利用率，未包括其它进程/OS/采样器；没有内存压力、swap、磁盘延迟/IOPS/fsync或逐worker数据，不能据RSS小就排除OS压力，也不能据MySQL低于一核就排除锁。

复位附近1Hz样本31.732622UTC在首失败前约15ms，下一点32.732300UTC约晚0.95s。API PID集合及observed状态稳定、组CPU452.69→429.14%，不构成亚秒socket、worker、TLS、keepalive、客户端或监督器原因的证明。PUBLIC已记request-deadline-exceeded=0；外层终态exit/status缺口也不能靠资源补成成功或断言超时/崩溃。需要新开发运行的TCP RST方向/时刻和中性worker生命周期/异常元数据。

## 旧profile能说明什么

81c909 Linux/MySQL sequential普通12/path，真实handler CPU get6.998、contract3.226、transition17.261ms；对应response-only schema0.879/0.247/0.959ms，Rows inclusive CPU3.930/1.569/10.313ms。层次重叠，不相加。listTasks20响应校验11.711ms是旧大列表热点，**round8核心四操作不包含listTasks**，不能把它当本轮主要解释；旧profile也没有createEscalation。

source-comparison.json逐字确认935的api/contracts/OpenAPI/application/common/engine/Rows/settings/escalation facade仍同旧profile；Runtime改项目S与scalar点锁、Workflow有DELIVER权限优先修复。字节同不等于环境、数据、并发或成本相同：旧是x86 Linux、小fixture、顺序；本轮Darwin arm64、40项目/6000任务/9000边/15000review+decision、400client，同机发压。不得把旧毫秒CPU或旧SQL次数直接当935正式根因或精确开销。

## 第一具体观测点

源码api.handle的Server-Timing从**同步handler进入**开始，headers构造时截断：包括Runtime/DB和首轮response schema/wire；**不含**ASGI body/middleware与线程worker进入前等待，且排除末次wire、JSONResponse.render以及发送。故其差值不是纯网络/排队。

root计划由operator仅从已认证旧raw发布匿名时间统计是合适的；须确认冻结latency的开始/结束语义（是否含response校验或writer），不请求源码或payload。对同一完成请求按operation配对计算latency、appdur及逐请求(latency-appdur)的quantiles；**P95lat−P95app不是残差P95**。另可只发布response_bytes分位，供canary匹配输出大小，不读body。

| 结果 | 下一条具体观测 |
|---|---|
| appdur也秒级 | source935采样stage：API schema/wire/render CPU，engine checkout，Rows/cursor，commit，P_S等待连接关系 |
| appdur小而配对残差大 | ingress/bodydone→workerstart、response末次render/send、客户端receive/validation/record分段；不能直接叫网络 |
| strictTLS canary同样慢 | 先看通用HTTP/连接重用/发压调度/证据writer中性时间与IO，非SUT校准不替代业务验收 |
| canary快而SUT慢 | 服务自身/DB与payload校验优先，仍用同源阶段证据定位 |
| RST再现 | 同步收窄TCP RST方向/时间、worker PID/exit/signal、server/client异常类、连接复用/idle age，不记录payload |

## 最小可执行开发隔离顺序（当前未运行）

1. **匿名旧证据配对**：无需重跑，不改原结果，发布计时边界/配对残差/response字节分位。只聚合成功与失败类别，不把无完整HTTP的14次RST拼成Server-Timing值。
2. **通用strictTLS canary**：维护者单独起新端口、新临时目录的固定公开JSON响应，使用原获准HTTP+证据writer；测试小JSON与匹配中性字节分位的padding。400client可校准栈/写入路径，明确非SUT、不改变业务oracle；bytes/s小不能排除高频fsync/锁或加密CPU，需中性CPU/IO计数。不得为了性能关掉正式证据写入；若开发A/B改record方式，单独标诊断、不算验收。
3. **同源935 stage harness**：只新tmp/810_backend_latency，不改业务/持久层。root给新独立schema/user并迁移，私密env不上传，不接任何旧schema；用原create_app、Factory、鉴权、CAS/审计/outbox/幂等。先开发公开小fixture、1client每四路径20请求，setup/warmup/profile-only排除。四路径必须为get/contract/transition/既有事件dedup escalation。ASGI ingress/bodydone、worker提交/开始、原handler、validation/wire/render、Rows/session/cursor/checkout/commit和send末帧同requestID、UTC+mono+实际threadCPU；inclusive/direct-child-exclusive明确，限量采样、独立少量cProfile，避免诊断放大成本。
4. **双机短窗一对隔离**：同一server source/deps/fixture/7worker/TLS/record/mix先开发co-located，再只迁generator；记录迁移的OS/CPU差异，不能把架构改变全归为拆机收益。先40再400客户端，有界短诊断窗口；记录逐workerCPU/线程提交等待、各池checkout wait/checkedout、连接上限、DB lock wait/statement阶段、客户端receive/record。只根据主导阶段选一项配置对照，不跑盲目大矩阵。
5. 开发定位/修复经复审及必要回归后，root另开独立正式freeze/admission、400持续600秒/零错/P95/完整资源与终态，不能用前四步短窗拼通过。

new schema metadata/fixture/private-session接口详见harness-interface.json，根须显式发实际目标才可执行。fixture可从公开3角色/20task开始，之后相同公开inventory规模只用开发自定构造，不借独立私有case分布。DB锁证据只新库连接，低权限P_S data_locks/data_lock_waits/threads，不监控旧共享7980现在的活动数据。

## 哪些参数需要双机验证，为什么先16/32而非64

baseline固定7worker；静态MySQLSettings默认每worker pool5+overflow10，上限15，API理论最多105连接（不等于实际占用）。线程pool/token上限须记录实际值，不能猜默认；DB wait在低CPU下也可把连接长期占住，再令只读contract/get跟着等。增加worker到16/32会潜在240/480 API连接，另有其它角色与管理连接，必须先核新DB连接预算，不能盲增池。

需固定或成对记录：服务器CPU架构/核性能/内存/OS、应用worker数、实际线程token/并发门、每worker池与timeout、DB配置/连接与IO预算、TLS/HTTP keepalive及连接复用、generator单进程/线程并发与证据writer、请求mix/字节大小/target与前驱degree/热点分布、fixture/cache warmup、客户端阶段边界。首次保持7worker/pool5+10，只有测到对应wait或CPU主导再改一项；keepalive变化也须先有RST/idle-age证据，不能用改超时遮住复位。

容量计算只能是规划假设：按冻结计数（包含14失败样本）133674/600=222.79完成/s，API组3.986核÷该完成率约17.89 CPU-ms/完成（含组开销、边界与在途，**不是请求CPU测量**）；六采样组约25.80 CPU-ms/完成。若假设400始终在途、无think、目标**均值**270ms，则需约1481/s及理想API约26.5核预算。这不是P95门槛的数学必要条件：尾5%、实际平均在途/客户端间隙未知，而且不同CPU性能和锁可改变成本，32核没有保证。

因此16核可作拆开发压/观测平台，只有确认CPU主导才做一次32核对照；当前API平均约4核/7worker，未证明8核吃满，64核没有测量依据，7个Python worker也不会因硬件扩核自动利用全部16/32。若DB锁/池或generator单进程先满，加应用核数不解决该约束。费用与购买由root按用户100元预算另核，本岗未开通或报价。

## 优化候选与本阶段边界

未提交产品补丁。当前源码可看到response wire重复遍历、每次新validator、EscalationFacade.current默认逐次读/验证规则；但前两项旧小响应CPU仅很小一部分、规则项仅约9.7%核心请求路径，且缓存涉及reload/错误/线程语义，不能据静态当公共秒级根因。旧global ref原型小路径无一致收益，继续不合入。先让新stage定位可量化热点，再向对应owner提交可审最小补丁/独立微benchmark与必要回归。

资源脚本1013df0实际离线运行、raw/final hash/行数全核，Ruff/format绿；没有新应用/压测/重测试或读取app访问日志。生产0新行，无新cloc，不把旧6326当935准确规模；规模由并行责任岗负责。原formal0、尾缺mirror、14错误、P95失败、根因NOT_PROVEN均保持。报告与执行均AI，不冒用户手写研究经历。
