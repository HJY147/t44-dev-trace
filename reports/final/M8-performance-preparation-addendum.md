# T44 性能准备尝试与H2方法修订补充说明

AI文档岗整理；固定新资料截止5ce98e0d46aec9ccde9a9a177d34137d6a651ae9。本说明只据五份明确公开资料，补充原M8截止之后的准备尝试和H2授权，不修改旧Word、旧QA或旧截止。六个新H2请求尚无公开结果，不等待它们或声称作业通过。

## 1 原六次准备退出不构成正式性能失败

[原公开摘要](../acceptance/v4-performance-original-attempts-public-summary.md)和[对应JSON](../../records/acceptance/v4-performance-original-attempts-public-summary.json)均明确：原H六次已启动脚本并exit1，环境ready与最终恢复都true；预热/稳态未开始，正式目标请求0，正式性能全部NOT_RUN。不能由workflow failure判400并发、600秒稳态、270ms P95、每分钟1000成功或零非预期业务失败的正式要求已通过或失败。正式P95/吞吐/业务失败数是null、不适用，不填0。

| 源与入口 | 运行ID | 实际准备秒 | 准备HTTP记录 | 正式状态 |
| --- | --- | ---: | ---: | --- |
| S1 / 868 | 40042618474 | 330.057 | 24459 | NOT_RUN |
| S2 / 868 | 40042618509 | 330.051 | 32835 | NOT_RUN |
| S1 / 867 | 40042618553 | 330.062 | 24883 | NOT_RUN |
| S2 / 867 | 40042618129 | 143.563 | 7141 | NOT_RUN |
| S1 / 866 | 40042617380 | 330.116 | 16394 | NOT_RUN |
| S2 / 866 | 40042618006 | 330.107 | 19479 | NOT_RUN |

330秒整体准备上限和5秒准备HTTP上限是tester在H中自选的工具预算，**不是老师验收指标**，也不是01:43UTC窗口截止造成终止。五次预算耗尽各取消40请求；S2-867先有1次无HTTP响应TimeoutError，退出附近32次ReadError和6次RuntimeError。不能把退出错误直接算38个独立产品故障。“无响应”不是HTTP状态码，未观察明确非2xx业务拒绝或已确认不变量违例，也不证明业务正确。

125191条记录全部属于公开HTTP准备，最多40个并行项目准备会话，正式400用户未激活。失败路径未做完整fixture表计数，实际项目/任务/依赖/评审决定数均unknown；不能按201响应数推算或填0。timing统一setup标签，不能完整重建每endpoint组成；准备诊断时延不作正式P95或S1/S2排名。资源采样放在完整准备之后而未到达，CPU/内存/worker/usage均unknown，不拿环境ready或工具合成绿补造RSS、峰值、物理同机及背景流量结论。原密文/timing校验和解密是tester公开摘要中的操作，本岗未读取或重算私密原件。

## 2 H2是接触SUT之后的明确方法修订

原摘要发表时H2尚未冻结；后来[H2冻结元数据](../../records/acceptance/v4-performance-h2-freeze-metadata.json)明确给出H2=fc75ca7d092517f597c8931d9e8d11b646e441b7、post_SUT_method_revision=true、first_blind_test_claimed=false、pure_mechanical_fix_claimed=false。这是观察准备失败后的方法修订，不是原H续跑、纯格式修复或预盲测；原六attempt和NOT_RUN状态永久保留，H2不能倒改它们或证明H到H2的正式提升。

| 方法/判据 | 原H | H2公开修订及边界 |
| --- | --- | --- |
| fixture准备整体预算 | 330秒 | 900秒，仍是有界工具预算，不保证准备完成 |
| 准备HTTP超时 | 5秒 | 30秒；预热/稳态/后检HTTP仍5秒 |
| 准备失败证据 | 未取得失败路径fixture计数/资源 | 记录已确认项目范围、等待同级客户端取消收尾、SELECT-only计数与有界资源观察，保留首要失败，无额外settle sleep或重试 |
| 正式判据 | 400用户/600秒，P95≤270ms、成功吞吐≥1000/分钟、非预期失败0 | 保持；无新增thinktime、自动重试或忽略业务拒绝 |
| 业务fixture与正式段 | 40项目/6000任务/9000依赖/15000评审决定 | 元数据声明规模、判据及18个正式片段字节保持；HTTP helper已改变，whole harness并非字节相同 |

上表的片段保持是公开元数据声明，不是文档岗打开H/H2源码或私密证明后独立核验。失败后观察能力的加入不代表未来运行一定返回完整数据；实际缺失仍unknown。

## 3 r2绑定与六个新请求只到授权

[r2环境绑定](../../records/acceptance/v4-performance-environment-binding-r2.json)支持harness 60至1800秒、job40分钟，只替代新H2请求的旧绑定；中性实现origin为f84c23762bcdc0cd08bcac6e51be0c04c20c4909。实际将执行各自不可变R，不能以origin冒实际R或SUT。绑定文件里的目标进程/资源能力不是本次真实资源观察值。

[H2运行绑定](../../records/acceptance/v4-performance-h2-runtime-binding.json)随后明确授权同H2、S1=bc5与S2=db87各3入口，共6个全新hosted隔离请求，harness1800秒/job40分钟。冻结元数据当时“尚未收到新绑定/未执行”与此后授权按时间分开，不将旧字段当后续授权不存在，也不把授权当运行已完成。此截止没有六个H2实际结果，既不预填通过，也不预填失败。

S1/S2须同H2/判据/fixture规则，每次新环境；host/背景变化仍限制比较。该新协议不是旧轮私密协议逐字复跑，旧六准备NOT_RUN不与旧v3正式结论混计。只有tester读取、解密输出并明确发表后的摘要才能进入另一增量。

## 4 本次核对与归属

五个公开文件各自Git blob/SHA-256、六行运行对象/准备记录/状态、总125191、异常1+32+6、fixture及正式指标null、H2三方绑定/预算和正式判据已做有限逐条一致性校验，详见[来源及检查](../../docs/reports/M8-performance-preparation-validation.json)。没有跟metadata私密路径、读取cases/raw/H/Word/R002或联系tester，没有运行服务/测试/CI/负载/Word。旧截止只追加本说明入口，旧35页技术稿及原33/35页QA不改。提示词六版与人工12/5/3不重新计数，学生研究正文本人写，本说明不构成最终作业或性能通过。
