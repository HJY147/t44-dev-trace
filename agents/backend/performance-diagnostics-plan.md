# 性能诊断准备 A：未运行实验

实际派工ROLE-backend-PERFORMANCE-DIAGNOSTICS-v1。工作树已快进397bd7973cfd835c635634d32e0c98ae56d74949（指定父产品43f51570e62e3160f7995c45bdddaf2f123242b3）。原proposed提示词保留原状态；本次实际dispatch另归档。阶段A准备时独立正式报告尚未发布，未读其文件/脚本；随后根正式授权两件公开报告，已核SHA并仅阅读这两件，优先修IAT01～05，不推定性能瓶颈。原始目标仍为400并发、600秒、P95≤270ms及≥1000次/分钟，诊断短跑不代替正式验收。

## 真实入口与观测边界

| 位置 | 输入 → 输出 | 拟观测/限制 |
| --- | --- | --- |
| api.capture → 同步handle | 原HTTP请求 → 严格JSON响应与现有Server-Timing | 现有app计时从worker内开始；ASGI总墙钟另记，含接收/路由/线程调度，非纯排队 |
| Runtime.execute | Call+validate回调 → status/result/replayed/original_request_id | 请求worker线程CPU、墙钟；可选每请求cProfile，仅覆盖Runtime子树，不包含之后HTTP envelope校验 |
| authorize/authenticate | token摘要查会话、实时用户/项目/成员 → actor/member/project | 保持会话撤销和项目权限；只看累计耗时/SQL数，不缓存身份 |
| validate_request、api.violations、api.wire | Schema/参数/JSON → 规范化Call、脱敏错误或wire数据 | 单独计调用数/墙钟/线程CPU，保留请求、提交前data和最终响应完整校验 |
| claim/locked_scope/complete | 已认证Call/幂等摘要/版本 → 行锁、租约owner或持久快照 | 分段为包含子调用的区间；不能相加成总耗时；不改session→idem→project→members→tasks锁序 |
| Business.dispatch/validate_data | 参数化Gateway+Call → 业务data/成功校验 | 状态机/证据、CAS、audit/outbox/结果同事务，拒绝后独立审计保持 |
| owner Engine.connect | UoW首次使用连接 → Connection | 获取连接+pre-ping/新连接初始化聚合，不等于纯连接池等待 |
| before/after_cursor_execute、handle_error | 实际DBAPI执行 → 完成/错误 | 只记次数/墙钟/错误数，不存SQL/参数；包含DB执行、锁与网络，未包含完整结果转换/commit |
| 数据库内部锁/提交 | 事务/索引竞争 → server侧等待 | 当前工具不能直接细分；阶段B需database在t44_profile提供中性观测，不由后端另写SQL |

源码事实：同步FastAPI handler经线程池执行；MySQLSettings默认每进程pool_size5/max_overflow10，生产启动worker数由实际命令另记。不能把默认配置当已测正式环境。`violations`每次构造validator/引用Schema，Runtime又有多次鉴权事务，这些只是待量化调用点，当前没有证据排定CPU、SQL、锁、pool或验证谁是主因。

## 955工具的实际范围

`tmp/backend/955_perf_profile.py`已写，仅准备、未执行/导入/编译/静态验证。无test用例，不占独立验收脚本；955本岗专属，下个编号954。当前仅提供诊断serve包装，不生成业务数据、不迁移/seed、不登录、不发负载；中性HTTP驱动在环境/公开报告到位后补到同一文件或使用根授权驱动，不能借独立测试私有脚本。

运行时必须显式`--execute-stage-b`、DATABASE_URL所选库和T44_DATABASE均为t44_profile；只绑定127.0.0.1:18083、单worker，最长120秒，输出目录必须新建。baseline模式使用真实create_app+owner UoW，不加观测hook；timings/profile模式只在本诊断进程包裹方法和SQLAlchemy event，不修改生产文件、业务字段、冻结响应或Server-Timing语义。

