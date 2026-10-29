# A 默认投影 / B 连接池配置：分别限定审核

## scope_baseline

AI reviewer；ROLE-reviewer-SELECT-POOL-20261028-v1。A产品 `82e92dfc420690980a6e16c88f209d08ab709e49`、完整检查点 `ac7664f9bea12362bc1d1466a386659a3c9d0c5a`；B产品 `92cf5c108ee549b35dda6d775e0357ded9e40743`，读取时完整材料检查点 `c4900aa87c4a5f9364e030a3d7a193372c766897`。共同产品基线 `a12e9e70b963bacafda3242bb6d82e53ee912ff1`；root派工基线 `7947c247` 的 backend tree 与a12均为 `4e8e917b070a167aec765360b0f8d02f161b9c1c`。

只评两个独立产品候选及相应开发测试/公开证据。未读独立tmp792/private、未发布cases或研究正文；未联系开发/测试岗。没有云、服务器、真实MySQL、HTTP、完整测试或黑盒验收执行。B两行settings范围已由总协调明确转述backend授权，本岗不改产品/测试。只写本报告和本岗四件。

## requirements_mapping

| 候选 | 实际产品差异 | 冻结边界 |
| --- | --- | --- |
| A | RowsGateway.rows默认fields由tuple(t.c)改成(t,) | 显式columns、白名单、参数、谓词、排序分页、锁、_execute/codec/UoW均未改 |
| B | mysql_settings新增int(os.getenv(T44_DB_POOL_SIZE,"5"))和int(os.getenv(T44_DB_MAX_OVERFLOW,"10")) | 默认5/10；MySQLSettings/engine、URL来源、TTL、DB guard、业务/API均未改；不捆A |

A产品与final的rows.py blob相同 `4bc873f80c28cf1f9af8ecb4f3e74b9a4d9ba825`；B settings blob `58a1d93ce7c25c533aed52a365d3c2e83a92cb4b`。A产品/测试路径与B产品/测试路径无交叉；整合两个源提交不要求相互修改接口或依赖。

## change_scope

A不是通配符SQL：当前SQLAlchemy Core会从可信Table展开列；不引入ORM实体、动态SQL或跨表join。当前冻结18表226列均无omit-from-statements标记，因此本次等价结论限定这些元数据和锁定运行时。未来若改元数据/SQLAlchemy版本仍需重新核展开/返回形状。

B只引入两个明确ENV配置入口，每次mysql_settings转换时读取，不提前在Settings.from_env读取或快照这两个值。显式无效整数拒绝，不静默回落默认。没有改变池等待、recycle、session init、UTC、严格SQL、READ COMMITTED、pre_ping/LIFO/reset/hide_parameters或DB连接生命周期。B不是性能修复证明，也不代表新的非默认池配置已经获实际资源准入。

## compatibility

A实际纯编译对照在SQLAlchemy **2.1.6**、18表×4变体×MySQL/SQLite共144对，旧新SQL文本、params、位置参数、selected column顺序/对象与结果列类型元数据均相同，覆盖默认/显式重复投影、绑定、分页、share/update/skip_locked。内存SQLite users/auth_sessions真实执行旧新gateway，平铺dict键序、UTC微秒、binary、JSON、NULL相同；不是MySQL锁或事务并发证明。执行、异常脱敏、UoW提交/回滚实现逐字未变，不从编译相等推导整体性能达标。

B无ENV时所有MySQLSettings字段与旧版完全相同；单独/同时覆盖只改变容量。size必须>0，overflow必须>=0，-1无限overflow仍被原类拒绝。int接受空白/正号形式，拒空串、浮点/非整数文本；无新增全局上界。URL driver/缺显式库、T44_DATABASE mismatch仍先于新int解析；成功转换后的identifier/credential/port等仍由原MySQLSettings校验，不声称多项无效配置之间新增了全部固定错误顺序。API LazyFactory仍把配置异常转换为通用PersistenceUnavailable，CLI仍只输出COMMAND_FAILED。

这两个ENV作用于所有经过Settings.mysql_settings构造的角色engine，不能只算API。非默认实验必须统计API/consumer/scheduler/admin等全部进程、池保留+overflow、实际max_connections与余量；本轮未查询真实预算。5/10或20/0能解析、进入lazy QueuePool不等于实际连接容量或性能已证明。

## correctness

分别未发现A或B的新代码阻断项。A原SQL/lock/rows layout在当前冻结条件下等价；白名单和绑定规则在原位置，不增加SQL注入或原始标识输入通道。B在配置转换时fail-fast、保留默认和原owner验证，不改变业务错误/审计/权限/幂等顺序。配置ENV动态读取是明确新增行为，已有Settings实例再次调用mysql_settings会读当时配置；没有自动热重建已创建池的实现。

