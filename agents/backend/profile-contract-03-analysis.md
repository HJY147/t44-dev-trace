# 契约校验短诊断 03：子阶段有效，控制器整体失败

实际被测工具提交245e56b9866b34d5c75b5d0670ba735a5ee75249；实际导入本工作树backend/t44，关键模块路径/hash在原metadata。生产文件与394项开发CI通过源4c20f32b71635016815420472b9d4bb4fa850df0字节一致。仅t44_profile、127.0.0.1:18083、1worker，实测线程令牌40、pool_size5/max_overflow10。未修改生产代码、配置、冻结14件或原性能条件。

2026-10-23T13:18:49.973332Z至13:19:57.093091Z，控制器67.119秒。bootstrap、sanity、六组10秒闭环和3次profile均实际完成；控制器最后RuntimeError/exit1原样保留，不能称整轮成功。其最终断言误读bootstrap的category_counts={}，没有接收profile client的返回值；不是业务HTTP错误。只把赋值移至采样client调用，原断言保持；修后仅离线读取原metadata确认正确操作数，不重新启动/请求/跑矩阵。

| 模式 | 并发 | 请求数 | E2E P95 ms | HTTP/业务错误 |
|---|---:|---:|---:|---:|
| baseline | 1 | 2277 | 5.444 | 0 |
| baseline | 8 | 3631 | 33.143 | 0 |
| baseline | 32 | 3282 | 149.208 | 0 |
| timings | 1 | 2506 | 4.856 | 0 |
| timings | 8 | 3418 | 35.185 | 0 |
| timings | 32 | 3172 | 151.564 | 0 |

P95采用nearest-rank ceil(0.95*n)，不是原k6算法/正式结果的直接可比统计。baseline9190、timings9096，加profile3，共18289主样本；sanity另3。每项均检查HTTP200、valid=true、business_guards_executed=false、category/validated_operation_id匹配及无violations。三类候选近似1:1:1，实际计数见summary。timings/profile9099条服务记录与客户端request_id一一匹配，dropped0、SQL错误0。baseline不挂逐请求hook，record_count0不能解释为没有请求。

| timings平均/毫秒 | 并发1 | 并发8 | 并发32 |
|---|---:|---:|---:|
| Runtime墙钟 / 当前线程CPU | 3.085 / 2.081 | 16.690 / 2.531 | 69.400 / 2.553 |
| authorize墙钟 | 1.258 | 8.336 | 47.677 |
| acquire+pre_ping墙钟 | 0.202 | 2.960 | 33.141 |
| SQL游标墙钟 | 1.243 | 8.574 | 23.958 |
| 请求校验CPU | 0.364 | 0.376 | 0.386 |
| violations聚合CPU | 0.447 | 0.465 | 0.477 |

阶段含子调用，不能相加。Runtime CPU不是整个HTTP CPU；请求校验与violations也有嵌套。每请求SQL游标次数平均8.666～8.667；acquire平均2次。pre_runtime的P95为0.262/3.461/15.688ms，包含ASGI处理/验证/线程调度等，不是纯队列。连接获取包含pool checkout、pre_ping、新连接初始化及调度，不能标为纯poolwait；SQL游标包含驱动、网络、server执行/等待，缺少数据库内部锁/CPU证据。只读验证也不代表写任务或升级接口的锁行为。

三份cProfile各1样本，仅Runtime子树。项目函数inclusive墙钟top3：category1 execute18.097/authenticate14.967/rows14.885ms；category2 execute9.304/rows7.110/_execute6.146ms；category3 execute7.606/rows5.163/authenticate4.562ms。合计最高execute35.007、rows27.158、authenticate24.111ms，互相重叠。默认cProfile使用墙钟，含等待；self最高SSL read5.609ms、一次冷握手1.612ms。不能把冷启动3样本称纯CPU热点百分比、稳态性能或优化收益。profile写pstats另有观测开销，profile3次P95=24.386ms不用于达标判断。

最小后续方案是由持久层owner协同拆分checkout、pre_ping/新连接及参数化查询构造/执行，另记录热样本CPU，证实等待来源后再选单一优化。目前不改pool、鉴权/撤销、锁/CAS/幂等、独立拒绝审计/outbox或任何契约校验。baseline/timings依次运行且冷/热不同，不能把其差值当优化效果；原4worker/400VU/600秒与P95≤270ms正式条件及失败历史保持。本轮也没有3500–5100源码规模通过结论。

三个子服务PID42015/42103/42148均正常exit0，无forcedkill，进程检查均已消失；root已收到窗口释放。原metadata保留failure=RuntimeError。归档profile-contract-03-metrics.zip含38份原始metadata/JSONL/pstats/子进程日志；排除私密bootstrap/fixture.json（0600、ignored）。各文件与archive SHA见raw-manifest，已扫描确认实际私密凭据字面值没有进入归档。原控制器最外层stderr没有单独重定向文件，下方命令及退出1为工具session11938执行事实，不伪称另存了完整原stderr。

真实启动命令（工作目录为backend独立树，仅这一次实际执行）：

```sh
PYTHONPATH=backend .venv/bin/python - <<'PYRUN'
import json,os,runpy,sys
from pathlib import Path
work=Path.cwd();private=work.parent/'.runtime';env=json.loads((private/'profile-environment.json').read_text());env['PYTHONPATH']=str(work/'backend');os.environ.update(env);os.umask(0o077);sys.path.insert(0,str(work/'backend'))
script=work/'tmp/backend/955_perf_profile.py';sys.argv=[str(script),'--execute-stage-b','--mode','orchestrate','--seconds','10','--credentials',str(private/'profile-credentials.json'),'--output',str(private/'backend-profile-orchestrated-contract-03')]
runpy.run_path(str(script),run_name='__main__')
PYRUN
```

原子命令实际argv/UTC/exitcode全部在orchestrator-metadata.json；其中子进程全部exit0，最终整体exit1。后续离线category映射曾两次KeyError，因pstats文件名是sample_id而非request_id；改用server sample_id→request_id→client category映射后得到上述逐类结果，没有重跑负载。静态及离线重处理记录profile-controller-fix-static.log与profile-offline-controller-check.json。原失败/原件不改写，修后控制器实际运行仍未验证。
