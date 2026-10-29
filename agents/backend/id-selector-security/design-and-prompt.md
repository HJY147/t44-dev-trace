# F04公开契约缺陷：整数selector SQL表达式分类

后端AI。基准确356f29983c904e949245aedfad464efc1bf7b63d，自有worktree/分支codex/backend-id-selector-security；不读取QA私有、不联系tester、不修改测量源/服务。

实际派工：
> Continue original project /Users/yang/Desktop/nothing/软件开发大作业, readAGENTS, use isolated worktree/branch. IndependentF04 on frozen356f found ONE confirmedcontractbug: GET /api/v1/projects/1/tasks?owner_id=1%20OR%201%3D1 actual422 PARAMETER_INVALID/audit75; frozen listTasks explicitlyIDselectorSQLattack→400 SECURITY_INPUT_REJECTED. Inputrejected, noSQLsuccess. Need minimalproductionfix +meaningful regression under tmp descending convention +moduleprocessreport +commit, keep currentperformancepaths semantics. RootcurrentlyP04measuringunchanged356f18:24..18:37. DoNOTreadQA PRIVATE or contact tester. Use publiccontract/code only. Onlyimplementcontractfix, tests; nootheropportunisticrefactor. Returncommit/SHA/CI/build needs asap.

公开冻结listTasks x-error-cases明确ID/枚举/排序selector含明确SQL攻击表达式返回400。api._ATTACK已在鉴权之后、类型解码之前处理selector，但缺少不带引号的数字OR/AND数字等式；随后整数解码返回422。最小修复仅扩既有selector攻击正则一类明确数字布尔等式，不处理普通业务正文，不把普通引号/任意非法ID一概判SQL注入。查询仍参数化；不改Schema、鉴权优先、角色、锁、事务、幂等/审计、正常任务/校验/性能路径、池或代理。

在原tmp/backend/contracts/986_http.py补真实SQLite/TestClient回归：准确编码URL400/固定错误/响应Schema及独立拒绝audit，实际SQL事件确认不执行任务业务SELECT；普通非法owner仍422、合法owner筛选仍200，缺身份仍先401。先旧源真实红再窄改绿；这是开发回归，不是MySQL/独立验收或P04重测。无新测试文件编号/无样式重构，完整新源CI/build在新commit后另行绑定。
