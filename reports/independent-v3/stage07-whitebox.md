# v3 限定白盒核验

结论：原4项白盒范围中2项通过、2项部分证实；不构成整体验收通过。对象始终为 `bc5aef9c62393134582affb7a690acb33ac2b833`。黑盒已经封存，本阶段未重设计或重跑任何黑盒案例，开发测试数量不计入独立黑盒整例。

源码访问在9c742c6明确解除后开始。正白名单190文件均核对SHA-256、精确Git blob、0444及复核后字节未变；190是完整性核验数，不代表逐行深入审核了190文件。

| 原范围项 | 结论 | 已核实与边界 |
| --- | --- | --- |
| W01 参数化SQL、状态机、门面与注入 | 通过已审范围 | RowsGateway用SQLAlchemy绑定值、表列及操作白名单；内部text片段为固定文本。decide为无SQL的纯状态决定。API组合根注入UoW factory、通知及升级门面，扫描独立进程。不能外推为全站安全证明。 |
| W02 全量suite及生产分母覆盖率≥80% | 通过 | 独立触发exact bc5的原product流水线，后端510/0失败/0错误/0跳过，前端89/0失败/0pending；全部44 Python、20 TS/Vue生产文件在分母，main/router的未覆盖也保留。 |
| W03 三门禁与真实PR失败阻断 | 部分证实 | 当前exact bc5的static/contracts/coverage/frontend实际通过；历史PR13在717cd65、reviewer/stage=failure、临时ready时实际merge exit1且main未变。当前5contexts保护配置有据；未逐项制造当前5门禁失败并尝试合并。 |
| W04 新评审项或升级规则≤1配置+1模块且≤1人日 | 部分证实 | 私密副本分别新增规则和评审项，各只改1配置、0 Python模块；实际diff及6个纯解释器检查留存。自动执行约0.225秒不等于人工工作人日；真实人工工时和部署启用流程未提供/未执行。 |

本岗通过GitHub连接器在exact bc5创建 `codex/whitebox-v3-source`，触发[实际run40033980420](https://github.com/HJY147/t44-dev-trace/actions/runs/40033980420)。四任务均成功；MySQL8.4/Rabbit4使用workflow隔离服务及显式迁移。四个工件下载后核对GitHub SHA-256，独立解析JUnit、Coverage JSON及Istanbul数据复算：

| 指标 | 后端 | 前端 |
| --- | --- | --- |
| 完整测试数 | 510 | 89 |
| 生产分母文件 | 44 Python | 20 TS/Vue |
| 行覆盖率 | 2638/2957＝89.21% | 364/390＝93.33% |
| 分支覆盖率（单列） | 659/824＝79.98% | 821/932＝88.09% |
| 后端排除行 | 0 | 不适用 |

契约、集成、故障标记分别162、93、19项，与510全套重叠，不能相加。前端CSS/HTML不在可执行TS/Vue覆盖分母；源代码规模另按已批准cloc口径统计。行覆盖率门槛与分支覆盖率分开，不将Coverage混合百分比87.20%误当后端行覆盖率。

历史拒合并原件位于bc0cd349的 `records/github/protected-merge-probe.json`；第一attempt只是GET main发生EOF，没有merge调用。完整第二attempt的head为717cd65，reviewer/stage真实failure ID57066080416，ready后merge返回base branch policy prohibits，main前后均1996d444，随后恢复draft。本岗再次只读核到该旧SHA仍为failure。它证明当时单context配置的拒绝，不能当成当前五项逐个失败的因果实验。

当前保护快照要求reviewer/stage、static、contracts、coverage、frontend，strict/enforce_admins开启，禁止force-push；四product检查来自GitHub Actions app15368。当前PR21仍draft/open，head为47184824，74个应用Git树条目与bc5完全相同；其文档/运维提交身份仍与被测bc5分开。draft/blocked本身不证明某失败检查造成拒合并。本岗没有新merge或修改保护。

过程异常如实留存：源开放后一次六模块读取误用了本岗旧机械工作目录，立即核对6/6字节均等于白名单bc5，弃用该次证据并在正确只读快照重读；没有读到其他候选源码，也未据源码改变已封存黑盒。一次私有覆盖摘要写入发生本岗变量遮蔽错误，修正后复算，原错误保留，不计产品缺陷。

本阶段新增确认应用逻辑缺陷0。尚未执行的当前逐门禁因果拒合并、扩展部署路径，以及缺少的真实人工工时均保留，不被绿色开发suite覆盖。更早正式性能失败、规范优先级未决与故障切点能力阻塞仍按stage04–06封存结论。

仅本MD及同名JSON明确发布；私密源副本、原驱动、用例、预期、原输出、截图、封面值、密钥均未发布。JSON列出来源SHA及证据摘要hash，不能据此跟读私密引用。
