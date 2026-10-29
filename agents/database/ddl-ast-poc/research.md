# MySQL AST隔离POC（已收口，未准入生产替换）

基线189dc4a3196be0fb84b753f23284f2566d823ea0。候选固定SQLGlot30.24.0，纯Pythonwheel只在ignored runtime解包，后端锁/环境/生产模块/DDL/API/freeze均未改；952按显式CLI执行，正常pytest收集不导入候选库/不skip或接触数据库。尚无已实现的生产节省。

官方来源：
- [当前PyPI原元数据](https://pypi.org/pypi/sqlglot/json)与[固定30.24.0发布](https://github.com/tobymao/sqlglot/releases/tag/v30.24.0)：本次核到2026-10-20发布，Python>=3.9；官方wheel SHA保存package-metadata.json并实际核对。
- [API官方FAQ/版本约定](https://sqlglot.com/sqlglot.html#faq)：解析器宽松，不负责SQL有效性验证；未指定源方言会使用跨方言超集，所以POC始终read=mysql。MINOR亦可能破坏兼容，必须精确pin并对升级重做差分。
- [固定版本MIT许可](https://github.com/tobymao/sqlglot/blob/v30.24.0/LICENSE)：商用修改/分发可行，但分发时保留版权/许可。当前未vendor第三方源码或宣称法律审核通过。

输入来自权威schema.sql及旧独立手写parser生成的Core元数据作差分；预期从权威DDL构造，不从实际Inspector/SHOW CREATE反射倒造。所有语句只是解析；无Engine、私密文件、数据库/seed/HTTP调用。原957只用root已公布要点，不读其代码或私有材料。

首轮run1 29通过/2差异：库能解析18 CREATE/2 ALTER与226列，索引/FK/59CHECK及PK差分先通过。失败为本岗adapter把SQLGlot显式NULL的allow_null标志误读；已保留原日志并编辑修复，待root短性能窗口结束才重跑。未知/Command fallback、多语句、别名尾缀等必须显式拒绝，ErrorLevel.RAISE不能替代结构检查。规范化只能消去AST的Paren节点（保留树中布尔分组）、标识符引号/大小写及限定ASCII安全引导符；不得改字符串或丢函数参数、二进制长度标志。

替换范围不能按原migrations321+schema117全数删除：迁移版本/摘要/连接生命周期、真实Inspector适配、索引/FK比较、SQLAlchemy类型/SQLite variant/循环FK元数据组装仍必须存在。当前POC只证明解析/比较，不含完整可替换Core builder；保留旧parser不动用于参照，不能把实验性净删记到生产规模。完成矩阵后再给按函数分解的有界估算及准入建议。

## 最终观察与准入结论

窗口结束后仅恢复子秒级纯解析。run2为36通过/1保留失败，run3补严格根节点/候选AST观察后40/1，run4补unsigned、DATETIME精度、ON UPDATE和表引擎等必要区分后为46/1，均原日志保留，未删失败凑绿。余下唯一失败是旧CHECK parser不能解析SQLGlot生成的13处`NOT x IS NULL`文本；新AST将其与原`x IS NOT NULL`归为同一树，但这不是MySQL执行或形式语义等价证明。不能拿SQLGlot assembler输出直接喂旧checker，生产旧checker未被修改。

18表226列、索引/FK/59CHECK/PK/表选项的静态差分一致；列类型/长度/unsigned/时间精度、NULL/default、同名索引列序/unique/前缀/前后USING/排序、FK源与目标列序/目标库表/删除及更新动作、CHECK恒真/IN扩张/OR恒真、字符串大小写/字符引导符/布尔优先级/函数参数与字节长度区分均保留。严格边界拒绝多语句、尾别名、注释、查询根、非ASCII的_ascii字面量及未知DDL。未使用SQL优化器去“证明”等价，规范化不交换AND/OR，不进行常量折叠。旧CHECK参考13项不兼容是当前阻断；新AST自己的59次roundtrip一致只证明其内部正常形稳定。

差分预期始终来自权威DDL，旧元数据也由独立旧parser从该源构造，完全没有实际数据库反射输入；部分类型别名/候选正常形共享SQLGlot，不能宣称独立执行oracle或一般SQL等价证明。未实现SQLAlchemy Core assembler，未实测新的MySQL反射/连接/CAS/循环FK/SQLite variants，不可进入生产替换。本轮不申请数据库或重负载窗口。

## 同口径真实行数预算

固定cloc2.10（SHA bf5927...）对同文件函数片段的非空非注释物理行计数见line-estimate.json；未改变项目统计政策。

| 范围 | 实测/估算 |
| --- | --- |
| 现生产schema.py / migrations.py | 117 / 321（实测），不是全可删 |
| 四个schema语法/构造函数加旧CHECK函数的最大可替换部分 | 171（实测上界；包含仍需重写的Core builder/type adapter） |
| 952中通用AST提取/规范化五函数 | 114（实测，只是原型，并未进入生产） |
| 尚必需Core assembler / native+SQLite类型适配 / 接入严格性与来源保护 | 35–65 / 20–30 / 5–15（未实现估算） |
| 联合替换的潜在净删 | 171−114−(60～110)=−3～−53，即可能增加3～53行；不是已验证最终实现 |
| CHECK-only小范围 | 旧83、新规范化29实测；另需8–15行导入/可信语法集合/返回None错误边界，潜在净删约39–46，尚未实现/未验证 |

引擎/事务工厂、真实Inspector适配与索引/FK比较、迁移锁/版本/摘要/异常资源释放、Core原生类型/SQLite变体及循环FK组装不能因引入parser消失。952共245应用外实验行包含差分oracle/矩阵/报告；未来若移动通用函数进生产，必须计入应用主口径，不得借tmp或外部库藏业务逻辑。**当前生产节省0**。

建议：不准入整对模块替换，不改backend依赖锁。SQLGlot本身可作候选语法组件，但现有POC未证明必要性和联合净删；CHECK-only约40行机会也需单独设计/准入，不能解决整体840行缺口。若后续另行批准，须先完成独立完整Core assembler、精确pin/hash和许可归档，再由root调度新隔离MySQL8.4库验证真实反射及C-P4拒绝/恢复，不能自改旧checker迁就渲染。成熟库版本升级及新节点/方言行为需重新差分。

本轮初次Ruff F401（遗留探索import）/I001保留，针对952仅整理imports后Ruff通过；矩阵未因风格改动重复运行。源码/DDL/API/freeze/依赖锁/975均未改，不接触独立私有材料；本报告不是产品/独立/性能或代码规模通过结论。
