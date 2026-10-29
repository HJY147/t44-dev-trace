# v3 scope桥预算修复与5d/16Z派生包限定复审

## 1. 对象与基线

AI reviewer，`ROLE-reviewer-V4-BRIDGE-RECHECK-20261028-v1`。原 [阻断报告](v4-bridge-20261028.md) 与原161桥、失败探针不改。本次修复源码 `5cedb2caf06369cf20c196eba106b072eaa61810`，完整交付 `5f6791308772cab9b53b3eba46acc1d2b1f91831`；实际读取并核这两提交的运行模块、测试、manifest及安装片字节相同。部署最终包 `25d863c5afce1fb84ea32300c45d123bb7919c76`；被打包SUT源仍为 `5d5e0a15e3b15e2f509c4ae71a927bbc35579be7`。本岗不读独立private、不联系测试岗、不访问云、不改产品。

## 2. 需求与范围

只复核两预算接口阻断、受影响的公开工具和准确source/profile/运输链。原120秒、nonce/key域、错误顺序、门槛和计数范围均不变。74本地检查是工具开发验证；没有新的独立业务、原生MySQL或400并发通过结论。

## 3. 实际修复

`generation()` 对 scheduler-token/rotate/start 透传 authority 中准确预算回执原路径及其PUBLIC副本SHA。`budget_receipt_binding()` 要求路径在本phase/receipts，文件名固定形状，PUBLIC原件绑定同binding/source/stop/project/database；APP再次按该SHA读取实际原路径。LOAD配置新增mysql_budget原件及独立APP实际路径，不把LOAD的副本路径当成APP原路径。

`_data()` 每个preflight/seal均在原共享operation lock内先调用原305f helper的admit，写有限PUBLIC准入回执后才运行直接SQL；GEN仍在父锁外。新 `live_mysql()` 核实际Compose project/service及CID，原helper继续核image、PID birth/StartedAt/restart、UUID/DB/预算。只是给本次加载的helper模块替换subprocess.run为剩余callback期限上界，原SQL、解析、measure/admit算法不变；没有改全局subprocess模块或延长原期限。

## 4. 原阻断复核

| 原项 | 本次结论 | 证据 |
| --- | --- | --- |
| V4-BRIDGE-01 | 本scope代码关闭 | 三action实际Capture测试核两flag与准确值；原receipt读取/phase绑定 |
| V4-BRIDGE-02 | 本scope代码关闭 | preflight/seal均LOCK→原admit/实际query解析→SQL→UNLOCK；无预算/换CID/restart/UUID/DB/容量不足先拒 |

三个原测试文件的全部Assert AST逐序相同，分别50、22、23，共95条，删除0。fixture只补新中性预算资料，旧mutex专项目标用中性admit替身保持原范围，另18新预算目标使用原305f逻辑和合成传输，未把替身冒作native MySQL。新manifest为 `e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7`；9运行文件逐项核字节/大小/哈希，4安装片在本岗74检查中真实重放及拒覆盖检查。

## 5. 部署最终字节链

profile SHA `3b3b6d4ca4f01a3f7bc36ac60cd2a56ce3930220251abc886de778db6d90f6f7`，准确源5d、53源文件、截止 `2026-10-28T16:00:00Z`；GEN `3232c18eb304d02875411d43f922b63f36a1e162c633eb808e67b3373e3cbcc9`、helper `305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d` 与5文件派生链相同。预算仍API64×5/0=320+64=384，真实上限仍待云query，F4/default亦保留。

六原安装脚本逐件核SHA/字节/完整base64+256说明预算，最大15372<18000；只替换目的根目录字面量，在本岗新本地目录实际重放6/6 exit0，安装的六文件逐字等于25d Git原件。没有安装到/root或运行派生GEN/Docker。

本地source ZIP166458字节、SHA `9ebb356360d190f466219a596f8d0954bb38399c0210d9aa75f9b47d81b9eea6`，不是官方CI下载。5件ZIP成员CRC/无重复/安全路径/无symlink、manifest和builder等哈希均核；未压缩TAR SHA `392222af763b6f7fe969d25e17621c381b7588a61f950adac79b6378e6f4bffb`。53源逐件对准确5d的bytes/hash与Git mode，47 frozen文件对935和5d字节及mode相同；共147次Git mode核对。实际运行原source receiver一次exit0。完整事实见 [字节链证据](../../agents/reviewer/evidence/v4-bridge-20261028/deployment-final-byte-chain.json)。

## 6. 本岗执行、失败与边界

本岗从准确Git对象复制公开工具至新 `tmp/781_reviewer_v4_20261028/`，无owner文件修改。首轮74检查73通过/1缺t44导入；第二轮补PYTHONPATH后73通过/1原断言要求product-source路径。两轮原log/XML保留；首轮外层shell在打印后exit0，pytest return未单独捕获，不能据shell0判通过。随后从准确5d归档product-source fixture，逐件核51文件原字节，未改原断言；第三轮 **74通过、0失败/error/skip、实际return0**。SQLite合成数据、假Docker/MySQL传输与真实本地flock/安装子进程分开描述；无HTTP、native MySQL、Linux/systemd或云。

首次部署字节链探针在六片已成功后失败：本岗误把git archive原始TAR模式0664要求为Git规范0644。原builder本就按exec bit规范化为0644/0755，再在build context固定写该模式；不是新模式偏差。原目标保留，未改包、原builder或receiver，第二独立目的目录重放并按既有算法核，实际原receiver也通过。首次失败只在本会话，不能伪称持久化了完整原stdout。

原源码、样例凭据或独立私件没有写入公开报告；临时product-source仅用于本地复审夹具，不提交重复应用源码。原应用规模、完整CI、真实预算、连续资源、F/600秒性能、账单和学生手写正文均未由本岗关闭。新增报告/JSON/岗位资料的scoped diff-check exit0；含原失败log/XML的全包diff-check exit2，六处原pytest尾空格按原字节保留，未把全包宣为绿色。

## 7. 十项门禁

准确版本/范围/修复接口/原断言/公开字节链在本scope通过；数据库实际运行、真实双机120秒链路和Linux外部guard健康未验证。业务状态机与外部API本次未改，不由工具检查推断验收成功。stop/status的预算前出口、原deadline与quarantine沿用原已审代码，未在新差分中改动。

## 8. 限定结论

**原两P1在准确v3代码scope关闭；25d最终公共包未发现新的限定阻断，可交总协调受限安装和新环境预检。** 这不是新F或正式性能的执行准入：仍需实际Linux守卫/新runtime、准确镜像与phase、实际MySQL预算及完整角色ENV、有效新授权、新nonce、足够原120秒端到端时延和完整资源留证。超期不得改旧stop补跑；新缺项依旧拒绝。没有发APPROVE、产品或正式性能通过状态。
