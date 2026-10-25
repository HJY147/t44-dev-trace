# Provider 修订复审：限定边界闭环

## 1. 对象

固定AI reviewer，只审根托管环境provider。精确HEAD `49ef08a7e726fa163106647b96e415213f2aae8f`，root报告测试逻辑源`df53c85fd96537ffb4e149c10e9717234a9af14e`；49ef最后将相同UTC瞬间用instant比较，避免时间串微秒格式差异。原a6c/6d09源码和首次阻断报告保持，不把静态发现改写为已跑红测试。

## 2. 责任与信任

仅821_provider、821_scope_checks、设计三文件及其Git源。根托管application-binding/env/CLI/controller由部署先核，本岗按明示信任，不读取private值或会话、实际receipt、token，也不运行provider/CLI/DB/HTTP。独立控制器/functional grant另范围；本报告不单独授权执行或证明项目scope已应用。

## 3. Expiry 与40上限闭环

统一UTC+paired保守mono截止并与supervisor原hard_deadline取min；inner每新path先检查40与双截止。CLI、scheduler apply、sealer均调用remaining裁剪timeout，剩余期耗尽不启动下一阶段。reply先在私有item内staged，成功后再检查remaining并os.link不覆盖发布，不能在明确超期时继续公开。原两P2在阶段启动/循环控制范围闭环。

## 4. 活跃 nonce 闭环

必填supervisor-receipt，根明确选择本次PUBLIC/runtime路径；拒symlink，核freeze、expires_at语义同瞬间、48hex nonce与两个正整数live PID。request的context.supervisor_nonce与该receipt精确相等，不再只truthy。root流程明确先看到本次实际PUBLIC receipt再启动provider，不从incoming request反推活跃身份。native/source/resources/single ID/scope/nonce文件名约束保持。

## 5. Secret 与固有限制

新0700/排他0600目录、token-file、stdin sealer、ciphertext PUBLIC和失败类名记录不变。单scheduler每次替换仍意味着旧项目不再周期扫描，不能用旧token仍可调用API冒充该项目持续被扫描。check到syscall存在普通调度间隙；subprocess timeout不等已提交token撤销，也不证明controller后代/scheduler自动全回滚。按已核owned部署/watchdog契约处理，不为本地恶意进程增加新需求。

## 6. 实际核验

三文件实际bytes同49ef；hash/命名测试源到49ef差量原件见`agents/reviewer/evidence/functional-provider-49ef/static-audit.json`。root报告11无网guard绿，本岗只读源码，0重跑/新probe、0CLI/DB/HTTP/SUT。旧7只覆盖validate若干参数，不覆盖原阶段间超期、inner40或活跃receipt来源；新11补helper/nonce目标也不冒真实主流程执行。Ruff/format/check0为root报告，本岗未重跑。所有旧源/原JUnit由root保留；本岗没有编造已执行红样本。

## 7. 十项判定

| 项 | 判定 | 依据 |
|---|---|---|
| 1 精确身份 | 通过 | 49ef实际三文件bytes/hash |
| 2 范围 | 通过 | root环境provider，不是业务用例 |
| 3 双截止 | 通过限定范围 | paired + receipt min、每阶段remaining |
| 4 次数 | 通过 | inner40重查 |
| 5 活跃nonce | 通过 | 明确receipt/semantic UTC/livePID/exact compare |
| 6 根托管source/env | 依明示信任 | 不另读private值，不扩大威胁模型 |
| 7 Secret/原件 | 静态保持 | token-file/stdin/cipher staged/link不覆盖 |
| 8 在途副作用 | 限制已列 | 不冒原子撤销/进程树全回滚 |
| 9 自测真实性 | 通过限定范围 | 11绿仅root报告，0本岗执行 |
| 10 功能执行 | 本报告不单独准入 | 还需控制器新freeze+精确grant/实际receipt |

## 8. 结论

未见此provider本身剩余具体功能技术阻断，旧两P2与nonce接口在限定范围闭环。已先给root结论；v4 PUBLIC控制器和中性grant单独审查，不能将本结论套成独立SUT已授权/执行。新provider源或信任契约变化另审。
