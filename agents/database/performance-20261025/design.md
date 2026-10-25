# 请求级数据库诊断设计

数据库 AI，基线 ade5e4c1998b4c2f014afde8c011645c6c5a7412。只读取明确公开的839联合报告、本岗公开路径报告及当前整合checkpoint，不读独立用例、原始请求或私有env。

## 输入输出和范围

新增诊断模块 `tmp/833_database_performance/833_database_trace.py`，只在显式诊断进程安装，无生产文件修改或导入时连接。接口与后端实对齐：`DatabaseTrace(max_requests=64).install(engine)`；在实际同步 endpoint worker 内 `with trace.request(operationId, request_id=UUID)`；`snapshot()`；请求完成及caller自行dispose后 `close()` 恢复补丁/监听。trace不加载URL/env/凭据、不创建schema或自动dispose调用方engine。

每条记录有固定operationId、受限UUID、UTC及perf/monotonic锚点、end UTC、wall/thread CPU、异常类（无消息）。每个phase的聚合为count/wall_ns/thread_cpu_ns/error_count；计时为inclusive，不能加总成互斥CPU份额。请求/SQL样本数量有界并显式记录丢弃样本数。

## 层次

- engine.connect：acquisition inclusive，含排队、新建、session初始化、pre_ping、checkout等，不称纯pool等待。
- dialect connect/do_ping/do_close/do_commit/do_rollback：真实DBAPI生命周期 inclusive，初始化仍属于connect/acquire边界，不删原调用；只记异常类及ping false。
- Session execute/commit/rollback/close及UoW enter/exit：原函数透明包装，只对绑定目标engine的session/UoW归属当前请求。
- cursor execute：SQLAlchemy before/after/handle_error事件，保留状态和耗时。PyMySQL buffered execute可已包含从网络取原始结果，不能称纯服务器执行或锁等待。
- Result mappings迭代：围绕真实iterator.next计时，另聚合from_db_time转换；不偷换生产Rows方法、结果顺序、异常分类或SQL。
- Rows._execute inclusive：保留现有实现的上下文和错误处理，外部计时；和上述子层有重叠。

SQL只输出verb、冻结registry内table名字及原参数化statement形状SHA，不保存SQL正文、parameters、自由正文、URL、token、异常message。install时记录实际dialect/driver/池对象安全属性；物理连接建立后只读timeout白名单，不能把源码默认值当运行值。未知/不可见指标为null，不拼造纯锁等待。

## 实施与验证

先提交本设计再实现。先用自有临时SQLite/生产Rows做有限实测，明确这不是MySQL、真实HTTP或云根因。合成自测覆盖安装恢复、Result透明消费、异常/上下文、SQL信息脱敏与上限；不复跑旧19配方/71 Rows。

root已明确本机无Docker且不准连接现存/未知本地库；后续真实MySQL诊断仅由root编排fresh GitHubActions service内的固定 `t44_diagnostics`，依现有锁定镜像/依赖和已冻结迁移；独立新service才允许DDL/自有fixture/SQL。后端创建app/fixture和有限真实HTTP输入，本模块仅接收engine，在同次worker请求内计时。该诊断最多10分钟，不是400×600正式性能复测，不启动收费资源。

安装补丁会增加时间和CPU开销，不能把仪表绝对数当无仪表正式成绩。可以帮助区分主要inclusive成本，精确根因仍须实际来源及对照。未知异常与原始失败都保存；诊断输出由caller使用排他0600方式保留，不静默覆写旧结果。
