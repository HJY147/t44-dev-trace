# c4e8 离线数据库诊断工具限定审核：输出排他不通过

## 1. 对象与基线

固定AI审核岗；实际prompt ROLE-reviewer-DATABASE-PUBLIC-C-v1。精确阶段候选 **c4e8c696411975ee6964ef3b2254c8f3937ecb32**，base **6d02cf1d3b99b15556c5d74e007cb4d8d546bbf9**，工具实施 **d75866f0d4077dd0399672f6dc914a82de6b9399**，先行设计80e9d67/cacd0af。工具SHA256 **ac30e655d584caeb6f34251e736025577506fc3026ff0b979edbe3abdbbfbaa3**。独立review worktree从c4e8建立；先scope提交970608e，再读工具与明确公开开发证据。

仅本诊断工具/开发E范围；不套用后端5cc审核，不读独立tmp839/841/852、私有case/driver/原始资源或凭据，不联系独立岗。

## 2. 需求映射

838只应在显式--run后，对本地合成内存SQLite执行有限Rows配方；不提供MySQL/HTTP/服务入口，不改应用/DDL/锁/池或声称性能收益。输出不得覆盖已有结果，导入不得触发配方或连接。设计先行，报告对toy schema、SQLite锁缺失、顺序版本谓词、未应用配方及未完成正式组均有明确限制。

## 3. 差量与责任

相对C **0dfb55c2191200d947c5423fd9ee74bb0812cc5a**，backend/t44、frontend/src及specs/database/contracts差异为空。新增可执行工具只在tmp/838_database_public_diagnostics/；其余为DB岗设计、报告和E。审核岗未修改工具、生产或开发矩阵，只写自己的报告/日志/反例原件。

## 4. 导入、输入与存储边界

模块顶层只有stdlib imports、常量和函数定义，main只在__main__调用；SQLAlchemy/t44 imports及create_engine都在recipes内。CLI只接--run/--output，无DSN/目标URL/账号参数；没有Settings.from_env或私有env读取。唯一engine URL为sqlite+pysqlite:///:memory:，只复制tasks/task_dependencies/project_members的列类型构建三张toy表，只保留id PK，未装生产FK/CHECK/其它唯一和非空约束。删除缺引用仅发生在该内存toy库；Session退出/engine.dispose finally保留。

13份指定C源在运行前逐字比较Git C并记录SHA/AST函数坐标；本岗逐一核对。它不是整个Python环境或所有依赖版本的完整证明，实际执行环境仍按报告的工作目录/PYTHONPATH；没有把MySQL方言编译冒称连接过MySQL。

## 5. 已证实P2 OUTPUT-EXCLUSIVE-01

位置：**tmp/838_database_public_diagnostics/838_database_public_diagnostics.py:263–264、293–294**。预检使用Path.exists()，最终finally却用Path.write_text普通w打开，缺少O_EXCL和NOFOLLOW。输出在检查后、写入前被另一执行者合法创建时，当前执行会直接截断覆盖它；悬空symlink也不会被exists识别为已有路径。该行为违反同函数声明的“Output must not exist; retain previous results”。

唯一实际微探针：加载精确工具、调用真实main；仅将recipes换成零DB函数，在预检结束后创建一个已有结果标记，确定性模拟第二写入者进入该时间窗。真实main正常打印completed，却覆盖标记；original_result_overwritten=true，DB/application新导入模块=[]。这是文件输出边界的受控反例，不是SQLite矩阵或业务流程运行。实际命令与结果位于agents/reviewer/evidence/database-public-c/output-probe-command.txt和output-exclusive-counterexample.json；临时文件仅在本岗目录内创建，探针结束自动删除，没有读取或改动原E。

责任DB岗：先设计修正，再排他取得目标fd并仅通过该fd写出，防止预检后重新以w打开；保留原输出及失败结果，处理链接/并发冲突，不能只再加一次exists。修复后只需同文件生命周期语义的窄回归，不能降低断言或重刷71条矩阵充数。审核岗未代修。

## 6. 公开证据与计数核验

本岗逐项核evidence-seal列出的13份文件SHA、工具提交/实际bytes及13份C源的SHA/AST位置。公开offline-run1.json确为工具d75866f、固定C：19个计数配方，71次Rows._execute＝69 SELECT＋2 UPDATE。19个measurement覆盖62次执行，索引59–65另属缺引用路径7次，69–70为顺序版本谓词2次；不是漏算或71个测试。

deps度0/4/32二读及skip-empty输出、成员3/32物化、依赖页1/4/32的1+P与batch2、listTasks20+COUNT、task lock形状及rowcount1/0原件一致。每个Rows记录仅含mysql_compiled_shape/mode/materialized_rows，不存参数；result_signature只有自有toy ID/状态/页计数。LOCK IN SHARE MODE/FOR UPDATE只证明MySQL方言编译，SQLite不证明行锁/RC；缺引用两次TypeError不冒充真实HTTP错误映射，顺序更新不是并发CAS。全部这些均为DB岗原执行，本岗没有重跑矩阵。

导入/缺--run/预先存在结果的开发guard原件存在；它们没有覆盖检查后的并发创建，因此不能消除此P2。首次Ruff I001/B023失败与之后成功原件均保留。原19/71结果不因本次输出反例被篡改、删除或改称失败。

## 7. 十项检查

| 项 | 判定 | 依据/边界 |
|---|---|---|
| 1 身份/版本 | 通过 | 精确c4e8/d758/source C及先行设计；固定AI审核 |
| 2 范围 | 通过 | 新独立scope；唯一tmp工具，无生产差量 |
| 3 接口兼容 | 不适用 | 不改业务API/错误/契约 |
| 4 DB兼容 | 通过（离线范围） | 只有三张临时内存toy表，无真实MySQL或DDL迁移 |
| 5 配方含义 | 通过（限定） | 源Rows真实执行/编译路径及19/71原件；不是生产动作运行 |
| 6 凭据/权限 | 通过（静态限定） | 无私有env/DSN/URL输入或参数日志；输出只合成公开值 |
| 7 并发/输出排他 | **不通过，P2** | exists→write_text时间窗覆盖已出现结果；真实main微探针确认 |
| 8 故障留痕 | 不通过（同P2） | 预先存在文件guard有测，检查后竞争未防；原矩阵失败证据保持 |
| 9 证据真实性 | 通过（限定） | 13manifest及13源逐项核、19/71计数核；本岗不称自己运行矩阵 |
| 10 整合准入 | **不通过** | 诊断工具须先修P2；无MySQL/HTTP/性能或全局门禁判定 |

## 8. 结论与复审

**当前c4e8诊断工具整合不通过，阻断为OUTPUT-EXCLUSIVE-01。** 其E可作为明确限定的历史开发证据保留，不能凭19/71或导入guard绿色宣布工具已可安全重跑。DB岗新设计/最小修复后绑定新SHA复审输出fd/链接/竞争边界，不需要重跑原矩阵来验证这一文件生命周期修复。

本岗实际仅静态/hash/计数检查＋一次零DB输出微探针；应用/矩阵/SQL/HTTP/MySQL/服务/负载/CI均0，无独立私密读取或通信。该结论不涉及BE ead的新CI数字，不归因公开502/P95，不发APPROVE、main/global gate或性能通过。
