# source935 stage诊断工具实现与本地因果验证

作者/执行者后端AI，根控制云UI与sessionpacket。先e51c8ce设计，再bc428ae最小checkpoint，于13:08UTC发根（首条派工13:00:59，10分钟内）。最终工具C **b76775326095bdc92ddd5883eaa4dc79eaf7d2d1**，产品仍935零修改；仅读本岗代码/公开产品与指定venv库实现，没有读其它岗位日志、任意runtime凭据或独立805/809/814/817/818/829材料，没有新agent/云/旧13306访问。

实现仅tmp/810_latency_diagnosis：透明outer ASGI receive/send与原同步handler包装、原requestID映射、真实线程CPU；原Runtime/request validation/business/precommit/API schema/wire/JSONResponse.render phase；只目标engine SQLAlchemy只读before/after/error及checkout/checkin事件。池连接总时与内部Queue.get分开，真实size/checkedin/checkedout/overflow/peak不伪造。边界和root执行接口见stage-runbook.md。

内部queue接口属于锁定SQLAlchemy当前实现，已在指定venv直接读Queue.get原实现确认Condition.wait；不拿ORDER BY或sleep猜等待。缺接口时明记不可用，未来根source935容器Python3.12还需实查输出，不从Mac SQLite推广MySQL通过。Linux read-only网络工具只输出ss/proc中性聚合/FD数，无地址/FD目标/命令行/env/binds，当前只测parser，不采活动系统。

## 真实失败与修正

- 首代码bc428 /Ruff-format绿，源码15296B/gzip packet6284字符；这是明确未准执行的checkpoint，保留initial packet，不能当当前版。
- 自有7检查首次1红6绿，发现**诊断自身ArithmeticError能盖原Queue.Empty/SQL异常**。只修observer边界为safe观察，正常SQL/原异常不改、诊断标INVALID，另修written为实际成功落盘计数、cap_skips与独占engine清理；同7绿。初检查文件E731(lambda赋值)lint红后仍提交的流程事实保留，随后def窄修，最终不冒首轮全绿。
- 新增真实source935 API+SQLite smoke及net parser后1红8绿：本岗fixture误写getMe路径`/api/v1/me`，baseline与instrumented均404。仅改用冻结OPERATIONS路径，不改产品/断言，9绿。一次patch格式上下文miss未部分修改，再按实际格式修。
- 新增六类无连接admission gate与owner close，共16绿；显式all模式无需改client header后17绿。
- root精确新库命名适配先51663f22设计记录，仅增`t44c_r9diag935_p`一个字面允许项，原diag810前缀保留，所有显式字段仍逐字同、旧P816/near-match/13306拒。允许路径只到达自owned engine桩，不创建连接；当时21 passed，随后增加启动配置隐私目标，最终 **22 passed/0failure/error/skip，0.77s**，不是把7/9/16/17累加。一般Probe metadata只标product_reference，factory过5件指纹另记source_binding，不把stub冒935或完整镜像。

## 最终22目标实际证明及限制

导入不创建app/thread/network；ASGI消息逐字/status/header/body透传；body/worker/send先后、两并发ContextVar与UUID不串及真正worker thread CPU；真实SQLite QueuePool一连接被占，Condition.wait进入事件后才释放held connection（不是sleep未返回推断），Queue.get时长包住受控等待，真实checkedout1；bind marker/token/口令不落日志；SQL原OperationalError类保留、观察器/落盘故障不盖原异常；source935 getMe真实API数据与baseline相同，内部/header/meta requestID同，SQL/schema/render phases真实出现；owned engine单次dispose/恢复原pool方法、invalid target在engine创建之前拒；新精确库名允许/旧近似拒；网络parser保LISTEN队列与TIME_WAIT而不输出合成地址。

这些是owned stub/SQLite/本地TestClient开发验证，不是云MySQL、四业务压力、全量CI或独立验收；没有用stub替代根以后真实serviceP1/dedup escalation。另为隔离明确再以完整最小child env（DATABASE_URL/T44_DATABASE为空、禁plugin自动装载）跑同21绿，防止本地API模块导入消费继承DB配置；源码未变、不是新增21。现有TestClient弃用warning保留。指定`.agent-worktrees/backend/.venv/bin/python`执行所有开发目标；标准库元数据操作不读取外部secret。原红/绿命令/source/log/JUnit保留，无测试放宽。

## 交付

current core17122B/SHA **8f0dbec80e168a8dbac7f3707b467d16c9146fe7937b7c5c2f6825b20bf966f6**；net7356B/SHA **dd776e1fe6c94aa005fa6b00734a6f8cebe54b24a9352917dbea7a771682552b**。`stage-delivery.b7677532.json`10575字符，`stage-install.b7677532.txt`11205字符，均小于18432；gzip逐字往返、每文件SHA/长度均核。旧b3 delivery.final（10379）仅历史候选，current以source命名文件为准。install只写新public脚本，不执行app，根须另给真实新库env/账号/20task与合法serviceP1 packet。

不读取SQL正文/bind/请求body/token/DSN，只保原UUID、operation、status/exception类及中性计时/占用。原HTTP错误/线程/事务/SQL和产品文件不改；附加观测/文件落盘开销非零且可影响后续调度，所以不将采样短窗当正式P95。未来云先核source_binding/每workerfinal/selected-written/INVALID stderr与cap，拒缺口或日志失败数据。

root后续独立source935新诊断campaign才是运行范围，命名适配不授权未来正式F/P。网络/连接/源端口/TIME_WAIT/backlog/连接复用/TLS重建/客户端CPU与writer背压均为待证假设，残差不叫网络根因；未改内核、协议、压力工具，after快照不冒interval。正式400/600/270/零错与原失败保持；无新cloc、产品新增行0，不冒用户亲改或手写研究报告。


启动隐私补充：首次泛化坏URL目标因SQLAlchemy实际抛ArgumentError而非ValueError而红（并未证明泄露）；改成缺@、让合成secret-like字段被当port后，真实异常消息含该marker，窄目标再红。仅在工具factory的配置解析边界从None抛固定脱敏ValueError，产品错误不动，同源全22绿；所有URL均owned假数据，未读取真实凭据。source命名旧f7投递只留历史，current为b7677532版。
