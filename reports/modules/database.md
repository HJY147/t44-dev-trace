# 数据库模块报告：两默认候选db87已提交，CI pending交接

- Agent-Role database；Prompt-Ref ROLE-database-POOL-DEFAULT-CANDIDATE-v1；基点5408c05→设计d4e152f→准确候选db87d30449356f3473b645a5c246dcc6c21d7cbe，Draft PR39。
- candidate branch codex/database-pool-default-candidate/PR head固定db87，当前metadata证据另分支codex/database-pool-default-evidence；不合integration，演示仍bc5。
- 产品只有MySQLSettings默认pool_size5→15/max_overflow10→0两literal。exact-diff证其他整个应用、14冻结、993/930/955及auth/锁/事务/超时/pre_ping/LIFO/reset/UTC/RC原字节同基线。
- 标准六默认池峰90同、保留上界30→90；partial size3峰13→3、partial overflow2峰7→17，双显式3+2/旧5+10保持。更多idle、内存/FD/全局余量未知，额外实例另算，不承诺503归零。
- root预留869：旧配置实际QueuePool返还只5非15真实红保留；候选10案例绿（含同目标），证容量拒绝/返还/两波复用/溢出关闭/dispose及Settings真实lazy factory原选项。无本机HTTP/SQL/真实连接/负载。
- 原993/930硬5+10不改，单独930collect-only0/exit5（matching文件名但无test函数），未跑历史负载；hosted实际JUnit待取得，不能把全suite说成旧930负载验证。
- 限定Ruff通过；原固定cloc基线6307→候选6307/净0，--require-range仍exit1，规模不达标。
- 一次push product40039282322、一次PR docker40039333270，最近GET均in_progress、准确head db87；初始PR merge快照400a5cac...，实际checkout/coverage分母/全套故障/容器结果待root只读跟踪，不冒用旧510/89或ABBA。
- Issue4评论6376739028/Issue3评论6376739310实际POST+精确GET逐字一致，summary/github-readback/ci-requested/pr-snapshot/cloc可核。
- 按root允许pending时先释放槽；不重触发套件、不设review通过或生产/正式性能准入。原正式失败/源码超限/本人材料缺口保持，操作者AI非学生亲改。
