# 前端模块报告｜通知独立计数修复与开发验证完成

## 实现与范围
- Vue3/TypeScript/Element Plus完整留痕前端；本轮ROLE-frontend-INDEPENDENT-UI-FIX-v1，产品源码f6547f2。
- 项目/成员、迭代容量、任务负责人/排期依赖/七态、八段十项评审、四视角预案审核、发布回滚返工已实现。
- 同源/api/v1、内存Bearer，401清身份；网络不确定写保留同body/key，403/409刷新且保留表单，422定位字段。
- 字典/模板/规则与状态以服务器为准；无前端扫描器、无假成功，安全证据链接；手机卡片、标签/焦点保留。
- 88e修迭代record.plan/plan.name与重放历史提示；bfa删除83条实际未用旧样式，未压缩/删业务或a11y。
- IAT-UI-v1-01：个人通知直接显示服务器unread_count/unhandled_count；分页不按rows算总数。
- 加载/错误隐藏旧值，动作/刷新后读取权威计数；保留本人/project scope与sequence乱序隔离；读和处理分开。
- 本轮产品仅一行统计区；未改冻结11件、后端/部署，未引入D005/D006或1.1逻辑。

## 正式独立输入与深链边界
- 只读根公开v1-ui-addendum.md/.json并核对指定SHA；不跟随私有证据、未读独立用例/联系tester。
- 其目标e8ceefe6，不能当b485/f654复测。迭代空白观察对应已有88e修复，未篡改原报告结论。
- 当前只有/tasks、/notifications等区域路由，没有项目/任务资源URL参数；抽屉ID仅本地状态。
- 未把深链环境阻塞认作权限漏洞，未为凑通过发明资源路由；公开说明agents/frontend/iat-ui-deeplink-boundary.md。

## 开发测试与精确CI证据
- 983新增3项先红后绿：完整分页总计、先处理仍未读再读、切项目乱序/403隐藏旧统计。
- 原iat-ui-01-before与targeted-after日志/raw gzip不变；阶段仅3项通过，不倒填历史成全套。
- 续派核查精确f654 CI push39948047446（PR39948051877亦绿）；原frontend artifact12498618830 ZIP摘要已验证。
- CI实际27/27、零跳过；typecheck/build成功；本地未重复同源码全套/覆盖/构建。
- 全19 TS/Vue分母与当前源码路径严格一致：行92.79%(309/333)、分支87.88%(689/784)、函数84.68%(188/222)。
- main/router仍计分母；只给行80%门槛，未新增分支/函数阈值。证据agents/frontend/iat-ui-ci-f654/。
- CSS49.99kB/gzip9.19，JS822.96kB/gzip162.12；原CI保留>500kB提示，未抬高阈值。

## 修复后真实开发浏览器
- 前端f654源码；后端固定02ecdea9（字节等价3b6dab5，IAT01～05修复），runtime1.0.0/t44_dev/18080。
- 根迁移18表226列通过；本岗只起5173，未碰tester端口/数据库；runtime公开receipt hash留本岗记录。
- 真UI建task21→限定project10服务身份创建event179→根真实故障worker产生通知5/6；不SQL造通知。
- 通知5 API/页面计数1/1→仅handling1/0→显式read0/0，已处理仍未读真实可见；三次任务GET均state1/version2。
- 项目10→3(0/0,total0)→10与刷新计数均匹配服务器；服务端总计直接呈现，浏览器未造多页数据，分页分母由模块回归覆盖。
- 一次披露的真实GET abort验证错误时旧数隐藏，解除控制后真实200刷新恢复；无伪造响应/状态。
- 一次浏览器run exit0，80 HTTP、pageerror0，console仅1条主动网络故障ERR_FAILED；不能写console零错。
- 1440/390截图已实际查看，计数/动作可见、无横溢出；counts-result.json含各步请求ID/计数/任务版本。
- 原始证据agents/frontend/iat-ui-counts-browser/与*.log/gzip；新fixture不重置旧通知。

## 当前交接
- 最小产品提交f6547f237bba12262b95d2701a7d0c9c0b474280已push；本轮最终仅测试工具/公开证据/记录更新，源码未再改。
- 实际prompt、WORKLOG、handoff与GitHub评论正文齐；原C-P1/C-P2/通知即时resize失败均保持旧阶段事实。
- Chrome与本岗5173已关闭；无独立复测/正式性能/全面安全或Rabbit成功链结论。
- 后续契约演进和资源深链需求另派；本轮不以开发回归撤销原独立失败/阻塞。
