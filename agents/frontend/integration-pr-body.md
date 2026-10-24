实现“留痕”完整业务前端：登录与项目成员、迭代容量、任务排期/依赖和七态动作、八段十项评审、四视角上线预案及审核、经理发布回滚返工、通知已读与处理分离、升级规则历史和项目审计。页面以冻结API为权威，同源Bearer、幂等重试、403/409刷新和422字段错误、手机卡片/抽屉及可访问控件。

修复审核正式发现的迭代嵌套plan预填/名称与历史重放误报当前状态；删除83条实际未使用foundation CSS，未删业务/a11y。24项模块测试、完整src行92.19% (307/333)、分支86.76%、函数83.78%，vue-tsc/build通过，保留bundle体积提示。

真实浏览器→18080→MySQL：完整七态/评审/预案/回滚返工/审计282HTTP通过，仅预期403；新task20/event173通知3真实read后仍未处理，再显式handling，三次权威GET状态/版本不变。写运行之后即时resize断言失败保留；等待实际抽屉关闭和展开详情后，最终114HTTP只读复查通过、console/pageerror0。截图/公共HTTP/全部失败在agents/frontend/integration-*，测试在tmp/frontend；不把模块证据等同独立验收/性能或Rabbit成功链。

Agent-Role: frontend
Prompt-Ref: ROLE-frontend-INTEGRATION-v1
Refs: #2
