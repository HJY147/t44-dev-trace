# P7/P16有限对照与限定响应校验原型

操作者backend AI。生产文件、业务函数、SQL、权限、请求校验、错误规则及270ms阈值均未修改。本岗没有访问云UI、原生MySQL、其他root runtime或792/private/验收用例。根报告云SUT已停并保盘；本岗未独立验证云状态。

结论：P16短窗较P7更快，但400客户端四路径P95仍全部大于270ms；零HTTP错误不等于性能通过。响应校验生成代码原型在20任务列表观察到约5–6ms的CPU减少，P7相关小响应收益有限且有反向样本，不能当作当前P7/P16主要性能修复。

## 公共结果绑定

仅新读两个明确白名单，精确bytes/SHA：

- matrix6996B，`4e7bbc36418bdfc25dfd9e8d78c1f6889e213797cc0e2e7c8b8f926513b22cc9`。
- resource11463B，`5af74d7ee2270beb0f8b317e9bbca055584c60ffba08c189c62111b1980d98ef`；其中窗口原始数据声明23269876B/SHA `045fa2e0340f1ea2e04794da93267025895fb43df855803f7b10406d062beee1`，与其stop/mirror-final记录一致。

matrix首行是明确的 `OPAQUE_PART_3_VERIFIED_NO_DISCLOSURE` 标记，因此首次按纯JSONL解析失败；后仅容许该精确标记，其余行严格JSON解析。没有读取PUBLIC内列出的任何private文件。P7使用本岗前阶段已核实的derived数据，未扩大当前root白名单。

PUBLIC声明源a12e9e70b963bacafda3242bb6d82e53ee912ff1；P16实际cohort字段seed44、anchor04:00与既有P7一致，selection相同为根协调报告，本岗未另读其私有selection原件。两个云矩阵不是本岗对容器实物源码的独立鉴证。

## 400客户端短窗

两组各8000请求，均200=6000/202=2000，failed/aborted/deadline clients=0。P7 started窗口21.890740s、barrier窗口21.742456s；P16分别15.144699s、14.993489s，barrier前0.151210s。P16 started/finished为 `09:47:52.170963Z`–`09:48:07.315662Z`，与资源窗口逐字对应。

started分母折算P7/P16=21927.079669/31694.258169请求/分钟；barrier分母=22076.622807/32013.896165。P16短窗少30.816871%，但这些只是等效速率，没有完整分钟最低吞吐或600秒稳态。

| 路径 | P7 P95 ms | P16 P95 ms | 本次P95下降 |
| --- | ---: | ---: | ---: |
| getTask | 1555.055565 | 1395.621864 | 10.252605% |
| validateContractPayload | 1370.412573 | 979.711415 | 28.509747% |
| transitionTask | 1680.087258 | 1499.957964 | 10.721425% |
| createEscalation | 1840.028403 | 1447.238331 | 21.346957% |

四项仍失败270ms，且transition最大值3389.143354→3494.455960ms反而升高，不能挑P95掩盖长尾。各路径分位数不相加、不平均成整体P95。P16的40客户端组只有getTask P95493.576627>270ms，另三条≤270ms；这也不能替代400客户端正式组。

这是顺序发生的一次开发对照，间隔数小时、不同namespace/数据库/worker配置、主机背景与缓存状态均可能混杂，没有ABBA重复或置信区间。相同源/seed/选择增强可比性，不证明worker数是唯一原因。

## 资源窗口

P7每角色22采样，P16每角色15采样。P16零记录采样错误，14个已知sequence相邻pair无内部缺口/倒序，头尾前后有采样；首延0.511583–0.515699s、尾距0.685937–0.689182s，含边界最大start间隔约1.06317–1.06469s。scheduler15行missing_role，CPU/RSS/cgroup全null，不是运行资源通过。

| 指标 | P7 | P16 |
| --- | ---: | ---: |
| API CPU p50 % | 543.177190 | 1117.675920 |
| API CPU P95 % | 1016.408952 | 1269.993555 |
| API CPU max % | 1208.942075 | 1269.993555 |
| MySQL CPU p50 % | 115.616128 | 189.915211 |
| MySQL CPU P95 % | 153.853657 | 209.624289 |
| MySQL CPU max % | 159.899578 | 209.624289 |
| API进程RSS max bytes | 899485696 | 1940951040 |
| API cgroup memory max bytes | 785215488 | 1633492992 |
| MySQL进程RSS max bytes | 1433186304 | 1543487488 |

CPU以单核100%计，P16 API中位约11.18个单核时间占用，并非host百分比。P16只有15采样，nearest-rank P95恰为max；P7的P95为第21顺位、即第二大，量化粒度不同。RSS进程和可重复共享页，不能与cgroup memory.current互换，不加不同角色P95或不同时间max来冒整机峰值。资源相关性不证明CPU、MySQL或网络因果瓶颈。

## 原型的安全范围与设计冻结

