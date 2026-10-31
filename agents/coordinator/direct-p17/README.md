# P17：修正后置核验后的单次压测入口

以READY.PUBLIC.json为准；只有READY_FOR_USER_BOOT才通知用户开机。原P16包已消费、v1/v1.1工具有已知缺陷，本入口仅使用冻结v1.2源和新目录，不能重试旧轮次。

用户开原64核APP(0mt)和16核LOAD(0mu)，给出当前公网IP后，总协调运行：

```sh
python3 /Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/global-latency-repair-20261031/agents/coordinator/direct-p17/after_boot.py --app-ip 当前0mt公网IP --load-ip 当前0mu公网IP
```

开机后不构建镜像、不下载依赖、不开发脚本、不重新排期、不等旧完整扫描。单入口并行上传固定小包和启动既有服务；短暂的连接/服务就绪等待及获取新会话是本轮执行步骤，无法在关机时完成，不冒称耗时为零。主机pin和永久restrict密钥沿用，不临时授权。原来源、业务日期、鉴权、持久性和DDL不改。

本轮测量400客户端、60秒预热、600秒稳态，四类P95≤270ms，每个完成分钟≥1000、稳态零错误；另要求400最终快照和400完整历史审计在原40秒预算内完成。额外30秒只清理，不能补算成功；总退出码反映完整结果。旧direct准备豁免保留，因此不冒称课程全部业务门禁正式验收。v1.2有效运行身份绑定原runtime+post+compiled+BOOT，不把整个工具说成原字节。

新run r30posttools17，新远端/root/t44-direct-p17，新LOAD工作区/root/t44-final-20261101/QA753_POSTTOOLS_V12_P17，均独占创建。启动写入不重试。发生异常时先只读确认远端wrapper已退出，再尝试回收已封存密文；未证明退出则明确记录待回收，不强制封存/停机；Mac只转公开证书/密文，不读测试PRIVATE、原始响应或明文Token/密钥。

APP观察回收后立即通知用户可停APP；LOAD完整密文下载并核bytes/SHA后立即通知用户可停两台。随后独立解密判读在本地进行。没有VM关机命令、倒计时或自动新轮次。
