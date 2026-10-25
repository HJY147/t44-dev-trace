# 796：以MySQL规范输出替代自写迁移语法处理的准入探针

数据库AI，ROLE-database-CANONICAL-DDL-PROBE-v1；独立codex/database-canonical-ddl-probe，基f4bd382d4668130793fc553df9ce6363c4656ea6。只设计/隔离原型/本岗记录，不改产品、旧freeze/DDL/API/依赖/计数。原MySQL13306绝不连接、启停或修改；不访问独立799/800/805/809/814 PRIVATE/runtime/env。已有CI695/Docker是root提供的历史状态，不作本探针结果。

## 必须证明的I/O

输入：权威schema.sql原bytes/hash、pinned MySQL8.4精确patch/build与SESSION quote/sql_mode/charset/sql_generate_invisible_primary_key、可信新空独立schema生成的reference；不能取待检查目标DB的marker/catalog作为预期。输出：当前18表226列逐表结构差异、明确版本/目标错误，与旧正负兼容用例一致。reference只放表/列/index/FK/CHECK/engine/collation等契约数据与来源摘要；不放函数/分支/SQL业务实现以躲计数。只忽略表级AUTO_INCREMENT=<current counter>，绝不删列AUTO_INCREMENT或字符串中的相似文本。

## 两条候选及反证

A. 原生SHOW CREATE TABLE标准文本逐表比较（只移除表级auto counter），不自建SQL parser。先检MySQL本身是否将旧接受的等价DDL收敛到相同文本；官方已说明NO ACTION默认不出现在SHOW而等价RESTRICT显示，可能直接反证raw-hash路线。还要覆盖ASCII/utf8mb4引导符、冗余括号/大小写/函数/优先级、显式ASC/BTREE、同库限定FK与extra自动索引。不能把新拒绝包装成旧支持等价行为。
B. 原生生成的结构反射reference+运行时反射签名：若仍须保留CHECK parser/FK/index归一化，则把这些保留行、reference校验/错误/读取/生成器源码成本全部列净账；metadata Core builder不能无证据删除。明确这是数据预生成不是业务函数转JSON。

离线先枚举本岗公开956/988正负用例与原生静态结构、检查当前真实缺口（列auto_increment/engine/collation等），做不碰DB的差分/保护字段原型与cloc函数净账。仅公开原tests，独立私密不读；957原审核探针未经明确公开允许不读/不改。当前18表/226列；实际CHECK/FK个数以冻结source核定，不把父派工简称35混记为CHECK数。

## 真MySQL校准的待批命令资源（此刻不执行）

如离线不能完整确定A/B，提交root审批一个**全新本岗临时实例**：只用root明确指定的已存在pinned8.4 mysqld二进制、其version/SHA；新空datadir/socket/pid/log全部位于本worktree agents/database/canonical-ddl-probe/.runtime/mysql84目录，模式0700；--no-defaults --initialize-insecure，仅socket、--skip-networking --mysqlx=OFF，无TCP/13306/原配置/旧凭据。只创建两个明确schema：t44_796_reference、t44_796_actual；执行固定权威DDL与白名单局部ALTER/SHOW/reflect；仅此实例root经私有socket且目录700。最大10分钟/128MiB buffer pool/单进程，无paid资源。

命令顺序须root确认准确binary和批准后才运行：mkdir新目录→mysqld --no-defaults --initialize-insecure --datadir=<new> --basedir=<approved>→mysqld --no-defaults --skip-networking --mysqlx=OFF --innodb-buffer-pool-size=128M --socket=<own> --pid-file=<own> --datadir=<new> --log-error=<own>→固定2schema生成/逐例恢复→仅持有own pid经正常shutdown/有界回收。初始化确需的系统表空间包含在新datadir内，绝不动13306现有服务。不通过marker复用reference，外键当前库名称差异须实证，8.0/其他patch不默认为兼容。

本阶段输出可信失败/尚未生成的reference/未实测8.0/预计净账；若不能保持等价，或只有逻辑搬家/更严格误拒/净省不足100–250，就否决，不为762强推。原型在tmp/796_database_ddl_probe；输出沿O_EXCL|O_NOFOLLOW固定fd避免覆盖，先设计commit，再原型；新资源未批不执行MySQL。