先冻结 `tmp/788/schema-response/DESIGN-FROZEN.md`，SHA `f48690390196ca1802da9ab380ab587bdaf6e66a34db21e9f21c555799d45734`。官方primary [fastjsonschema文档](https://horejsek.github.io/python-fastjsonschema/index.html) 说明支持Draft04/06/07，并指出regex/default差异；不能将其直接冒充当前Draft2020-12。单独hash锁定2.22.2，只装本岗隔离venv，不改产品依赖锁。

原型仅白名单中的get/list/contract/transition成功envelope及data_schema。只接收固定可信规格，不编译客户端schema；不缓存用户上下文。编译当前兼容子图：本地无sibling的ref、无循环、明确已知keyword；不支持oneOf/dynamic/anchor/id/unevaluated/未知keyword；multipleOf仅正整数或0.25；if只允许literal-property/required条件；date-time/uuid格式委托当前原FormatChecker；禁default注入；非JSON/非有限数直接回原。root及所有传递ref内容都进入cache key，SPEC变化不会复用旧编译器。

任何unsupported、编译异常、快速拒绝或未知schema调用原violations；只在快速确定成功时返回[]。库错误路径/消息从不替代原列表，顺序与前100映射仍由原函数生成。请求schema全部回原；只在临时进程patch api/application的violations别名，业务和SQL未变。有限差分不是全等价证明，仍需38操作/故障/并发/未来schema审查才能提出生产准入。

## 保留的失败与两次运行

根报告前一派工因模型capacity错误中断，本岗没有provider原始错误码/次数，不将其虚构成产品或本地工具失败。本段保留原context/模型继续。

Run01：27准备+4响应seed=31 HTTP成功，guard阶段停止，**没有计时**。exact2.22.2在detailed_exceptions=False时纯compile实测KeyError('definition_rule')；原型回原校验器，随后注入故障守卫错误地假定cache存在，再触发KeyError。原始raw与两工具当时源码都封存；没有把guard写成通过，也没有观察到falseaccept。

同版本detailed_exceptions=True纯compile成功。执行前另冻结 `DESIGN-AMENDMENT-01.md`，SHA `ab4b9ff40452250549a2f8096f53e1a51b4b13e5ecac72c26f096c49b33b646f`；仅改诊断选项/检查cache可用性，计时样本降为7，维持累计HTTP≤200，不放宽兼容子集或守卫。

Run02：从Git准确a12导出51文件并核blob，新内存SQLite/生产SQLAlchemy+UoW/FastAPI实际worker。27准备+4seed+16warm+112计量=159 HTTP，两个运行累计190；网络/MySQL尝试计数均0。所有HTTP成功，客户端每个响应独立用原schema完整再核；128个被Probe记录的warm/计量均200、threadCPU>0且≤handler墙时。

**计时前424项守卫**通过：8合法seed、400字段/类型/删除变异、状态与日期边界、root和ref内容改变、原FormatChecker注册更新、ref sibling/unknown、oneOf重叠、dynamic/unevaluated、循环提前拒绝、tuple/nonfinite/nonstring-key和注入fast异常。原错误列表/顺序与异常种类均相同，未发现falseaccept。

**计时后另补13项纯守卫**，没有HTTP/DB：重复标量/对象、bool与integer相等区别、105个嵌套类型错误的前100原顺序、default不注入、quarter multipleOf、regex末尾换行回退等，全部相同。它们不是424项前置守卫的一部分，不倒写为计时前完成；完整设计的这些特定覆盖补得较晚，因此ABBA仍作为探索结果，不能称已满足全部前置覆盖的受控验收。两阶段合计437个有限守卫不是全等价或独立测试。

## 无profiler的实际A/B/B/A

A=原violations，B=原型。每phase每路径7次，先各1次warm；同app/同内存DB，按get/list/contract/transition轮转，时间取实际同步handler线程CPU。计量阶段编译CPU为0，cold/guard累计编译82.014544ms另列。状态/version随真实写增长，单次顺序对照存在缓存/主机频率/背景负载混杂，没有统计区间。

| 路径 | A1 CPU中位ms | B1 | B2 | A2 | A1−B1 / A2−B2 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| getTask | 2.000208 | 1.430708 | 1.759875 | 1.867208 | 0.569500 / 0.107333 |
| listTasks，20任务 | 8.583666 | 2.784209 | 3.364958 | 8.570000 | 5.799457 / 5.205042 |
| validateContractPayload | 1.234500 | 1.129459 | 1.423875 | 1.139084 | 0.105041 / -0.284791 |
| transitionTask | 4.865708 | 4.357250 | 5.395041 | 5.037458 | 0.508458 / -0.357583 |

两个B各98次校验调用：35个白名单成功响应/data快通道，63个请求等仍回原；测量时没有新编译。保留contract/transition的反向B2，不能挑B1或列表收益代表P7四路径；本轮未测createEscalation。更不能用前次较慢Mac profile数字当同一环境基线而夸收益。

## 交接判断

本轮没有找到已证明能让P7相关小响应下降数毫秒的安全改动。大列表的完整schema遍历有毫秒潜力，但listTasks不在P7/P16四路径内；不建议当前直接生产引入生成校验器。原型152物理行、137非空非#行（不是cloc），加响应钩子/依赖与未来守卫后是约140行以上的正成本，不是源码节省；生成代码/第三方依赖不能用于规避统计口径。

重复wire的小响应CPU此前就不大，本轮没有另建wire实验刷正结果；此前select(table)每条约5µs仍只是零增行小候选，不充当主要收益。保留实时鉴权/事务/锁/校验/阈值，若未来扩展请求生成校验或其他引擎，应另设计/准入，不由本轮自动授权。

完整counterexample/guard/phase逐请求数据和失败原件见三个json.gz；raw/gzip双SHA/字节/roundtrip见raw-manifest.json；准确源码/设计hash和静态check/format原件齐全。没有产品CI、MySQL执行、独立验收或云部署，新一轮400/600也未授权。