输出metadata.json（SHA/机器/Python/进程/worker/pool/CPU/窗口）、requests.jsonl（随机样本ID/服务request_id/operation/status/字节数/含子调用阶段计数与耗时/SQL数）、可选pstats（函数名/调用时间，不含实参）。无口令、Bearer、DSN、自由文本或SQL参数。输出在ignored运行目录，归档前只取脱敏指标。最多50000条详细样本，多出计dropped_records，不把丢样本当完整结果。profile在Runtime结束后写pstats会拖慢HTTP，该模式绝不能用于性能达标判断。

## 阶段B短跑方案（需根继续派工，当前不能执行）

1. 收到已发布报告路径与被测SHA、根确认资源空闲、新库t44_profile及中性角色/服务账号。先记录机器、所有共机进程、实际API/DB/worker/线程池/连接池配置。可记录/比较原被测SHA与当前源SHA，结果各自分开，不把新源当原基线。
2. 在profile库保留无修改基线，root/DB初始化独立前缀数据及三类输入；不触dev/acceptance/perf。命令模板（尚未运行）：`PYTHONPATH=backend .venv/bin/python tmp/backend/955_perf_profile.py --execute-stage-b --mode baseline --seconds 30 --output <全新ignored目录>`。DSN仅由私密env提供，不出现在argv或日志。
3. 三接口分开短跑，先1并发少量正确样本，再8/32并发各10～20秒；每组有单独冷/热标记和原始请求计时。先不跑400/600秒，不并行其他诊断。baseline先记录客户端E2E、Server-Timing、状态/成功数；相同输入分布另起timings，再以1并发少量profile定位。诊断开销不能从结果中主观扣除。
4. 任务流转：POST /api/v1/projects/{p}/tasks/{t}/transitions，真实developer-owner、expected_version和合法action；新写用不同任务/正确版本/新key，重放/竞争拒绝另组，不把同key缓存吞吐当新写性能。200 TransitionEnvelope。
5. 契约校验：POST /api/v1/projects/{p}/contract-validations，已认证成员；category1+TaskCreate，或category2/3+task_id+对应payload；无幂等键、无业务写，200 ContractValidationEnvelope。非法输入/项目越权单列，不能把422当业务成功。
6. 升级：POST /api/v1/internal/projects/{p}/tasks/{t}/escalations，仅授权服务scope，expected_version/schedule_version/rule_version/scan_run_id；服务端决定时刻/收件人，202 EscalationEnvelope。首次创建、同key重放、事件已存在created=false分别统计。完整MQ投递/降级与处理链仍需owner真实进程；API202只说明已持久，不冒充已通知。
7. 关联CPU/SQL/连接获取/ASGI前Runtime区间；数据库锁待owner证据。一次只选择一个有因果证据的优化，先回归被冻结Schema、auth/revoke、并发CAS/idem、拒绝审计、outbox再对照短跑。原失败/基线不覆盖。真正优化另派工，当前未改任何生产实现。

## 官方资料依据与限制

