# 修正后置工具后的P17离线准备

用户本轮原话：“找到现在问题的具体原因，并真正解决了，然后讲所有准备工作做好以后，通知我开启服务器进行压测验收”。该授权覆盖新一轮离线物料、入口与必要验证，全部准备后通知用户开机；准备期间无SSH/云/SUT，不自动开机或倒计时停机。

总协调继续使用被测bcec产品源，v1.2原runtime9cf/postfeff/compiledff95/BOOT09e9组合。旧P16四P95与稳态指标已达标，剩余失败是后置核验不完整，不能混称当前稳态仍慢。HTTP完整响应在AsyncResult等待40秒处超时、旧全局stop立即关闭在途连接的源码路径与原认证时间线相符；逐条云端断链没有独立stack，保留因果证据的边界。新版本提高仅post校验/并行效率，修正配额后/实际dispatch前期限门禁、强引用schema memo、owner退出再close和完整结果退出码，旧NP不回写。

本轮只复用永久restrict密钥和原hostpin。新RUN=r30posttools17，material transport身份r30materialposttools17，DIRECTpacket.run_id与RUN相同，不能套legacy NEUTRAL身份协议。新REMOTE=/root/t44-direct-p17，KIT=REMOTE/kit，APP初始化输出REMOTE/app-init；LOAD工作区/root/t44-final-20261101/QA753_POSTTOOLS_V12_P17。所有目录独占，禁止旧prefix复用。

部署岗49114a86已核完整中文producer与原真实router集成；总协调8组本地控制流检查已过，含旧身份拒绝、失败不dispatch、不重试、非零仍备份、坏hash不宣称回收、外置控制日志。原product CI不因工具改动重复运行。当前尚待QA具体接口/环境复核与最终总包独立审核，READY仍PREPARING_DO_NOT_START_SERVERS。

操作者均为AI实际角色，研究报告不冒充学生本人，需规/设计继续暂停。本文件仅工程记录。


首次新入口独立审核12ac2c18明确BLOCKED：可直接CLI绕READY、监控超时缺少回收路径。两个问题均由root修复：run.py本身也校READY/包hash/本地源；dispatch前落仅表示尝试的marker，异常后只读确认wrapper退出，才下载已封存密文并验hash，未知/活动状态不封存、不重发、不谎称可停LOAD。正常非零仍回收；fallback另名保留原失败。新增门禁/异常/活动状态/坏hash回归，控制流11组通过。原拒绝报告不改写。首次本地SSH配置演练因macOS /var临时目录不是canonical路径失败；只将合成临时路径resolve后重跑，通过两原hostpin/永久key元数据及本地生成，零连接。
