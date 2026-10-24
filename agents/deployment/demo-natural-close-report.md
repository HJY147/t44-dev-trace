# 原14400秒演示自然结束只读封档

本页只对应 `app_20261023_234943_3f9bad` 的既有演示生命周期。应用仍为 `bc5aef9c62393134582affb7a690acb33ac2b833`，控制器实现 `62ac2f327e7523ffed69a2bd9f98c87ba2372931`；没有续期、重启或运行后置脚本补证。

- 原开始：2026-10-23 23:49:43.904838 UTC；原截止：2026-10-24 03:49:43.904838 UTC（北京时间11:49:43.904838）。配置14400秒未变。03:48:40Z先记录只读设计，单次等待55秒；03:50:20Z在截止后读取实际终结回执。
- 原控制器summary：`stop_reason=duration_elapsed`、`success=true`、`cleanup_success=true`，结束03:49:48.016395Z；从开始至结束14404.111557秒，其中原截止至结束4.111557秒为结束清理阶段。最终status为finished，78次追加TTL300轮换。controller累计验证81条扫描是验证子集，不称数据库总扫描数；首次实际扫描间隔60.319299秒。
- 原driver回执：实际退出码0，结束03:49:48.338874Z，确认runner实际退出，`wait15000_unconfirmed=false`。原有编排随后自行产生post回执：实际退出码0，结束03:49:49.462396Z。本岗没有执行driver/862/863/post。
- 既有post证明：89个已登记进程（含runner）全部不存在；API实际worker数4；spawn为API/consumer/UI各1、scanner80代；Rabbit与EPMD不存在；本run五端口18088/5178/25674/35674/24369均unbound（lsof退出1）。post记录92个源文件已核；controller SHA仍084618…。
- 原protected-after-finish与before-serve九端口记录逐项相等。03:52:30Z本岗另一次只读快照，原driver43819/runner43888均不存在；九端口PID/UID/start/pgid/command SHA及监听地址与before-serve仍逐项相等。仅读进程/监听元数据，没有连接对应应用或数据库。driver/controller/runtime文件SHA与原绑定全部相同。

证据：`demo-natural-close-validation/terminal-first-read.json`、`post-listener-observation.json`记录白名单事实和原文件SHA/字节数，原私密回执继续留原路径，不公开argv、Token、SQL行、通知内容或完整post证明。`manifest.json`标识本次公开投影字节。03:17Z“尚无末次回执/最终结果未知”的旧快照保持原样；原失败360及新360成功记录均不回写。

这是原4小时演示自然结束及清理的实际回执，不是全时连续健康、浏览器业务、正式400/600/270/1000性能、独立验收或云部署通过。历史16事件/26通知仍只复核，`new_publish_by_this_run_claimed=false`；本轮没有新发压/HTTP/SQL/浏览器/信号/服务操作、没有读取独立私密资料。未另行全量重采业务/会话数据；没有以提取器成功代替driver实际退出，亦无缺失终结回执待补。