组合无生产或新增测试路径冲突：A只改rows.py及tmp/787…，B只改settings.py及tmp/786…，类/依赖/API不互改。完整分支行政材料若同时改database日志/交接应合并保留各自事实，不能把产品路径无冲突泛化为所有历史材料无需处理。

## evidence

本岗一次内联纯目标脚本，指定既有Python binary、PYTHONDONTWRITEBYTECODE=1、PYTHONPATH=backend，首次exit0。动态加载Git精确A/a12 rows和B/a12 settings；没有修改产品。仅编译、独占SQLite内存映射及配置/lazy-engine检查，PyMySQL connect被禁止且实际调用0；无外部数据库。运行环境其余backend与a12相同。

本岗真实输出摘要（不是owner成绩）：

```json
{"SQLAlchemy_runtime":"2.1.6","A_tables":18,"A_column_count":226,"A_compiled_old_new_pairs":144,"A_equal_SQL_params_lock_projection_result_metadata":true,"A_local_memory_mapping_tables":["users","auth_sessions"],"A_UTC_binary_JSON_NULL_flat_mapping_equal":true,"B_config_checks":14,"B_defaults":"5/10 unchanged","B_URL_and_declared_database_priority_equal":true,"B_lazy_engine_capacities":[[5,10],[20,0]],"B_actual_MySQL_connect_calls":0,"A_B_product_paths_disjoint":true}
```

另只读复算owner原始JUnit和其verification摘要：A final30/0失败/0错/0skip、原持久138/0/0/0；A额外mapping1与30重叠，不相加。B旧5含4红1绿，修后38=31新配置+7原回归，0红错skip；这些是开发本地证据，本岗未重跑套件。A的17 integration deselected、MySQL/HTTP/云/fullCI/正式性能未跑边界保留。两个源提交产品+测试scoped `git diff --check`均0。

B整个材料包的raw diff-check **exit2仍保留**：旧红log/XML中8处原pytest尾空格，不把本次限定源码守卫0写成全包check绿，不去掉原失败内容。首次读取B测试曾猜错tmp/786路径，git show exit128；随后用提交name-only定位实际 `tmp/786_database_pool_20261028/786_pool_settings.py`，不将该读文件错误当产品测试失败。未读取指定解释器相邻env/log/DB。

## findings

| 十项核对 | A | B |
| --- | --- | --- |
| 1 身份/准确版本 | 通过，独立评其他岗 | 通过，独立评其他岗 |
| 2 需求/范围 | 一表达式、无断言降低 | 两ENV行、授权范围明确 |
| 3 外部接口 | 当前返回布局等价 | 默认不变，显式ENV新行为 |
| 4 数据库兼容 | 编译/内存限定通过，native未跑 | 连接参数限定通过，native未跑 |
| 5 状态机 | 实现未改 | 实现未改 |
| 6 权限/SQL边界 | 原白名单/绑定保留 | 原DB/配置验证及错误脱敏保留 |
| 7 锁/事务/资源 | SQL锁子句等价，真实并发未验证 | pool配置到达，真实总预算未验证 |
| 8 幂等/故障 | 原实现未改 | 原实现未改，无自动重建/重试 |
| 9 证据真实性 | owner与本岗执行分开 | 旧红/尾空格失败与局部绿分开 |
| 10 完整门禁 | 未验证；LOC未过 | 未验证；LOC未过；全包diff-check2保留 |

A有效LOC净0；B净+2，5935/超5100上限835仍不达标，不是规模优化。400协议、功能/安全门禁、完整资源尾部与正式性能条件不降低。

## conclusion

**A：CONDITIONAL_INTEGRATION_CANDIDATE；B：CONDITIONAL_INTEGRATION_CANDIDATE。** 没有新窄范围代码阻断，组合未见生产/测试或接口依赖冲突，可交root整合到待验证分支；不是主干/发布/验收通过。必须绑定准确组合新SHA执行完整CI、真实原生MySQL及相关新配置/查询回归；不能把38局部绿、SQL编译相等或惰性池容量推导整体通过。

总协调随后回传已仅整合A/B，当前 `fee30ae5` 应用差异仍为rows一表达式/settings两行，未云、未宣通过，并将两新增测试接入CI后跑完整714+新增及原生MySQL。本岗按root回传记录该新状态，不把它冒成本岗已执行CI/native。没有再扩大探针；本报告及本岗四件封存后释放槽。
