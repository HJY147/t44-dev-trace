# a12 Python CPU 定位与零增行查询构建候选

操作者为backend AI。产品未改，云UI/原生MySQL/旧tmp796/792私有资料/测试用例均未访问。先写design.md，再执行一次135 HTTP本地诊断及一次纯表达式ABBA微测；不是400并发、600秒或正式P95验收，云根因仍NOT_PROVEN。

## 准确执行范围

从Git准确源 `a12e9e70b963bacafda3242bb6d82e53ee912ff1` 导出全部51个 `backend/t44` 文件到新TemporaryDirectory，每文件核Git blob与SHA-256。工具源码未替换产品函数，只在诊断进程包裹实际同步handler和调用形状观察；既有834开发夹具准确SHA `e0a49e630957268195adc6d6f1cd924bf6481b533f7c3c276b3e832b21aeba49` 仅复用新内存SQLite/3用户/TestClient准备，不运行其MySQL、旧实验或测试用例。

新venv由仓库锁文件 `3b15a7bdf93024750835ac20584a140eb93f1dc7476be61bb0af145e8ff0cc30` 的67个hash锁定依赖建立。实际Python3.12.14/macOS，FastAPI0.161.1、Starlette1.9.0、SQLAlchemy2.1.6、jsonschema4.26.0、referencing0.37.0、httpx0.28.1。进程内显式注入生产SqlAlchemyUnitOfWorkFactory/RowsGateway，SQLite新内存库；unset数据库环境变量，禁用socket connect/connect_ex/create_connection及MySQL engine入口，实际阻断计数0；未启动HTTP监听器或后台worker。

时间 `2026-10-28T08:36:02.568317+00:00`–`08:36:23.874540+00:00`。实际135 HTTP：27准备（3登录、1项目、2成员、1迭代、20任务），再4预热、80无profiler计时、20独立cProfile、4单独shape观察。所有请求达原成功状态，所有响应再由原冻结schema独立校验；108个主请求全部200，threadCPU正且不超handler墙时。任务流转使用manager BLOCK/UNBLOCK真实递增version/CAS、幂等、审计及outbox，未把重放当业务写。

cProfile在真实FastAPI同步worker线程启用，timer=`time.thread_time`；无profiler的CPU也读同一线程的thread_time_ns。shape计数在其他阶段关闭，但其包装函数的条件分支仍有少量仪表成本，因此这些CPU数值也不是完全无仪表的生产基准。profile开销单独列；其函数调用仪表对不同函数密度的扰动不同，不能把下面profile份额当作非profile真实CPU占比，更不能外推MySQL/云。选择cProfile避免附加云进程、权限与py-spy采样环境变化；本轮没有安装/附加py-spy。

## 真实函数与调用形状

| 路径 | 无profile样本数 | handler CPU中位ms | handler墙时中位ms | 独立profile数 | instrumented CPU均值ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| getTask | 20 | 7.580688 | 8.702521 | 5 | 21.408139 |
| validateContractPayload | 20 | 4.329709 | 5.225417 | 5 | 11.621692 |
| transitionTask | 20 | 20.397834 | 24.385813 | 5 | 55.482632 |
| listTasks，20任务页 | 20 | 31.396083 | 37.333979 | 5 | 137.182933 |

下面是互斥的函数**独占**CPU分类，各行相加等于该路径instrumented profile总CPU；调用树累计CPU仅用于排序，不相加。`other`包含builtins、SQLite、T44其他函数、仪表等，未进一步归因给上游包。

| 路径 | SQLAlchemy表达式 ms/req | SQLAlchemy其他 ms/req | jsonschema/referencing ms/req | common.wire独占 ms/req | other ms/req |
| --- | ---: | ---: | ---: | ---: | ---: |
| getTask | 4.333 | 3.337 | 4.851 | 0.421 | 8.467 |
| validateContractPayload | 2.178 | 1.636 | 2.693 | 0.109 | 5.006 |
| transitionTask | 13.651 | 8.608 | 10.998 | 0.539 | 21.686 |
| listTasks | 4.775 | 3.852 | 77.084 | 6.989 | 44.482 |

具体证据可在baseline原件每路径functions找到源文件、准确line、primitive_calls/calls、exclusive/inclusive原值：

- getTask五个profile有45次RowsGateway.rows（9次/请求），10次authenticate；两轮各读session/user/membership/project，再读task。shape的一次实际请求确认相同9次rows。
- contract五个profile有20次rows（4次/请求）、5次authenticate，已经是一次认证/UoW专门路径；不是尚可再删一轮认证的旧版本。
- transition五个profile有106次rows，15次authenticate；单次shape观测21次rows，含三次用户/成员读、4次项目读，以及claim/owner fence、membership共享锁、task唯一PK更新锁等。五个profile交替动作不同，不能把106/5当每种动作固定查询数。
- SQLAlchemy `sql/coercions.expect` 的get/list/contract/transition调用数分别720/760/280/2387，`sql/cache_key._generate_cache_key` 在transition有141次主要入口；这支持检查语句构造成本，不能仅凭调用量宣称可获得相应HTTP收益。
- common.wire的primitive/递归总calls：get30/685，list220/12350，contract20/165，transition35/895；均为五个profile合计。API当前对同一个payload在响应schema检查和JSONResponse前各递归一次，模型与Runtime也做转换。小响应的实际profile wire独占不大，20任务列表才明显放大；list不在P7四路径工作负载内，不将其结果替代P7。
- validator构造的五样本累计CPU折合get0.549/list0.439/contract0.569/transition1.054ms每请求，仍远少于完整schema遍历；不复活旧构造缓存、引用原型、15行委托或OperationPlan+14路线。

