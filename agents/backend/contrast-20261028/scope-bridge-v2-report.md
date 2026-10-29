# 可预装scope回调桥：真实过程、最终离线结果与限制

后端AI，2026-10-28。此次仅实现和自测工具；没有云、SSH、SUT、独立用例/私包/密钥读取或新CI。产品源码、原冻结790七文件、v1/v2/v3诊断包、T15 provider及上次已结束的scope请求均不改。不是学生本人研究报告。

## 解决的问题和保留边界

上轮实际功能会话结束前，完整scope callback尚未预装；root已确认原等待120秒自然结束，而scheduler启动迟到，旧草案没有实际密封/交付。此次把LOAD取实际pending请求和活性、APP原GEN供应+真实credential验证+原wire密封、LOAD最终复验和原子交付三个步骤完整预装。没有给已结束请求补发，也没有把容器exit0或交付回执记为业务PASS。

根必须显式提供下一轮真实PUBLIC request/rootgrant/launch/supervisor/F binding/neutral identity/execution admission及SHA；六原件保留原字节，实际nonce、公钥、project/iteration scope只取该request。execution admission把rootgrant精确SHA与冻结build关联，弥补原launch/supervisor自身没有grantSHA的事实。旧公开实例仅供形状检查，不成为运行授权。

LOAD用实际Docker容器完整ID、host PID/startticks/PGID、容器NSpid/NSpgid、祖先关系、time namespace和operator UID检查owned live与pending；APP不能把跨机旧快照当持续活性证明。APP只接受30秒内快照、最多80秒lease，开始供应须剩45秒、执行最多60秒；原callback120秒和GEN至少600秒不变。LOAD最后独立再验活性/pending/本机monotonic截止，no-follow固定FD写入fsync后hardlink原子出现相同nonce密封文件，无覆盖、无半JSON；进程检查与文件发布不是一个OS原子事务，回执明示此观察限制。

APP原GEN首次scheduler-token、以后同owner健康scheduler用scheduler-rotate，再scheduler-start；实际scheduler image/labels/mount/env指针/原token文件SHA和原authstore digest/active/exact scope/expiry核同后才密封。token/K不进入argv/env/stdout，root只搬PUBLIC和opaque。原RSA3072 OAEP-SHA256/AES-CBC/HMAC编码器逐字同c89；不改ACK或撤销协议，撤销由原工具auth/logout。任何mutation后失败保phase quarantine，可能已在途的动作如实标记，不自动retry。实际入口强制同phase固定`.scope-callback-state`，后续nonce不能更换state绕过隔离。

## 按先设计、再红例、再修复的实际记录

| 阶段 | 实际发现/行动 | 结果及证据 |
| --- | --- | --- |
| 4c9715a6设计、4221d6c9 alpha | 无网络fake clock/owner、真实原CLI+SQLite/RSA roundtrip；新增边界发现argparse owner参数重复、进程在poll/getpgid间退出导致timeout丢prefix | 原2红无损gzip；79567a2a修复后26绿，再扩私密输入/原子发布等至34绿 |
| ee849653/62bffbd5/fc278283 | original CLI issued token→原authstore→seal→自有私钥验MAC/解密核digest；恢复原c89编码器字节；同公钥改PEM折行不能绕过key域 | v1最终34绿，encoder4895B SHA c89d0300...2ad06 |
| 570b90db封包器 | 本岗手填扩写freeze/build常量与协议原件不一致，真实metadata assertion红1 | 改AST读取原常量，安装9绿；未投云，错件保install-metadata-red-manifest |
| 447f611f v1封存 | 新目录四小片、实际本机子进程完整安装/拒覆盖/拒混装 | v1候选34+安装9；root新v4锁契约后封存不用、不回写 |
| 3a7dc84e设计、5aa72038红 | v1两个直接SQL阶段未取跨GEN共享mutex | preflight/seal各红1（总2），再分别取部署同锁，GEN父锁外 |
| v2首次联跑 | 本岗漏PYTHONPATH致原t44 import失败；新测试误写SHA拒绝错误名 | 2失败+39通过，保first-integration-setup-red.gz；修测试执行环境/错误名，原34断言未删 |
| 005349c8 | shared mutex和部署确切305f helper本地互斥/超时绿；实测CLI umask077使PUBLIC control目录0700，UID10001不能遍历 | 新红1封存后显式chmod755；安装器也显式0444/755，不依赖宿主umask |
| 最终v2 | 固定phase state守卫、原34逐字保留、部署实际helper只作本地公共fixture、完整小安装命令 | 56 passed / 0 failures/errors/skips；限定Ruff通过 |

