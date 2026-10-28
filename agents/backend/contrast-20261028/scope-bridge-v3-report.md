# Scope桥v3：修复预算审核阻断

后端AI，ROLE-backend-SCOPE-BRIDGE-V3-BUDGET，2026-10-28。根派发审核39a20035指出原161b82ee工具两项阻断：GEN三种scheduler命令缺预算回执参数；直接SQL只取共享锁、没有锁内实际budget.admit。属于工具与新v4契约衔接缺口，不是产品假绿，也不能由原56自测覆盖。原v2/manifest/56证据、旧会话失败保持；本次另新目录，不云试、不读独立私件、不改产品。

设计e95a744c先固定输入输出：root必须提供实际probe-budget产生的PUBLIC回执原字节/SHA。LOAD配置新增originals.mysql_budget本地PUBLIC副本path+SHA，budget_receipt_path另钉APP实际phase/receipts/mysql-budget-32hex.PUBLIC.json。authority完整带文档与APP路径；LOAD核kind/source/binding/stop/namespace/路径关系，APP再核实际原路径同一SHA。没有默认384或虚构probe。

修复前e5b775f7在原v2字节上实际得到5红：scheduler-token/rotate/start各缺两flag（3），preflight/seal锁内未admit（2）。原JUnit无损gzip保存，原回归断言不删。5cedb2ca修复：三命令每次透传同一--budget-receipt及--budget-receipt-sha256；父桥不持GEN锁，GEN自行重验。直接SQL每步在原operation_lock内先调用未改的305f helper admit，再派发SQL容器；每步保存有限PUBLIC准入回执。

admit使用实际owned MySQL metadata（唯一CID、image、PID/startticks、StartedAt、restart、DB/namespace）和原只读numeric query，再核同serverUUID/实际max/完整角色预算。原query_once/measure/admit/SQL/解析均保留，适配器仅将subprocess.run timeout限制为桥剩余lease，元数据探针也受原deadline；不修改MySQL配置或放宽120秒。库/UUID/CID/重启/容量/回执变化都先于业务SQL拒绝，异常释放锁且无自动重试。

最终74 passed，0failures/errors/skips；为原56加18新预算检查。新测试使用原305f admit/measure/numeric parser和本机flock，Docker metadata及只读query transport为自有合成值，没有真实MySQL或网络。有效合成例当前max128、F4预算124能准入，当前123会拒绝，证实没有借默认384；不是云测性能结果。新增query剩余3秒timeout传参检查、错误PUBLIC receipt/path/source/binding/namespace拒绝、GEN精确透传和锁内次序。原56用例为新契约只补PUBLIC fixture和旧锁专测的中性admit stub，三个文件95条assert的AST顺序逐条一致，删除0；原5红用例的assert AST也一致。crypto c89和phase helper305f逐字不变。

最终manifest `e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7`；工具目录tmp/790_backend_contrast_20261028/scope-callback-bridge-v3-budget，九runtime模块、四安装片，新两机目录/root/t44-r9/scope-bridge-v3-01。四完整命令12216/12953/15289/12840B，各加300说明仍<18000；配置空模板、三阶段execute模板、dependencies/verification、final74-local.xml和budget-red.xml.gz齐备。参考scope-bridge-v3-runbook.md，null/占位符不能运行。

依赖部署最终25d863c5的v4/STEPS与21599B/SHA305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d helper，GEN派生器负责安装，桥仍按binding及manifest双pin。保持fixed phase state、120秒/lease/snapshot、原nonce/key/wire、无token/K argv/env/stdout、GEN前释放父锁和one_serial_operation15连接预留。

限定Ruff/diff检查通过；host3.10仅AST/标准库接口，本机Python3.12/Mac运行。未由本岗运行云、实际Linux/MySQL、SUT、CI或独立验收；没有产品规模节省或性能结论。新commit/manifest已交审核岗，阻断是否关闭由复审决定。研究报告仅提供这份AI过程素材，不记为学生本人撰写经历。
