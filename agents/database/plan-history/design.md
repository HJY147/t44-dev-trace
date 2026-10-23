# Issue28：数据库固定任务排期历史批读契约

数据库岗 AI；实际派工 `ROLE-database-PLAN-HISTORY-v1`，基点 `02c4b2a59cdcc3b3dc6bc7981735f4c1b74f181a`。依据根准入记录与已集成 RFC；本文件先提交设计，随后按既有准入实施，不代表独立验收或全局通过。

## 真实源码复核

- `schema.sql` 的 schedule_changes 为12列，既有 `uq_schedule_task_version(task_id,to_version)` 保证每个精确pair最多一行；project复合外键与target CHECK约束仍保留，版本范围1..2147483647。
- `RowsGateway._execute(..., "rows")` 已经使用完整映射，JSON由SQLAlchemy类型解码，DATETIME经现codec转换为UTC aware datetime；复用该路径，不额外JSON字符串化/裁剪。
- 现RowsGateway通用where无法表达成对关联，增加固定入口，不改变rows/get/count的任何语义。SQL驱动异常沿现脱敏 PersistenceUnavailable/IntegrityError及rollback-only机制。

## 给后端的精确接口

`RowsGateway.task_schedule_changes(project_id: int, pairs: tuple[tuple[int, int], ...]) -> list[dict]`

1. project_id和task_id必须为type(value) is int且1..4294967295；to_version必须为type(value) is int且1..2147483647。bool、字符串、浮点、None、越界一律StatementRejected。pairs及每项必须为tuple，每项长度2；输入最多100项，在去重前检查上限。无效输入不执行SQL。
2. 校验project后，空tuple立即返回[]，不获取session/不execute；重复pair按值去重。合法Version=1可以输入，虽然现正常schedule行to_version至少2，查询自然无结果。
3. 固定select(schedule_changes) AND project_id=:project AND iteration_id IS NULL AND tuple_(task_id,to_version).in_(pairs)，所有值绑定，稳定ORDER BY task_id,to_version,id。无LIMIT、不做task IN × version IN、不接收表名/动态排序/锁/原SQL。
4. 非空只调用一次_execute并返回其完整解码row list，不新开连接/事务，不锁行、不提交，不改变调用方UoW。distinct pair数为唯一键支持的硬bound，0..100行；不扫描全项目历史、不cache。
5. 返回值必须为完整列字典；id/project_id/task_id/to_version必须是合法原范围int，project与pair必须属于本次输入且iteration_id为空；同pair或同id重复、超过distinct pair数、范围/结构违约均调用_failed并抛脱敏PersistenceUnavailable，不返回截断结果。before_plan/after_plan/evidence/reason的保守业务匹配由后端拥有，数据库门面不猜测其含义。
6. SQL异常保留现异常分类；故障不能降为[]。后端在授权audit当前页内提取pair，原GET UoW退出后沿现Runtime拒绝审计，不由数据库新增HTTP错误码。

## 实施与验证范围

仅改本岗rows.py及README、现有993_foundation.py/988_mysql.py和本岗记录。DDL、14冻结文件、原audit、后端matcher/UI、依赖/通用rows与原测试断言不改。不新增编号脚本、不读取任何独立私密材料或联系tester。

先在旧源增加入口目标断言并实跑红，再加实现。SQLite真实精确pair/交叉干扰/跨项目/完整codec/排序；空0execute、有1execute、去重与100/101边界；严格类型/上下界；模拟异常与返回违约rollback-only。真MySQL只运行新增目标用例，使用现988受保护t44_test连接与自有随机名合成fixture，不清表、不改别人数据、不停数据库、不重跑整套/负载。行读前后原值核对，事务回滚自有新增fixture。

代码预算修正：安全结果检查使生产净增预计35..50 cloc，而RFC原估18..30偏低；实现后按固定脚本实测，不能压行。基线02c4b2a同原口径实测应用6124行（baseline-cloc.json），已超5100，非口头6108；设计阶段产品净增0。最终精确源码审核/组合CI由root调度，本岗自测不代其结论。
