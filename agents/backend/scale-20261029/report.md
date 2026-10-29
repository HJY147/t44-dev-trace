# 契约缓存候选与规模复核（2026-10-29）

本轮由后端 AI 岗执行；仅本地、无云操作、无付费资源。先行设计 `c0671440`，准确产品候选 `7d101e02590566bcde5385563c45d9c8866cc53f`，父产品基线 `f7cdb5fa3b19f84d8ab0d0b042bf51a5b8484e8f`。**建议保留候选供复核，暂不集成或花钱为其复测。** 当前性能门和代码规模门均未关闭。

## 实际产品改动

唯一应用改动为 `backend/t44/contracts/__init__.py`。公开 validator 保持每次新建；violations 以 schema 有类型、有插入顺序的结构快照及格式注册项快照，复用最多128项私有实例。非原生 schema 对象/不可哈希格式注册值回退原路径。缓存仅保存校验器，不保存请求数据、校验结果或错误；仍完整执行 iter_errors，再截取100项。请求、提交前 data、HTTP envelope 的三个调用位置均未修改。

jsonschema4.26.0 对现代引用路径使用局部解析状态，referencing0.37.0 Registry/Resolver 的更新返回新对象；没有使用旧可变 RefResolver。此适用性判断来自准确版本源码和本轮交错/线程验证，**不是上游通用线程安全保证**。公开实例的 schema/格式器可变性、schema 后续修改、类级格式新增/替换/移除、SPEC 引用内容修改均有差分检查。官方依据见[Validator源码](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/validators.py)、[FormatChecker源码](https://github.com/python-jsonschema/jsonschema/blob/v4.26.0/jsonschema/_format.py)、[Registry文档](https://referencing.readthedocs.io/en/stable/api/)。

缓存上限是128项，按服务端固定契约规模使用；没有宣称对任意超大 Python schema 的字节上限。服务中没有并发修改全局格式注册表的业务路径；并发注册和未记录的 monkeypatch 全局函数不属于本轮保证范围。私有实例不向业务代码暴露；以后升级依赖须重新验证。

## 实际验证

- 新774用例最终 **163通过、0失败/错误/跳过**。直接加载准确 f7 Git blob 作差分 oracle，未复制一份“优化实现”充当测试。含原870的19样本、全部130组件×9类边界输入、有序多错误/105错误截断、异常/非原生schema、动态schema/SPEC/格式注册、公有实例隔离、12线程760任务与128项上限。额外计数格式器证明每次105项均实际运行，连续两次210次，避免只验证返回前100项。
- 新HTTP实测两次createProject，每次提交前 data 和完整HTTP schema各运行一次；坏data回传被提交前校验拒绝并实际回滚项目插入。原 `tmp/backend/contracts/986_http.py` **123通过、0失败/错误/跳过**。合计286唯一开发用例；首轮162与最终163为重复轮次，不累计为448。
- 61个已有测试目录跟踪文件与f7逐字相同；v1.2清单实际15个冻结文件hash全部保持（不是沿用旧14文件数量）。OpenAPI副本/DDL/错误枚举不变。全部65个应用路径集合保持，唯一代码diff为contracts模块。Ruff0.17.2 check/format通过。
- 复用协调者批准的既有venv，实核jsonschema4.26.0、referencing0.37.0、attrs26.1.0。本地没有安装依赖、运行MySQL/RabbitMQ、真实云负载或独立验收；未完成全CI，归档push意外触发的取消run见末节。Starlette/httpx旧适配路径产生一条上游弃用警告，本轮未更换依赖。

## 有界微基准：收益太小，不能外推云性能

真实SQLite/TestClient生成getTask合法响应，仅fixture准备涉及HTTP且排除计时；随后在同一进程CPU中做ABBA×4、每case每phase100次、各模式8个batch，先各预热10次。下表是**单个校验调用CPU中位数**，不是HTTP延迟或400并发P95。

| 样本 | 原实现 μs | 候选 μs | 中位数减少 |
| --- | ---: | ---: | ---: |
| Plan合法 | 54.220 | 45.710 | 15.69% |
| Id布尔拒绝 | 21.195 | 14.650 | 30.88% |
| TaskCreate合法 | 90.205 | 80.610 | 10.64% |
| 契约验证合法 | 142.955 | 133.140 | 6.87% |
| 105错误数组 | 1535.945 | 1530.140 | 0.38% |
| 实际getTask data | 314.175 | 303.610 | 3.36% |
| 实际getTask完整envelope | 359.150 | 349.880 | 2.58% |

getTask两层相加只省约 **19.835μs，即0.020ms**；未计构建HTTP、数据库、调度、锁、线程和队列。部分batch范围重叠；不是统计显著性结论。首轮微基准与原HTTP回归并行，是一次不够干净的调度选择，原JSON/log保留为contended diagnostic；不以该轮推断收益。之后旧HTTP结束后单独运行本岗ABBA，形成sequential.json。未记录初轮工具的执行时SHA；第二轮产品bytes在原JSON绑定，工具以当前准确候选提交保存，verification.json明确该工具hash不是运行时采集。

这份微收益加上额外代码，不值得单独开启一次付费测试窗口。不能据此声称P7改善、400×600通过、正式根因已定位或任何验收达标。

## 真实规模与整体架构取舍

原固定脚本、同cloc2.10哈希、同65应用路径：5898→**5924**，**净增26有效行**，超5100上限824；候选require-range实际退出1。物理diff净增34行与cloc净增26行是不同指标，不互换。根当前f7若不集成本候选，仍5898、超798。

本岗19模块共2159有效行。API/Business/Call已经共享HTTP适配、组件派发、分页、CAS和输出；api244+application147+common141合计532行。即使荒谬地全删且零替代，也不足798。其余状态机/业务守卫并非可由一个CRUD循环无损替代的重复。现有内部委托、默认值、枚举/映射小改不能提供可信798净减包，不能把迁移/造数从统计中移走解决。

跨模块真正的大范围取舍是一次内部架构v2重写，而非再找十几行：持久层migrations374+seed326共700行，前端1099行，本岗核心2159行，消息/调度也已有共享层。单独去掉整个迁移/造数实现都不足798且违反功能保留，因此不能拿这700当可得预算。下一步若要继续，必须先由相关责任岗提交可执行片段的**准确净减预算和对应守卫/故障/差分证据**，并在本地原门槛通过后再消耗云余额；不应先跑满云窗口等待重写。

截至本轮，**没有已识别、可实现并已验证能闭合798的整体取舍**。采用外部包搬走自研代码、把流程换成排除统计的JSON/SQL、删验证/迁移审计、压行都不在授权范围。无法诚实承诺在剩余短时间完成保全既有语义的大幅重写；根应继续把这一点报告为未达标风险，而不是以通过开发测试代替规模要求。

## 可复核文件与命令

`verification.json` 汇总准确source、hash、JUnit和计数；原件在 `tmp/774_backend_scale_20261029/`：differential*.log/xml、original-http.log/xml、microbenchmark*.json/log、baseline/candidate-source-count.json；candidate-source-count.execution.json记录真实退出1。

所有Python测试/工具命令使用协调者提供的现有venv，并设置PYTHONPATH=backend。实际命令分别为：

```text
python -m pytest -c backend/pyproject.toml tmp/774_backend_scale_20261029/774_contract_reuse.py -q --junitxml=tmp/774_backend_scale_20261029/differential-final.junit.xml
python -m pytest -c backend/pyproject.toml tmp/backend/contracts/986_http.py -q --junitxml=tmp/774_backend_scale_20261029/original-http.junit.xml
python tmp/774_backend_scale_20261029/774_microbenchmark.py --output tmp/774_backend_scale_20261029/microbenchmark-sequential.json
python -m ruff check --config backend/pyproject.toml backend/t44/contracts/__init__.py tmp/774_backend_scale_20261029/*.py
python3 scripts/metrics/source_count.py --cloc <approved-cloc-2.10.pl> --output tmp/774_backend_scale_20261029/candidate-source-count.json --require-range
```

初次用system/rootvenv寻找工具遇到ruff/SQLAlchemy/pytest不存在，未安装；随后使用批准venv。初次baseline计数命令后跟cat，外层shell退出0掩盖其range返回码；报告只引用within_range=false及候选结构化执行的真实退出1。原pytest日志/XML均保存，报告不以外层tail退出值当内层门禁证据。以上均为实际AI过程，未写入学生本人研究正文。

## 归档push意外触发CI（实际纠正）

首次push报告头ad54322e时，我把检查product.yml和push放在同一命令，没有先读返回值再决定，导致所有codex/**匹配自动触发[product40812638415](https://github.com/HJY147/t44-dev-trace/actions/runs/40812638415)。这是本岗的调度错误，已立即通知总协调并仅取消本分支/本头run；没有改动根的云或集成run。CI确实短暂启动：static检查运行，frontend到构建阶段，coverage/contracts在初始化容器阶段收到取消，产品后端完整suite步骤未运行。不能再把本轮说成“完全未触发CI”，也不以取消run作通过证据。

此后的纠正归档提交使用[GitHub官方支持的skip ci标记](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)，只跳过这次文档push；没有改工作流或降低根以后集成准入门槛。取消原件/最终状态保存于tmp/774_backend_scale_20261029/accidental-ci*.json。无ECS或付费云资源操作。

普通取消后static上传清理仍在运行，追加仅本run的force-cancel，API实际202接受；最终状态以accidental-ci-final.json为准。

最终复核40812638415为completed/cancelled，coverage/frontend/contracts/static四job均completed/cancelled，原JSON保存；不是CI PASS。
