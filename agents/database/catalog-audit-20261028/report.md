# 原生目录审计修复：本地开发验证完成，待根审核/整合

AI数据库岗；基线22f666e2，应用基线f4bd382d。先行设计cacd03b1，原生配方108a9657，首修7c94fc6d，最终生产源 **26d6328ab882b06eb9f6026a29656999e122f57d**。

原SQLAlchemy反射遗漏的性质已由四条完整字面、schema级只读INFORMATION_SCHEMA查询补审计。生产只改migrations.py；DDL/API/冻结/依赖/Rows及业务事务不变。check_schema输入/返回形状不变，migrate沿用原锁、目标库、版本、checksum、partial-state和SQL错误处理。

## 真实问题、修复和兼容性

全新socket-only官方MySQL8.4.11 macos15-arm64上，原实现的31配方仅24项符合要求。漏判七项：必需索引DESC、移除id AUTO_INCREMENT、改MyISAM、改表默认collation、改字符列collation、CHECK NOT ENFORCED，以及新补的必需索引INVISIBLE。每项在原实现均check passed、重复migrate也接受；不是只在假的Inspector里推理。

新增核验从已验原始DDL生成的可信TABLES获取期望：表引擎/默认collation；各列EXTRA及字符集/collation；必需主键/唯一/普通索引逐列位置、名称、唯一性、升降序、前缀长度、类型、可见性；原CHECK执行性。CHECK目录明确限制CONSTRAINT_TYPE='CHECK'，不与其他约束名字混淆。没有比较表自增计数、SHOW原字符串或由目标库倒生成标准。

最终26d6328a上 **31/31** 原生配方符合要求：8个等价正例、23个意义漂移负例；所有例均核check与重复migrate的相同接受/拒绝结论，未发生DDL设置错误。原ASC/BTREE、增长计数、括号、合法_utf8mb4/_ascii、当前库限定及NO ACTION/RESTRICT仍接受；原索引/唯一性/外键/CHECK/列类型/默认/空值漂移仍拒绝。额外非唯一辅助索引继续被允许。原有表达式和外键normalizer保留，不借补审计改变兼容定义。

所有配方使用独立新空schema，变异后的schema保留，不删除失败设置或用数据修复覆盖证据。这与最初设计的逐项变异/恢复稍有不同：采用“每例新schema”提供下一例干净前提，未宣称原地restore已经执行。

## 版本与实际证据

| 证据 | 源和真实结果 |
| --- | --- |
| native-before.json | 改码前实际31例：24满足/7漏判；12.747秒含初始化与清理，own exit0 |
| native-after.json | 首修31满足；15.771秒；入口尚未绑定commit，不能当最终精确源证明 |
| native-after-proof.json | 7c94fc6d入口核已提交产品/工具/lock SHA，31满足；9.639秒，own exit0 |
| native-after-static.json | 最终26d6328a入口核已提交字节，31满足；9.649秒，own exit0 |
| targeted-junit.xml | 首修53目标通过；包含原956的15项、原迁移序/默认值与19个新native层单位检查 |
| persistence-junit.xml | 首修本岗完整非integration：106通过、17按标记未选择，2个原record_property警告；不是123通过 |
| static-literals-junit.xml | 最终SQL字面量调整后同53目标通过0.84秒，不与之前计数相加 |
| bandit.json / bandit-static-literals.json | 首修新增SQL拼接触发B608退出1；改为四条完整字面SQL后退出0，无nosec/放宽门禁 |
| source-count-static.json | 原固定cloc2.10、精确26d6328a：应用5933行、超833、范围检查exit1 |

最终migrations.py SHA256：`cf2e6b30c6284148afc24b039ee483f744e9fa8af0fbe5f0982f67fb42371ca5`。原requirements.lock仍为3b15a7bdf93024750835ac20584a140eb93f1dc7476be61bb0af145e8ff0cc30，打包DDL仍c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4。

原956仅为Inspector-focused fixture隔离新增native补查层，原15项断言没降低。新19单位检查直接覆盖native层字段缺失、性质改变和查询错误传播；真实31例没有stub，使用真正check_schema/migrate及原冻结DDL。新固定源码5933相较5862 **净增71**；旧7c94计数5929单列保留，不用git物理diff或目标收益代替cloc。不将安全修复宣传为减量或性能优化。

## 资源、失败和未验证

四个自有临时实例只用项目tmp/794/{before,after,after-proof,after-static}新datadir、仅socket、禁mysqlx/网络、128MiB、570秒运行+30秒清理预算。每次核child PID+datadir命令、pidfile、@@datadir身份后正常SHUTDOWN，均exit0；数据保留，停后进程不存在。原PID7980/13306、其他schemas/config/env/runtime日志/凭据均不操作。没有云/CI/HTTP/负载或独立验收操作。

环境中根.venv没有SQLAlchemy，本岗另建ignored venv按原lock哈希装包。初pip系统CA缺失验证失败，显式使用/etc/ssl/cert.pem后成功，没有关闭TLS验证。首次工具Ruff提示C408/BLE001后改字面dict/具体异常；一次多文件patch因已格式化上下文不匹配原子拒绝，核diff无部分写再按实际行重试。几个定位路径不存在的读取失败如实发生，不当产品失败。

最终限定CI同配置Ruff通过，限定Bandit通过，元数据/源hash/进程保留检查见verification.json与stop-confirmation-final.json。未进行Linux/其他8.4patch/8.0矩阵、完整开发CI/覆盖率、独立验收或正式性能；四个附加查询只用于显式schema审计，没有改变每请求路径，但启动审计耗时差额未隔离测量。总协调仍需限定审核、整合后固定计数和统一CI，后续云测试绑定新的实际源。

本报告是AI真实过程材料，不能替代学生本人手写研究总结；提示词见prompt.md。
