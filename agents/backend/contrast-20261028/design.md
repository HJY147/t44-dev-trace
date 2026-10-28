# 新源双臂开发诊断夹具：先绑定，再准备

后端AI，2026-10-28。用户恢复后的总协调派工；不是独立验收。Git实核目标a12e9e70b963bacafda3242bb6d82e53ee912ff1相对f4只改migrations.py（净+74物理行，git统计+75/-1），产品与26d6328a一致。以下不修改产品/CLI、不访问云或任何私密运行资料。

## 输入输出与阶段

1. Host bootstrap显式接收新phaseDir/bindingSHA/新输出名/UTC anchor；核root Linux、private binding、完整file_hashes、实际新源image/全源清单与live stop timer。只准P7/P16新namespace；旧935/f4、F、过期窗口、symlink及已有输出拒绝。data-only原admin内先核19应用表空，再原CLI创建三个真实synthetic用户，随机口令仅stdin与0600账号文件。种子使用原公开seed_demo(seed=44,anchor_at=04:00Z)产生V2 40/6000/9000/15000；CLI没有seed/anchor选项，已获总协调明确采用原函数而不改产品。
2. S1在data-only原admin读实际SQL候选，核实际用户/项目成员/容量/已完成依赖；用anchor至原stop整窗同级提醒条件选441个互不重叠task对（1 baseline+40 warmup+400 measurement），各项目轮转。原CLI签发40个实际项目scope服务令牌，核auth_sessions存储摘要/权限并证明未创建提醒；只向S2传候选私包。
3. S2仅官方Python+stdlib工具、edge网络、固定CA与实际TLS目标，不能挂产品/DB env。真实三次登录，逐slot核GET与契约，经HTTP各创建一次提醒并新key去重一次，保存真实递增版本及事件ID。只输出metadata，账号/令牌/会话保留0600，根不读正文。
4. LOAD只接CA、control、session包与精确hash，沿既有受限私网TLS或一次性加密运输，禁止在UI/日志打印包正文，拒绝传DSN或用户账号。先1客户端20循环(offset0)、40客户端5循环(offset1)预热，再400客户端5循环(offset41)计量；分别新O_EXCL输出，400组预热前不使用。四操作为真实GET/contract/block-unblock/已有提醒dedup，每组完整8000请求；超时、错误或不完整均终止并禁止续包。

## 不变量

source始终固定a12完整SHA；每phase控制包绑定真实binding、namespace、database、workers、CA、target、stop、anchor；不得通过伪装旧source935准入来运行新源。两臂seed44/anchor04:00一致，分别新namespace与账号/任务组，候选selection摘要应一致才能比较。S2和client的prepared窗口最多600秒且截止不超原stop，真实session TTL不修改，不自签令牌或改时钟。所有旧云记录/控制器/私包保持。

## 本地验证与边界

先做过期/旧源/错binding/namespace/CA/角色/私有文件/覆盖等守卫及导入无副作用。之后在本岗临时准确a12源快照、真实SQLite schema+原handler/CLI做小规模兼容链，完整V2种子另核441候选充足；SQLite不证明MySQL锁或TLS网络。root执行新源云两臂后才有相应回执。正式独立792/799/800资料不读、不联系，临时790工具不替代独立400×600秒验收。