这些是AI岗位的真实错误和修复，不改写为用户亲自排错。最终56是46桥/锁/原CLI/权限检查加10安装检查；不累加中间19/24/26/34/41/42/44/55等重复运行计数，不算独立验收。原34测试文件逐字一致，含50条assert，删除0。两项历史边界红、metadata红、锁红、执行环境错、umask红均保原失败内容或无损gzip，不规范化失败文本冒充原证据。

## 与部署岗最终对接

公共依赖部署v4 `mysql-budget.py` 21599B SHA `305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d`，原件只读，桥不改。新GEN安装进每个phase并在binding.file_hashes记录；桥manifest双pin。按已核字节compile载入，避免SHA核后再次按路径读取不同源码。每个SQL容器单独取operation_lock，等待min(10,剩余窗)，锁后再核deadline；GEN前释放让GEN自行取得同一`.v4-operation.lock`。真实本机flock检查了SQL时互斥、异常释放、GEN可取得锁、foreign锁有界timeout、错误依赖SHA导入前拒绝。

桥只使用one_serial_operation的15连接预留；observer独立锁计1，不额外常驻连接。64连接总预留由部署岗完整预算管理：F4=60+64=124，P16×20=320+64=384；实际globals、其它role及源必须由部署准入核。没有把400+64装进384，也没有据此声称提速。模块实际root/Linux模式和真实MySQL并发尚待下一窗口。

## 交付、可复核命令与未证实项

最终目录 `tmp/790_backend_contrast_20261028/scope-callback-bridge-v2-mutex/`。manifest SHA `f5623b9e9ea4b44d967c4c6ab1c2f1dbe22cfbcdd2165c440b5e20253c38df8b`；九runtime模块，phase helper不混装，fixture副本不进入运行包。四安装片含300字节说明的总长度仍<18000，命令本体11700/13021/16245/10852B；新目的两机`/root/t44-r9/scope-bridge-v2-01`。`delivery.PUBLIC.json`、`dependencies.PUBLIC.json`、`configuration.template.PUBLIC.json`和三个execute模板一起交根。完整步骤见scope-bridge-v2-runbook.md；null/尖括号不可原样执行。

最终本地执行使用原a12只读源码快照作PYTHONPATH、已授权旧依赖解释器；pytest输入为同目录790_bridge_checks.py、790_mutex_checks.py、790_install_checks.py，新独占basetemp为`tmp/790_backend_contrast_20261028/local-run-scope-v2-final02`，JUnit `final56-local.xml`。验证摘要和所有证据SHA在`verification.PUBLIC.json`。宿主兼容仅Python3.10 AST/标准库接口检查，实际测试机为Mac/Python3.12；部署模块的本地锁测试是本机flock，不冒充Linux双机或MySQL。

下一步必须根限定审查整个桥/部署接口、预装全部传输与执行小命令，给新源/新F/新rootgrant/实际owned runtime和新nonce；再核真实跨机搬运耗时，原120秒不延长。不自动开VM/发SUT/重跑旧会话，不声称独立业务验收、正式性能、代码规模或研究报告已完成。此次产品有效行节省为0，工具不参与产品规模口径。