## 候选：全列查询使用select(table)

准确位置为 `backend/t44/persistence/rows.py` 的 `RowsGateway.rows`：

```diff
 fields = (
-    tuple(t.c)
+    (t,)
     if columns is None
     else tuple(t.c[k] for k in self._fields(t, dict.fromkeys(columns)))
 )
```

现状 `select(*tuple(t.c))` 把全列逐个传给SQLAlchemy coercion/cache-key结构；候选 `select(t)` 由Core展开相同表列。仅改变一个AST表达式，其他函数AST逐字结构一致；默认全列分支变化，显式columns投影分支不动。没有语句缓存、用户上下文缓存、少查SQL、缩小投影、跳过校验或改锁。预计净有效行变化0（没有新cloc或全局规模达标声明）。此为数据库责任路径，只交协调岗转DB岗实施/回归，当前产品及P7/P16准确源均未改。

实际纯等价检查使用生产RowsGateway.rows，其_execute在诊断子类截获表达式，根本不构造Session/Engine：18注册应用表各5组合，加9拒绝，共99 cases；MySQL和SQLite两方言共198对签名全部完全相同。每一对**完整original/candidate**原件均在query-construction-01.json.gz的signature_evidence：

- SQL文本逐字符、bound params字典相同；IN含非空/空集、limit0、offset、负向排序、普通查询、share/update/skip_locked均覆盖。
- `statement.selected_columns` 的key/type顺序相同，compiled result-column的keyname/name/type顺序相同；显式id列投影保持。
- 非法表、where字段、投影字段、排序字段、布尔limit、负offset、非法lock、无lock的skip_locked、非法predicate操作，异常类型/消息相同。

这证明有限纯表达式覆盖的SQL/参数/编译结果布局等价，未证明实际MySQL结果物化、锁竞争、异常/连接故障或完整应用等价。SQLite方言会忽略锁，MySQL方言签名明确保留锁语句；不能用SQLite编译当作MySQL运行。后续必须由DB岗核原RowsGateway恶意ClauseElement/嵌套值拒绝、datetime/NULL/JSON/Decimal绑定、显式列/缺行/重复字段，以及新隔离MySQL查询结果和锁/事务回归；禁止为提速降低断言。

无profiler的纯构建ABBA：A为准确原函数，B为仅该表达式的临时函数；每phase5批×100条=500条语句，五种真实表users/auth_sessions/project_members/projects/tasks等权。计时用thread_time_ns；没有SQL执行或HTTP。

| phase | 5个批均值的中位数 us/statement |
| --- | ---: |
| A1 | 21.665000 |
| B1 | 16.779580 |
| B2 | 16.013330 |
| A2 | 21.147080 |

A1/B1=1.291153倍，A2/B2=1.320592倍；相应纯构建CPU减少22.549827%/24.276401%，每条仅约4.89/5.13微秒。这是一次本地纯构建ABBA的真实观察，不是置信区间；未计Session/执行、SQLAlchemy缓存键生成、DBI/O或HTTP。不能拿“1.32倍”描述整体接口；没有候选端到端运行，也没有性能通过或根因证明。

## 其他路线与交接

API把同一payload只wire一次再给schema/JSONResponse复用，可另作局部设计，预计净+1有效行；必须保留完整envelope schema、500 fallback与错误体转换语义。当前小响应wire独占观察不足以把它排成主要优化，本轮未做候选实现或HTTP对照。

重复认证/项目上下文确实可见，但跨UoW复用旧session/identity/membership/project会触及实时撤销、RC可见性、校验前授权、claim/fence及原错误优先；本轮不给删除鉴权或跨事务缓存建议。`_fields/_clauses`的重复校验亦保留，不凭profile直接删除安全检查。优先交DB岗审零增行表达式候选。

原件baseline611580B/SHA `0df044fba87bfe581125774ca2bc7006e76d34bb8b8f7b4b5f8ba4e9db5e532e`；query887024B/SHA `03876a7501eb0e2b9fe9f1a346c7dc42a7e2b9fb9a851dd68d1646b00c128462`。均无损gzip提交，raw/gzip双SHA、字节及roundtrip在raw-manifest.json，未删改本地原JSON。summary/verification为可重算派生资料。

静态check/format最终三工具均绿。首次summarize初稿有两个E702分号lint失败，修后才执行派生；不是产品失败。原HTTP诊断有Starlette httpx兼容入口deprecated warning，未抑制；未改锁依赖或换客户端刷数。初稿执行前root路径索引/采样时间端点在静态阅读时修正，未生成失败运行或旧数字。没有全产品CI、MySQL运行、独立验收、云操作或额外HTTP候选对照。原P7/P16失败/未完项保持。