- Python cProfile用于调用剖析，有观测开销，不用于证明benchmark通过；thread_time只计当前线程CPU，perf_counter计等待墙钟。[profile](https://docs.python.org/3.12/library/profile.html)、[time](https://docs.python.org/3.12/library/time.html#time.thread_time)。
- SQLAlchemy官方建议分别看查询和代码，并给出before/after_cursor_execute计时；工具不启echo、不输出原SQL/参数。[SQLAlchemy2.1性能诊断](https://docs.sqlalchemy.org/en/21/faq/performance.html)。
- Starlette同步endpoint经anyio.to_thread.run_sync，共享默认40令牌；这是框架默认，阶段B应记录实际值，不先调大线程数。[线程池](https://starlette.dev/threadpool/)。旧www.starlette.io/threadpool抓取502后改用官方新域，未据失败页面作结论。

阶段A没有延迟、CPU、SQL、pool/锁等待数值，没有优化收益或性能结论；3500–5100源码目标仍未满足。诊断文件在既定tmp范围，未搬移业务逻辑、改变统计口径或删必需功能。

续派纠错：原准备提交c44bd33曾写18082，工具未运行；总协调确认该口为不可变原性能API PID16590后，工具/当前方案固定改18083，并在metadata记录port。原提交作为历史保留，不绑定/停止18082。业务IAT修复优先，阶段B仍未开始。

续派真实性约束：955启动前按脚本自身所在Git树取HEAD并拒绝相关产品未提交修改；记录实际t44/api/contracts/runtime/tasks/projects/reviews/persistence.rows的__file__及文件SHA、实际openapi.json SHA，若PYTHONPATH导入别树则在创建Engine前拒绝。当前仅源码静态检查通过，未启动验证这些hook；Stage B待业务checkpoint及总协调避开Word渲染的明确窗口。

## 首次实际窗口后的状态（历史准备稿不覆盖）

业务修复CI362通过后获root独占短诊断窗口。首启工具startup hook失败已修；96e4源baseline服务实际启动两次并正常退出，但bootstrap登录收到非JSON502，尚未产生fixture或任何主样本。系统代理为待验证原因，两Client现固定trust_env=False，仅直连127.0.0.1:18083；这不改变TLS校验。响应JSON非法时仍记录实际HTTP状态。metadata补实际UTC起止，后续仍核exact source/import。

两服务已停止并通知root释放LO；下一次服务/请求须在协调后的新窗口执行。下一步先直接bootstrap验证候选，再baseline1/8/32各10秒、timings同组、profile1并发最多3请求；只测契约入口且验证HTTP200和业务valid=true/无violations。没有主样本前不分析空闲CPU或把502当产品延迟失败。归档profile-bootstrap-*与profile-proxy-static.log。

## 修正后的单调用方案（待新quiet窗口，尚未运行）

前两次setup真实失败保留；第二次bootstrap已成功，但下一工具调用晚于45s服务自停，3个sanity只有ConnectError。root要求改成一个持续控制器，不能让请求启动依赖下一次模型调用。源码4c20候选Schema版本修正已获394项完整CI通过，生产代码当前保持该字节。

955 `--mode orchestrate --seconds 10` 在一次exec内顺序管理三个独立子服务，服务每个120s安全上限、完成矩阵即主动正常SIGTERM+wait，异常finally清理；若强制kill则标run失败。全局160s，预计约70–100s，预留≤3分钟。baseline阶段先bootstrap再1并发3请求，严格核三类HTTP200/valid=true/无violations；之后baseline和timings各1/8/32并发10秒，profile仅1并发3类各1请求。任何失败停止后续阶段；实际argv/起止UTC/exitcode/PID、actual imports/hash写入metadata，不记录DSN/口令/Token。baseline与timings测量范围不同，不把hook开销扣除或外推正式4worker/400/600秒收益。

以下单命令仅为准备稿，提交controller后收到root新窗口才执行，输出目录每轮新建：

```sh
PYTHONPATH=backend .venv/bin/python - <<'PY'
import json, os, runpy, sys
from pathlib import Path
work = Path.cwd()
private = work.parent / '.runtime'
env = json.loads((private / 'profile-environment.json').read_text())
env['PYTHONPATH'] = str(work / 'backend')
os.environ.update(env)
os.umask(0o077)
sys.path.insert(0, str(work / 'backend'))
script = work / 'tmp/backend/955_perf_profile.py'
sys.argv = [str(script), '--execute-stage-b', '--mode', 'orchestrate', '--seconds', '10',
            '--credentials', str(private / 'profile-credentials.json'),
            '--output', str(private / 'backend-profile-orchestrated-contract-03')]
runpy.run_path(str(script), run_name='__main__')
PY
```

准备时controller仅Ruff/format/AST通过，没有运行/性能样本。归档profile-controller-static.log；不重复跑已验证生产代码全套。

## 第三窗口实际结果（不覆盖前文准备与失败）

工具245在13:18:49.973332Z–13:19:57.093091Z实际完成所有子阶段，最终profile断言错变量导致整体exit1。18289主样本+3sanity均HTTP200且有效，三服务正常exit0。真实命令、原始metadata/JSONL/pstats/子日志与指标在profile-contract-03-*；原metadata不改。工具赋值修后仅离线正确操作数检查及Ruff/format/AST，不再次负载。

六组短P95与阶段inclusive/线程CPU见analysis/summary；仅初步看到鉴权持久访问及连接获取/游标墙钟增长，尚无纯poolwait/数据库内部锁因果证据，3份冷cProfile不算CPU-only或稳态收益。后续测量/优化由root另派并协调窗口，不自动继续。正式400/600/4worker条件与失败、源码超限均保持。
