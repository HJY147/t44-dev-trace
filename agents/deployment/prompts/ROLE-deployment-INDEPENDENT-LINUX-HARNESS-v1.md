# ROLE-deployment-INDEPENDENT-LINUX-HARNESS-v1

## 总协调实际派工原文

ROLE-deployment-INDEPENDENT-LINUX-HARNESS-v1：先只读看根189dc4a及已有docker-integration.yml/Compose，设计并实现供下一轮无历史独立tester使用的中性托管Linux验收环境workflow，解决本地无Docker/Erlang/Rabbit、原v1 MQ/故障环境阻塞。你不写tester用例、不联系独立tester、不读tmp/independent/private-*，仅可读公开冻结1.1与published reports4文件（不跟其私有路径）。建议workflow_dispatch接精确product_source_sha和独立tester自己冻结的harness_ref/path，分别checkout，搭真实MySQL/Rabbit/API/worker/scanner，明确中性CLI/SQL只读审计及受限可恢复故障控制；只提供能力，不注入预期缺陷/通过结论。采用现有Docker方案/镜像固定版本，随机凭据仅runner临时私密/mask，token read-only，artifact严格白名单不含.env/cover/private数据。harness_ref可以是tester冻结commit中tmp/independent/...入口，root不读未发布内容；若有更简单稳妥等效方案可提出。环境脚本不是测试；需新增自测文件先申请下一编号953，所有测试文件须tmp。不可改产品业务/现有门禁/统计口径。负责部署目录/.github新workflow+必要README/role日志/module/handoff/prompt/核验本岗实际Issue及PR15对接。先反馈可执行方案/限制，再做可review产物；必要环境自检一次，不重复0448 Docker整套。需tester harness才可执行的部分明确待运行，绝不伪造独立已覆盖fault。保留失败及恢复。无需租云/购买/触个人服务。

## 实际澄清与登记

- 总协调分配953给tmp/deployment/953_acceptance_environment.py，根ledger next952。不得修改他岗/独立私有用例。
- 总协调要求可取回的tester证据，不能仅runner临时明文后销毁；提出tester本地私钥/冻结接收证书，OpenSSL CMS密文artifact，tester自行解密审查发布，root/dev不读未发布资料。
- 总协调要求核实dispatch依赖default branch。官方主源确认、本仓库main无workflow；实际实现严格分支/path push请求入口，不改保护或提前合main。
- BE独占profile窗口期间仅写代码/资料和远程接口，未执行本地953/安装/浏览器等；总协调明确窗口结束后才运行本岗25项guard与静态核验。

## 产物对应与理由

新增deployment/acceptance/{run.py,control.py,README.md,request.json}、新workflow、953守卫及本岗日志/报告/handoff。能力和独立用例分开；精确双SHA、只读SQL、受限故障/恢复、密文取回和公开artifact白名单均是运行边界，不是独立用例或验收结论。不把跨岗新派工算同一提示词六版演进，不虚构用户亲自改码。

- 追加实际约束：总协调要求不用189dc4a立即环境check，等待随后完整1.1产品修正的准确SHA；实现先独立commit/push，请求另交。为避免旧runtime push自动重跑整套，部署使用同worktree新本岗分支codex/deployment-acceptance-environment，既有门禁不改。
- 总协调随后实际指定远端完整产品4c20f32b71635016815420472b9d4bb4fa850df0，只运行本轮唯一环境check/恢复/加密roundtrip；独立harness仍待冻结，不注入产品调试结论。

## 必要修复与能力补充实际派工

原失败保留。修复实际连接/早失败归档后，已授权一次有针对性的环境能力复核，不必再等或向用户要确认：先前“唯一check”是避免无变化重跑旧0448整套，失败后必要复验本就在职责内。只在新实际代码变更后提交新request触发一轮，不能虚称首轮通过。请先从公共diagnostics核具体异常/连接阶段（DB还是AMQP/拒绝or鉴权orDNS），不要仅凭internal网络猜因；日志只记录异常类别/安全状态，不泄临时凭据。继续保持产品Compose不改、仅本验收override中性环境，harness仍未运行。

根读中性protocol发现all38ops的通用环境能力缺口：有scheduler-scope轮换CLI，但context只给manager/read-only/AMQP，未给tester用于内部升级HTTP入口的限定service bearer。请补一个中性service-credential/issue-service控制能力：仅本project显式project-id/scope(escalation:write)、短TTL，按现有真实CLI签发或读取受控scanner凭据并只输出给harness私密stdout/0600文件；公开control-events只记project_count/会话元数据，不记token，不能把reader查hash冒作能调用。不需要也不得问新tester要用例。该能力是既有接口鉴权所需，不是某缺陷复现夹具，protocol/953必要guard同步，环境check可验证返回metadata/有效scope但不泄密、不跑独立业务案例。如果实际已有未列的可用接口请说明并补README，而不要重复造能力。
