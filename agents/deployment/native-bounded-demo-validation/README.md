# 有界本机演示工具阶段证据

新工作区/分支deployment-bounded-demo，基于实时root c1aff86；先行设计daaccb7。原应用固定bc5，原capture窄修保留；旧PR31/34、原run1失败/0a6 run2成功/cd3仅关闭P2的历史均不改写。

工具新增serve/明确duration180..14400、私密runner/status、SIGINT/TERM标记、安全点与到期cleanup、剩120秒的TTL300 scanner轮换、新tick/锁确认，以及完整身份匹配runner PID的stop请求。默认run入口仍不传serve控制；capture AST与runtime.py不变，无业务/锁/规则差量。

`serve-guards-final.json/.log`仅执行现有871的ServeGuards 17项：时限真假类型/范围、信号handler恢复、单调deadline、早停/错误仍cleanup、单run一次/ready与cleanup分开、固定source/controller/角色拒绝、ready自己的会话回收、stop精确PID/无group/身份失配拒绝、absent不冒充cleanup、轮换顺序/失败不提前完成、expiry余量、公共白名单、默认run分支。初始14项与后扩展17项分别保存，最终口径17项，不累计凑数；Ruff原件通过。

全部身份/信号/HTTP/DB/子进程由合成替身，未读真实凭据、没有真实被测服务或OS信号；未跑旧ApplicationGuards/CaptureGuards/873全套/完整cycle/中性或独立套件。source-scope.json记录新源SHA/路径，CLI帮助只解析参数，不启动应用。

**当前未准入/未执行360秒实跑。** 等根确认压力比较窗口；实际证据后还需专职新增范围审核，才可另准入用户限时演示。公共结果白名单与私密原回执分别保存，未来实跑的secret扫描另作真实记录，不能把本合成无秘密状态写成已读凭据扫0，也不能回填独立正式三组同次unknown。
