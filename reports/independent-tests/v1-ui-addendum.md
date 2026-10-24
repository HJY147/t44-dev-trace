UI环境补充验收v1已完成：5项中3通过、1失败、1完整用例仍环境阻塞。执行窗口2026-10-23T11:08:46.555Z至2026-10-23T11:32:07.745Z，发布时刻2026-10-23T11:34:52.497226+00:00。这是AI浏览器自动化观察，不是真人手测。

本次是原报告发布后补交中性前端环境，前后端仍为`e8ceefe699951c52d4b01023b47a76b575d48c2a`，未收到修复版本或开发解释。只访问5174前端及其18081/t44_acceptance代理，使用本实例普通账号和新建合成项目1008/迭代1009/任务1150。未读取产品源、开发日志/测试或其他岗资料，也未使用后续审计SQL能力。

原v1发布时5项UI因目标未提供而阻塞；原报告、结果和900条计数保持当时记录，不倒填。本补充不会撤销原v1业务与性能失败结论。

|原件|保持不变的SHA256|
|---|---|
|v1-blackbox-report.md|`edde6aa85653cc697c31d51f7c01d909a399cbc04d4cd40c577c4ed5706c99f8`|
|v1-blackbox-results.json|`e88a2b30c2823c9fa5f6fd3a6eeaf5d960bc266edce8da98064dcfe519049e0d`|

原6个冻结文件及冻结摘要亦再次核对未改。冻结摘要SHA256：`23a69bf10a50a63ebcef214d6ea9d088a0a0a9094d1b9fb821bb21ed4f996ffc`。

方法为persistent node_repl调用Playwright1.62.1、安装的GoogleChrome156.0.8078.47，headless1440×1000，时区Asia/Shanghai。通过可见控件操作并记录带UTC时间的截图、DOM可见文本和真实API请求ID。没有把工具误定位/等待超时算成产品失败：初次会话因错误按钮名重建；表单关闭后的动态locator和原生details/summary识别已修正并留存工具限制记录。

|冻结编号|本次状态|实际观察及边界|
|---|---|---|
|UI-browser_end_to_end|通过|页面创建项目/成员/迭代/任务，阻塞解除、退回重提、完整评审、独立预案评审、经理交付/回滚/显式返工；刷新及重新登录后记录和历史保留。最终state2/version19、排期5、交付轮次2、评审轮次1；实际操作者ID与UTC转北京时间已核对。|
|UI-browser_permissions|环境阻塞，部分观察通过|成员撤销后旧页面查询403，刷新清空列表；未参与账号无项目选项，篡改选择触发真实UI403，已知API深链亦403。前端资源抽屉不产生资源URL，未得到实际前端资源深链及参数约定，因此完整前端深链步骤保留，未用API深链替代。|
|UI-browser_conflicts|通过|双页同版本一次成功/一次409并查询最新；收到真实历史重放version6后显示权威version7。参数/证据反馈定位到字段并给出追踪编号。|
|UI-browser_notifications|失败|降级标记、独立读/处理动作、刷新持久化和任务不被自动解决均观察通过；页面未呈现冻结要求的独立未读/未处理总计。|
|UI-browser_evidence_safety|通过|HTML/引号/文档型脚本地址为惰性文本；HTTPS链接带noopener noreferrer；未见脚本执行、危险链接或自动宣称引用内容已核验。|

历史重放观察使用了明确的浏览器网络控制：先让真实API完成version6提交但暂不向页面交付，另一页面真实提交推进到version7，再以同键向真实API请求，得到meta.replayed=true/version6，并将这份真实响应交付页面。没有伪造响应状态或内容。UI重新查询并保持version7；这验证历史响应处理，不声称验证未观察的UI自动重试/保键策略。

**IAT-UI-v1-01，medium：通知页缺少独立未读/未处理总计。** 最小复现为新项目有一条未读且未处理的降级通知，打开通知中心，再只处理而不标已读。API初始计数1/1，处理后1/0；行状态正确变为“未读·已处理”，页面仍只有“共1条”和逐条标记，没有两项独立总计。本条失败指计数呈现，不是通知状态写入失败。

请求ID：`ea131d55-be99-4d0b-8e79-5699f679d139`、`f21e8579-d99d-4fba-ae7e-a094cc6d03a4`。

经理通知833先处理后仍未读；开发通知834先读后仍未处理，再处理得到0/0。通知带实际“降级站内待办”标记，刷新后保存；查看关联任务仍为state2/version19。通知夹具由公开服务API和本实例真实messaging进程产生，没有伪造通知。原环境仍无真实RabbitMQ，故不证明broker投递。

**IAT-UI-v1-02，low：所属迭代选项无名称。** UI创建的迭代1009在真实API中plan.name为“IAT UI iteration”，登记任务时option value1009的文本为空，选择后显示空白。该条为同一流程中的可用性观察；单一迭代下本次流程仍已完成，没有凭此扩大完整流程用例失败。

权限的已观察请求包括撤销成员后的`2264da22-5b61-4714-9e59-6f666720ae62`和未参与账号API深链`eedf7c4f-1e96-4a42-810c-78fbfff7dcce`，均403且无current_version/current_state或任务内容。为触发前端错误处理，测试工具给未参与账号的选择框增加了一个不可信项目选项，再使用正常选择事件；真实后端作出拒绝。没有把隐藏按钮当权限证据，也没有猜测未提供的前端资源路由。

若产品支持前端资源深链，后续仍需中性提供其真实URL/参数约定以完成UI-browser_permissions的剩余步骤。目前观察到打开任务抽屉后URL仍为/tasks或/notifications，未把这点直接宣称为权限漏洞或路由功能缺陷。

关键私有证据及SHA256如下；完整清单与每项请求ID在JSON伴随文件中，完整用例步骤和原始记录保持私有。

|证据文件|SHA256|
|---|---|
|961_ui_network.jsonl|`bd3ad108ece9168267f920dc641414ebfad0554dbbb59945eb21ba9c8462896f`|
|961_ui_observations.jsonl|`ec9fedc1110ad2652e5efba45a570a3022c80a32169dfc6a100056029e406925`|
|961_ui_controlled_replay.json|`0259984c4dc9d6f8170abc752a13ec589f90f9faf67b4710cdda9fc71754652d`|
|961_ui_safety.json|`92b16c575daf13260c48b270c8bbae1e538b14a8d3d8b253765b3f4860c12743`|
|961_ui_24_rework_after_reload.png|`dc56d30c1bddbe68249e12844d5efd31a4dabf363bea0f5c548bd38e38ec7647`|
|961_ui_26_manager_notifications_before.png|`5867d064697ba58e0e61d82d9c5028f9233a9f0f7d3a60bbfef2d87aea2cd7f5`|
|961_ui_27_handled_but_unread.png|`d6660d491b3555b7df48916876e061e41ed00120bebb1ad8ff5cd744aba7fc9a`|
|961_ui_38b_blank_iteration_option.png|`f2efcf7b93294696637e09e39e721f8f76c8ac6838dd1dcb20f2883f9f56fbb5`|

截图38初版捕获在模态动画期间，保留原件但不作为空白选项的视觉证据；38b使用稳定元素截图并已目视核对。浏览器网络记录已去除密码和token，截图不包含登录密码。

自建浏览器和messaging进程组28689已关闭；Vite、API和MySQL共享进程未停止。此阶段仅完成原5项UI环境续验，未开展修复后复测、SQL审计或白盒检查。
