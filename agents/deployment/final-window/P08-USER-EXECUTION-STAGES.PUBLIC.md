# P08用户亲自执行：最小阶段清单

当前仅本地文件准备。开机、云助手命令和压测所需命令均由用户亲自执行；root只核用户发回的PUBLIC事实、整理下一条命令及协调独立QA，不代执行。只取一轮准确90b的严格P结果，不追加F全验收、Word或重构。不能承诺一条命令跨两机和QA批准完成。

| 阶段 | 用户动作 | 自动化边界 |
| --- | --- | --- |
| 0 | root先核实际充值/欠费/可用额和平台保盘定时经济停机保护，用户再亲自开原两机 | 不新增资源；guest关机不等于计算停费。未验证平台保护则不开机 |
| 1 APP准备 | 一次粘贴`P08-USER-APP-PREPARE.INLINE.PUBLIC.sh` | 8049B级自包含，无GitHub下载；核真实APP boot/NTP、盘上P07/90b原SHA，安装未上传P08v2/S+1原字节并派生cap50工具；不freeze、不启动容器、不发SUT/QA请求、不创建费用批准 |
| 2 LOAD事实 | 用户执行root随后给的LOAD事实命令，发回原PUBLIC输出 | 只核本次LOAD boot/NTP、原Python/资源限制、QA公开安装和无旧负载；root先核两机事实。不能拿旧proof改时间 |
| 3 新费用+窗口 | root根据两个本次实际boot另写批准cap50费用原件；用户按给定命令在APP启动P08准备 | 计价起点取本次两机最早真实boot，不复用昨晚17:29或旧deadline；新LOAD就绪≤120秒。APP固定phase→新3账号/seed→service根副本→scheduler→新packet/790可自动；S10/E23/G25/C30不改 |
| 4 LOAD准备 | 用户把APP原PUBLIC bootstrap传到LOAD并执行原解密/ENTRY prepare命令，发回PUBLIC准备结果 | 加密传输和原五文件校验可自动；新binding/CA/import尽早收齐。独立QA核新target和一次grant，绝不绕过grant |
| 5 正式一次 | 独立QA/root批准后，用户在S−30前执行一条systemd定时arm命令，真实S+1调用原ENTRY | `P08-SPLUS1-EXEC`核原入口/grant SHA，S+1≤now<S+20才执行；过时拒绝、无重试、不retime。材料来不及则如实不启动 |
| 6 结果 | 用户执行给定取证命令，发回独立结果、退出状态和请求/资源证据 | 运行完成与400/600/270/1000达标分别报告；失败也真实输出，不自动继任轮；按已验证的平台保护收尾 |

**阶段1脚本说明**：只使用`/root/t44-final-20261029/ops01`、盘上`P07-CONTINUOUS-copyfix`及`source90b/official`。真实boot来自`/proc/stat btime`，NTP来自timedatectl；只输出PUBLIC元数据。若旧P07仍活动、已有P08派生件或NTP非yes，它只报告需root复核，不覆盖旧文件、不强制停止、不继续freeze。源码346 profile和P07 e880、六件新工件均严格核SHA；没有读取QA PRIVATE。内置费用上限50是新campaign内部上限，不是充值或余额保证。

**窗口协作**：两机通用身份/QA工具元数据必须在freeze前核完；idle立即取本次phase资料；packet生成后马上用户LOAD prepare，不等S前最后20秒才收资料。root给下一步命令前须说明仍有多少真实余窗；缺事实、未批准或超期就保留失败，不借历史时刻。此清单与脚本仅本地语法检查，未在两机演练，未创建定时器，未发生正式发压。
