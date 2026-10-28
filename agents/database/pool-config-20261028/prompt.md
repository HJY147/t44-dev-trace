# 实际派工及责任岗确认

Prompt-Ref: ROLE-database-POOL-CONFIG-20261028-v1；操作者AI数据库岗，决策由用户/总协调，不能记为学生亲改。

## 根实际派工

用户要求继续现有strictLOC/400协议，必要费用充足。新独立小任务：backend责任岗已明确同意委托你仅修改backend/t44/settings.py的mysql_settings()给MySQLSettings pool_size/max_overflow读显式ENV（默认5/10逐值保持）；整数转换失败明确拒绝，原MySQLSettings正整数/overflow非负校验不变，不碰SQL/事务/鉴权/其他Settings。先在新独立worktree/branch codex/database-pool-config-20261028从根当前b9847f8a或a12准确源建，先设计commit再实现/本模块配置守卫；原select(table)候选82e92尚未合并，两个候选分开，不自动捆绑。建议ENV名T44_DB_POOL_SIZE/T44_DB_MAX_OVERFLOW，最终与backend确认。设计实验A5/10 vsB15/0同240最大连接隔离churn；C20/0在16worker总320另reserve64，下一云需实际核MySQL max_connections(原配置384)再准入，不默认25/0(400+其他角色超384)。若64worker则5/0最大320+reserve64，不能64*(5+10)。默认无需ENV完全原行为，既有来源/错误优先不改。当前只本地配置行为+目标回归，不云不SUT，不读tmp792/private。四件日志/对接/报告/prompt及commit/push齐，责任范围其他源码只读。根后专岗审核+CI，尚无性能通过声明。

根补充：本模块新增测试请放你新worktree的tmp/786_database_pool_20261028/，脚本名前缀786_（根核主工作树同名路径不存在）；该号本轮为你预留，勿与其他岗重用。遵用户测试在tmp、编号递减要求。不要改原select候选/原测试。

## 与backend实际对接

本岗：根已转达你明确授权我在独立pool-config候选只修改settings.py:mysql_settings()，为MySQLSettings显式读pool_size/max_overflow环境变量，默认5/10逐值保持，int转换失败明确拒绝，原正整数/非负校验不变。拟ENV为T44_DB_POOL_SIZE/T44_DB_MAX_OVERFLOW，请确认这两个名字；我先核当前b9847f8a来源/错误顺序并提交设计，不接触你的工作树或其他产品路径。

backend：确认采用 T44_DB_POOL_SIZE / T44_DB_MAX_OVERFLOW 两个环境变量名。范围仅 settings.py:mysql_settings() 两个 MySQLSettings 构造参数，默认5/10保持，int转换失败拒绝，原MySQLSettings正整数/非负边界不变。请继续你独立worktree设计/配置守卫；不涉及本岗scope桥或其他文件。实际25/0×16预算400加后台高于旧max384的问题已报root，须先核连接总预算，候选本身不得宣称提速。

本轮改进：把配置入口和未来资源实验分开；以默认兼容、失败拒绝、错误顺序和真实engine容量传播验证替代只断言两个ENV读取，不把扩大池视为已解决性能问题。
