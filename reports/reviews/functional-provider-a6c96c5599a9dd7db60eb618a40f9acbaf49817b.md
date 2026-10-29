# 环境 provider 窄审：执行边界需修订

## 1. 对象与身份

固定AI reviewer，只审root环境provider，不是独立验收用例。目标HEAD `a6c96c5599a9dd7db60eb618a40f9acbaf49817b`，包含provider源6d09d2e；精确全SHA及三文件bytes/hash见`agents/reviewer/evidence/functional-provider-a6c/static-audit.json`。只读取821_provider、821_scope_checks和functional-provider-design，三文件与命名源逐字同。最初worktree有无关CI解压目录未跟踪，本岗只见路径未打开，不称全树干净。

## 2. 需求与信任边界

root明确由部署核验自有CLI/source appbinding、新schema/vhost与scheduler-control哈希，provider可信任这些根托管私有文件。本岗不读取其值或执行controller/CLI/DB/HTTP，不要求恶意本地进程/OS隔离增强。范围仅functional、有限活跃grant、实际单项目scope、nonce/环境绑定、secret传递与过期边界。独立控制器新版本另scope，不从本报告宣称其准入。

## 3. 保持的边界

main要求admitted=true/functional、grant与PUBLIC manifest freeze一致，sealer及部署controller哈希正确，CLI绑定source一致；request逐项比较tool/source/runtime/resources/functional、严格单个正整数ID、escalation:write及48hex nonce/文件名和时间窗。目标目录新建0700、排他0600文件；CLI token-file保存，controller读取文件，sealer由stdin收credential，PUBLIC reply只有ciphertext。失败普通输出仅异常类，不打印token/自由异常；可能含诊断的controller输出写在私有目录。本岗没有看到具体secret或实际授权结果。

## 4. P2 PROVIDER-EXPIRY-01

第65–71行仅validate一次检查UTC；第144行CLI最多30s，第158行controller最多45s，第201行sealer最多20s。其间没有重新检查stop/stop_mono或grant expiry，timeout也不按剩余预算裁剪。可在expiry前一瞬validate成功、CLI稍后返回，然后在过期后开始scheduler replace及sealed reply发布。外层while检查不能约束当前链，design的“provider stops at grant deadline”未实现。

最小修复：统一活跃UTC与独立monotonic截止，在每个会产生权限/进程/reply副作用的阶段前检查；子进程timeout由剩余预算裁剪，超期不再启动后续apply/seal。保存已可能提交token/部分apply的准确partial失败收据，不自动重试或声称原子回撤。已在途命令是否仍可产生晚副作用须按实际CLI/controller取消与owned进程监督契约披露；不能把timeout等同数据库事务回滚。到期后写失败/最终收据属于留痕，不混为新授权操作。

## 5. P2 PROVIDER-CAP-01 与 nonce 接口

40上限只在第113行outer while。内层for一次取得多个路径后，第117行seen.add没有再检len(seen)，例如进入for时39、还剩两个有效文件会处理至41。最小修复是在每个新path前重新检查时间及40上限，到限立即break，而不是完成整个glob再回outer while。现有7guard不覆盖此主循环。

第47–50行对supervisor_nonce只检查非空，没有与本次活跃receipt/根托管expected nonce相等。时间窗和runtime/source/resources不等于当前supervisor会话匹配。若root启动流程另已绑定唯一活跃nonce，应明确该契约/来源；否则给provider一个根托管expected值或受控PUBLIC receipt并精确比较，不能把truthy写作“已验证活跃会话”。这是当前输入接口尚缺的一项核对，不据此编造发生过credential泄露或实际跨run混用。

## 6. 限制与实际验证

0probe，0既有guard重跑，0CLI/DB/HTTP/SUT；未读829 private、用例、journal、keys或会话文件值。root报告7无网guard绿，本岗仅审源码的6个拒绝参数+1接受目标，不读取未指明的raw或冒称实跑。上述两反例来自直接控制流，无需搭建假业务或重复现有guard。

单scheduler每项目替换是已明确环境能力限制：先前token仍限自己的项目API，先前项目不再周期扫描。本报告如实保留，不擅自要求新多项目scheduler，也不把限制当产品bug或偷偷扩scope。实际root grant/env/provider启动尚未授权，不从准备好合成session推导可执行。

## 7. 十项判定

| 项 | 判定 | 依据 |
|---|---|---|
| 1 身份与源 | 通过限定范围 | 精确a6c/6d09三文件hash |
| 2 范围/信任 | 通过限定范围 | 只根托管环境provider，不扩本地恶意进程模型 |
| 3 scope输入 | 静态部分通过 | 单实际ID/strict int、精确context/nonce文件名 |
| 4 环境来源 | 依根托管已核契约 | 不读取private值、CLI source及controller SHA约束 |
| 5 过期副作用 | 不通过 | validate后子进程链未重查剩余期 |
| 6 40上限 | 不通过 | inner for可越过40 |
| 7 活跃nonce | 待闭合接口 | 仅truthy，尚无exact active来源 |
| 8 secret/原件 | 静态限定通过 | 私有模式/token-file/stdin/sealed reply，未见值 |
| 9 执行真实性 | 通过限定范围 | 7绿仅root报告；本岗0probe/CLI/SUT |
| 10 功能执行 | 暂不准入 | 先修两P2并明确nonce契约，新源再审 |

## 8. 结论

当前provider有两个确定执行边界阻断，功能授权前须最小修订并给新精确源；同时闭合active supervisor nonce的核对来源。已先给root技术反馈，后封角色记录。根托管文件按题定信任，不读其值，不要求新业务功能，不改provider或独立工具，不联系测试agent。实际项目/凭据/调度配置结果仍无本岗执行证明。
