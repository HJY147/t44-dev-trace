Agent-Role: database (AI owner; not student manual edit)
Prompt-Ref: ROLE-database-PLAN-HISTORY-v1

已从指定02c4b2a基线完成设计复核和固定门面实现，设计提交e9a769a，产品精确提交[3b7bc0c92f92a20bc69ee76293f547fe9f1e9a9a](https://github.com/HJY147/t44-dev-trace/commit/3b7bc0c92f92a20bc69ee76293f547fe9f1e9a9a)，分支codex/database-plan-history；使用skip ci，完整CI由root统一调度。

下游契约：RowsGateway.task_schedule_changes(project_id:int,pairs:tuple[tuple[int,int],...])->完整codec解码list[dict]；输入最多100项（去重前），严格int，ID1..4294967295、Version1..2147483647，拒bool/字符串等StatementRejected。固定schedule_changes+project_id+iteration_id IS NULL+精确tuple-IN，按task_id/to_version/id排序；空0execute、有1execute、无LIMIT/跨乘积/N+1/新连接或提交。完整列/范围/项目pair/iteration/重复pair或id/硬bound违约显式PersistenceUnavailable并rollback-only。业务理由与快照匹配归后端，数据库故障不能当作缺理由成功。

开发自测：旧源目标真实AttributeError红；新增SQLite/mock专项48通过，原993整文件66通过（包含同48）；真MySQL新增读取1与实际服务器报错1均通过，最后为新增实际SQL账本重跑同两目标2通过。以上重叠/重复，不相加为独立案例。首环境缺pytest、首MySQL自有fixture漏project_members的FK失败、首次I001均保留，只修环境选择/自有夹具/import，没有弱化原断言或为夹具改产品。

真MySQL只在明确t44_test创建自有随机名有限fixture：100精确pairs一次返回100完整行，排除2交叉干扰/另项目/iteration，覆盖空0/101拒绝0/重复1/合法上界、2000字符/完整JSON/UTC微秒、读前后不变。104条history及关联数据同UoW最终rollback，随后自有用户不存在；不清共享表、不操作别人的数据或停库。真实SQL与整数绑定/次数见agents/database/plan-history/mysql-sql-ledger.json；实际服务器错误仅测试进程registry替换指向不存在自有表名，未建删表。

14冻结文件摘要与基线字节全部相同；16旧RowsGateway方法及两自测文件全部旧函数源码字节相同，证据unchanged-boundaries.json。限定Ruff通过、rows定向Bandit0。完整接口、原失败与log/JUnit/summary在agents/database/plan-history/。

预算真实上修保留：RFC净+18..30→本岗设计+35..50→最终rows cloc237→299/净+62。原固定source_count.py/cloc2.10实测基线6124→该产品提交6186，--require-range退出1，源码规模仍失败；不压行/改计数。最终提交计数将随证据提交归档。

当前仅数据库owner实现和自测，不代表后端matcher/GET投影/前端UI/Issue28整体完成，不是独立复测/HTTP/性能或全局通过。root还须先做精确DB源码小审，再调度后端接入和组合CI；main仍保护，不设置review成功状态。
