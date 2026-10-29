# 请求级数据库诊断：首轮工具与有限实测

操作者：数据库 AI。基线 ade5e4c1998b4c2f014afde8c011645c6c5a7412；先设计 df6fa10，首工具 c11f6305b489ed1e7adade770d0745411d37d5c2，有限样本驱动89af321a2e106ee433a502b36230bbbd9de3c670，最终工具 edc3e2a32a4e657964155d5137c251a0d972d586。没有生产、DDL、API、冻结、池、认证、锁或事务语义修改。

## 已实现的接口

公开模块 tmp/833_database_performance/833_database_trace.py，最终SHA256 **4edbf24779794a826bbe754ccad26890ea4c5c1d3f13f05778bad0e52ec307a9**。

- DatabaseTrace(max_requests=64,max_sql_samples=200).install(engine)，只接受显式MySQL/SQLite engine。
- 后端在实际同步worker的原endpoint内部 with trace.request(operationId,request_id=canonicalUUID)；snapshot()在close前取，caller自行dispose后可再取生命周期计数；close()恢复patch及SQL监听，不替caller.dispose。
- 每请求UTC、perf/monotonic锚点、thread CPU及异常类；分层phase为inclusive，不能加总为互斥份额。Rows/UoW按本次单engine应用假设；Session/SQL钩子显式绑定engine。Result proxy只覆盖当前Rows用法，不是通用Result替身。
- engine acquisition包含排队/新连接/初始化/preping/checkout；DBAPI connect不含其后connect事件中的session初始化；cursor execute可能含PyMySQL buffered取原始结果，不能当纯服务器/锁等待。mapping迭代和from_db_time转换另聚合，不改原Rows方法或排序/异常分类。
- SQL仅verb、registry内表名和statement形状SHA，不保存SQL正文/parameters/自由正文/DSN/token/异常消息。实际pool安全属性和physical connect返回对象的timeout白名单分别记录，不拿源码默认冒运行值。

## 实际执行与边界

在Mac Python3.12.10 / SQLAlchemy2.1.6，既有database/.venv中实际运行。initial-junit.xml和final-junit.xml均为**同6项**全通过，无失败、错误或跳过；时钟改动后重跑，不把它们相加成12独立测试。覆盖导入不加载DB/network/application模块、真实SQLite生产Rows调用、DateTime codec和scalar分层、异常类脱敏/原PersistenceUnavailable、上下文/上限/UUID限制、安装恢复及重复安装拒绝。

有限驱动只用本岗临时SQLite合成表（210行、2个项目、id PK及toy列，不是生产DDL或合法业务fixture），仍调用当前生产Rows和UoW。sqlite-initial.json和sqlite-final.json各保留6个顺序请求：页1/20/100各A/B，每请求两条SQL、全部正确200总数和页序，映射合计242行。每份12个cursor语句；这是实际有限请求/语句，不是HTTP或12个验收用例。fixture/schema操作不在请求记录内，另记outside_request_phases。

首份样本发现thread CPU略高wall约1–2微秒：wall终点后先生成UTC才读CPU，两个区间不等。修正先读CPU终点再读wall/UTC，原sample未改写；最终6样本wall为0.295–1.037ms、CPU均在其内。它是计时语义修正，**不是产品提速A/B**；非原子时钟读和仪表开销仍存在。没有P95/吞吐达标声明，也不能由SQLite快判云数据库不是瓶颈。

两次样本结束均pending0、checkedout0，engine已dispose，自有临时目录清理；observer恢复。无旧云env、未知本地MySQL、HTTP、服务、400客户端或正式性能运行。原19配方/71Rows未读取或重跑。初次读取不存在的tmp/backend/conftest.py失败后，仅参考公开993本岗toy模式；一次apply_patch标记错误被拒且未部分写入。初始Ruff7项I001/SIM117修正、demo一次I001修正后，最终三脚本Ruff绿，未改规则。

## 与后端/root的实际对接

BE确认在APIRoute原同步handle worker内部传operationId和request.state.request_id，fixture/setup不当请求计量；其StageRecorder/cProfile分开解释重叠。已两次通知准确source/hash及时钟边界改动，最终模块接口不变。

root明确本地无Docker、不连现存库，准入后续fresh GitHubActions MySQL service独立t44_diagnostics schema，沿现有锁定镜像/依赖，由root编排：DATABASE_URL所选schema、T44_DATABASE和 python -m t44.cli migrate --database t44_diagnostics 三者一致。后端供自有fixture/有限真实HTTP，本岗observer只接收其engine。下一阶段才有真实MySQL/HTTP数据；本报告不替它预判成功、不代独立验收，也不关闭原云502、0完整600秒组和6316行超限。
