### 后端 801：源935新诊断P准备器/短窗工具（非独立验收）

工具 C `f811c5c1cc4573ab57db1be35fa1e9ade379d7cf`，仅 `tmp/801_backend_diag_fixture` 与本岗记录；产品935零改，未执行云/实际MySQL/正式压力或读取实际私密账号。

810观测entry不依赖sessionpacket，可先启动；801准备器只准精确新库/3306非root及根显式三角色文件，先 `--inspect-only --slots400` 输出真实候选匿名counts，0登录/令牌/业务写。实际不足400保留统计并拒，非业务缺陷，可1/40先诊断；原6000/9000库400候选当前NOT_PROVEN，静态seed算法600候选不冒实库观察。

根后续运行的普通prepare使用原CLI对实际40项目全集授权服务会话、三次真实TLS登录、实际SQL任务选择；独占transition/escalation任务、先真create再新key验证真dedup。driver四真实路径使用当前版本、新幂等key、strictCA持久连接且reset不重试；提交后失响应会resumable=false，不能盲续旧包。

最终同13个owned目标1.45s绿（SQLite原CLI/API、实际40项目/缩样400任务、transport stub、提交后断连和不足400零写），不是云TLS/MySQL/400持续证明。最初测试误猜提醒201而冻结实际202的1红11绿和lint失误保留，后窄修为精确202，不改业务断言。公包12643字符/install13724，均小于18432且owned实际展开逐字一致；prepare SHA `b53e8f0add93948fc787bfdfe0ddf5d7e14b499c930070650c328399f18facbd`，HTTP SHA `ef065f56e74e8bb1b6c8289bfe5618cbfe3b130e95dcdfea54e4483b109971d3`。

交接：`agents/backend/diag-fixture-20261025/{design,report,runbook}.md`，`verification.json`、原始红/绿log/XML、精确公源包与receipt齐。真实执行、原21UTC hardstop、正式400/600/270门槛与资源/费用由根统一核对；AI过程记录不冒学生手写报告。
