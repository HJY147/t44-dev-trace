# T44 多 agent 团队协作规范

本规范把用户最初要求的十个岗位和随后追加的审核岗落实为十一个岗位的固定职责、责任目录、接口交接和可验证的记录。岗位长期存在；实例按任务启动、完成后释放执行槽位，后续以岗位文件恢复工作。当前并发上限是四个活跃 agent，包含总协调，岗位分批执行。

## 岗位与目录

| 岗位 ID | 工作内容 | 代码和配置责任目录 | 对接对象 |
| --- | --- | --- | --- |
| frontend | 页面、交互、错误提示、前端测试 | frontend/ | backend、messaging |
| backend | 鉴权、项目权限、业务状态机、评审与上线决策、事务 | backend/app/api/、backend/app/domain/、backend/app/services/、backend/tests/ | frontend、database、messaging、scheduler |
| database | 表结构、字段规范、迁移、索引、数据约束、数据生成 | database/、backend/app/persistence/ | backend、messaging、scheduler、deployment |
| messaging | RabbitMQ 投递与消费、通知去重、故障降级、站内消息列表 | backend/app/messaging/、backend/tests/messaging/ | backend、scheduler、database、frontend、deployment |
| scheduler | 临期/超期扫描、规则、扫描幂等、重启续扫 | backend/app/scheduling/、backend/tests/scheduling/ | database、messaging、backend、deployment |
| deployment | 打包、Compose、启动、环境、部署、备份恢复、主干门禁运行机制 | deploy/、scripts/ops/、.github/workflows/ | 各开发岗、总协调 |
| testing | 独立验收设计、功能与安全/故障/并发/性能测试、结果 | tests/acceptance/、tests/performance/、reports/independent-tests/ | 仅总协调，不直接联系开发岗 |
| documentation | 收集岗位事实，汇总需求、设计、测试结果与研究分析报告 | docs/reports/、reports/final/ | 各开发岗、guidance、prompt_engineering；测试只收冻结报告 |
| guidance | 回答零碎问题、操作指导、解释概念、记录用户决策 | records/qa/、docs/user-guide/ | 总协调及相关责任岗 |
| prompt_engineering | 保存原始 prompt、优化、按实际迭代登记、上下文到产物映射 | records/prompts/、docs/prompting/ | 各岗；不得联系独立测试岗注入提示 |

| reviewer | 审核其他岗位的阶段PR、证据和门禁，结论绑定commit SHA | reports/reviews/、docs/reviews/ | 总协调和开发岗；不接触独立测试内部上下文 |

“消息列表”按消息队列后端及站内通知列表业务两部分承接。消息岗拥有查询/已读等业务契约，前端岗拥有页面代码，不重复建立第二套通知数据。

后端不能直接改数据库岗的模型与迁移；其他岗不能直接改另一个岗的代码。共享接口由总协调冻结，变更需列出调用方、兼容影响和验证。接口未冻结时标为草案，禁止把岗位各自猜测当作联调契约。

## 每岗的固定产物

每岗都有任务书、按真实执行追加的工作日志、模块报告及结构化交接单。开发模块报告覆盖需求映射、输入输出、设计取舍、代码位置、对接记录、执行结果、限制和后续事项。代码作者仍须解释自己的设计，不能把全部记录外包给文档岗。

交接单字段为 role、stage、implementation_status、artifacts、interfaces、commands_executed、results、unverified、questions、prompt_refs、updated_at。资料必须包含文件位置；自测与独立验收分别标识。

## 调度和对接

1. 提示词岗规范原始请求，总协调保存实际派工信息；独立测试可从原始需求独立建立验收基线。
2. 前端、后端、数据库形成接口及数据设计提案；总协调消除冲突，冻结可实现的契约。
3. 消息、调度、部署按契约提出方案，再进入各责任岗编码和必要自测；集成时继续记录对接结果。
4. 独立测试在无历史实例中冻结用例、检查被测版本、出具事实报告；总协调派发缺陷，责任岗修正。复测实例仍无开发上下文。
5. 文档岗主动向各责任岗索取资料；不得把“我完成了”替代证据。所有正式测试通过声明引用独立报告的版本和原始结果。
6. 指导岗整理用户问题和本人决定；提示词岗整理实际 prompt 演进。报告中人的判断需用户自己的事实支持。

文档岗的实际询问须留下询问、回答、时间及证据路径。测试岗不参与开发群聊，文档岗的测试资料询问经总协调转交中性问题或直接读取冻结结果。

## 质量与提交

测试用例、执行结果和覆盖率不是同一件事；未执行不得写通过。需求报告、设计报告、最终代码、测试结果、AI 可执行规格及其说明、AI 时代软件开发研究分析报告分别归档，避免只交一个总结文件遗漏其他材料。

团队约束和岗位任务是本项目的 AI 可执行规格的一部分，不等于业务需求已经冻结。初始化报告不等于最终模块报告，人员初始化完成不等于软件完成。
