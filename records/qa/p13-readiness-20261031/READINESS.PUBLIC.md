# P13 PUBLIC离线接口复核

结论：现有PUBLIC准备接口完整，可保留原字节；本次未更改包装、原测量工具或断言。仅确认公开调用关系与本地冻结字节一致，未运行原工具，未证明已安装工具身份或实际运行兼容性。现有公开接口SHA为 e92b18416324f8ec436808ee7edf0a67febed561。

run=r30manualp13；material=r30materialresume06；maintenance=r30restoretransition06。400客户端、60秒预热、600秒稳态、P95≤270ms、每个测量分钟吞吐≥1000、零业务错误及原全部断言不变。真实identity/grant/prepare/execute本轮均未签发或执行，全部许可保持false。

## 中性准入材料清单

以下均需本轮实际原件、SHA256、采集UTC、实际主机/容器绑定和缺失声明：

1. 七个APP角色实际容器ID、不可变镜像/config digest、源提交/源manifest、bundle manifest、源到镜像映射和真实导入receipt/provenance。由原验证器接受；不能以旧资料改名替代。
2. 当前APP/DB CPU、内存、资源预算；LOAD镜像及实际资源、固定8CPU/8GiB预算；独占、无其他写者/运行事实。
3. APP0mt当前磁盘ID及挂载用途、盘型/等级/容量/IOPS等实际读回原件，与本轮APP/DB身份和采集时间绑定。用户报告ESSD PL1 40GiB 3800IOPS仅为待核对输入，不能作为已验证身份；不据此复用旧批准。
4. 实际隔离schema、准确迁移SQL/hash和执行receipt、迁移前后DDL/索引/约束原件、fingerprint、冻结v1.2语义比较和绑定全部原件的补充manifest；缺失before-state如实保留。补充审查不冒充原V4断言。
5. 四个真实会话的主体/角色/范围/实际到期，400客户端/800不同任务资格与项目分布、任务状态/归属/计划/结束、升级事件/规则/时间、fixture SHA与真实计数及演示数据规模。秘密只进入封存中性包。
6. TLS origin/connect IP、CA字节SHA、有效证书与有效期、封存传输receipt、本轮链绑定；opened的session.private.json、ca.pem、source-manifest.json、backend-bundle-manifest.json、backend-import-receipt.json准确SHA。packet与target/grant身份分别满足原接口。
7. 独立当前身份审核通过后才可签IDENTITY_ONLY_FOR_ZERO_SUT_PREPARE；prepare的原default-false grant、环境SHA、五项输入绑定、新输出未消费及排他证据。再独立审查全部七项review字段、schema补充绑定和实际会话到期，签一次性决策；当前没有该决策。身份/源/镜像/schema/会话/输入/排他变化使准入失效。

## 工具身份及公开命令

冻结ENTRY SHA256：d15874c477fef0d92bc68ab77802a5354d15be237c853621b56467005c20d43e

冻结ADAPTER SHA256：a4cbb793ac6ecb292ad6d4c6451052b051a1ea50fbf798ccad4463b92173fc1c

原tool-manifest SHA256：78a0aca6e90b61695338a332f7adb1becb5f7eebd13d0c8bd28d3f6ff4f09a05

原runner：sha256:4f3baf081863a4580b5608699d9a7a8af2d89c3e87abbb60089b630b9102b2a1（不是本轮产品镜像身份）。包装逐文件SHA见原DELIVERY_MANIFEST.PUBLIC.json，本次全部核对相符。

全部公开命令及参数保持 records/qa/p13-public-20261030/READY_INTERFACE.PUBLIC.md 原样。prepare→ISSUE_ONCE→原ENTRY execute；phase观察→所有写者确已停止后seal。不得现在执行。`--check-only`也需要已签身份并核对ENTRY/ADAPTER和新路径，不能证明packet、安装工具、云或SUT就绪。实际prepare才检查原manifest及已安装工具hash，并调用原ENTRY。

RUNNING400仅证明readiness barrier释放，FINISHED不等于PASS。真实执行需在四会话最早到期减900秒和独立decision期限前触发，只消费一次，不自动重试/后继。原始结果及备份验证仅交新独立PRIVATE实例；不得交开发或总协调明文。

## 本次验证与限制

本地三份Python仅AST解析，shell仅sh -n；6个PUBLIC交付文件SHA与manifest一致；6份冻结需求/规则/契约/数据库输入SHA与v1.2冻结一致。原任务书原件直接读取DOCX XML，确认400并发10分钟、P95≤270ms、吞吐≥1000/分钟及无失败。旧TASK所指specs/sources在本worktree不存在，未据此声称已读；改读项目根原始任务书、作业要求和提交注意事项，无改写。

未读开发日志、issue47讨论、其他岗内部材料、PRIVATE实现/结果；未访问云/SSH/SUT，未签真实身份或许可，未新造测量用例。共享文件系统只实现流程隔离，非操作系统隔离。证据为CHECK.PUBLIC.json。本次提示词ID：ROLE-testing-P13-READINESS-20261031-v1，按当前任务约束限定公开核对，无额外演进版本。
