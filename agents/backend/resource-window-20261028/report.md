# P7 公共短窗与只读资源窗口聚合

操作者：backend AI；范围：开发诊断，不构成独立或正式性能验收。工作树从 `22f666e25d2b7280224e58eb1c91cf6be0077ac7` 建立；总协调确认无须重建到其协调树，由其处理岗位元数据合并。生产代码、配置、数据库、负载生成器、验收 oracle 均未修改。

## P7 已核实的请求结果

仅读总协调明确白名单的两个 PUBLIC 文件并核精确 SHA/字节：matrix 为 5961B / `8007971120f72242ca552153a1a9c1f200b44f4cc72bda0b5c89c17293452383`；mirror status 为 3043B / `b8abbb98482bd9aebe2c01b18fd1a4c6c1248478b51151a9f4805c66eb4a00fd`。结果源 `a12e9e70b963bacafda3242bb6d82e53ee912ff1`，API workers=7。

| 客户端 | 完成请求 | started→finished 秒 | barrier→finished 秒 | started 分母折算请求/分钟 | barrier 分母折算请求/分钟 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 80 | 4.467047 | 4.458703 | 1074.535370 | 1076.546251 |
| 40 | 800 | 3.417044 | 3.396640 | 14047.229126 | 14131.612417 |
| 400 | 8000 | 21.890740 | 21.742456 | 21927.079669 | 22076.622807 |

计算为 `observed_requests * 60 / elapsed_seconds`。400 客户端 started 为 `2026-10-28T06:33:02.088909+00:00`，barrier 为 `06:33:02.237193+00:00`，finished 为 `06:33:23.979649+00:00`；barrier 前耗时 0.148284 秒。两个分母均应显式标注，均为短窗等效速率，不能当作完整一分钟最低完成量。

| 路径 | 1客户端 P95 ms | 40客户端 P95 ms | 400客户端 P95 ms |
| --- | ---: | ---: | ---: |
| createEscalation | 64.055296 | 288.159190 | 1840.028403 |
| getTask | 52.055226 | 518.348331 | 1555.055565 |
| transitionTask | 68.005880 | 292.209303 | 1680.087258 |
| validateContractPayload | 51.987325 | 254.856585 | 1370.412573 |

400 客户端 8000/8000，200=6000、202=2000；failed/aborted/deadline clients 全 0。四路径 P95 均大于 270ms。summary 含失败请求，不将不同路径 P95 相加、平均为整体 P95。40 客户端仅 validate 路径 P95≤270ms；本轮没有 60 秒 warmup、600 秒 steady state 或每个完整分钟检查。零 HTTP 错误不等于性能通过；瓶颈与因果根因未证明。

PUBLIC mirror status 说明运输完整、7516207B、原始 SHA `2662a505f4034f63ae50f836d0c239cff1f2e018431cf2869af4a496ecbdd283`，全流每角色1067行，scheduler 的1067行 CPU/RSS 全 null。该全流覆盖不能替代具体 cohort 的资源统计。本岗未访问服务器原始文件，未运行云资源聚合。

## 脚本与数据语义

`tmp/788/resource_window.py` 9560B，SHA `f1df806992ba0c9b4508abf9ebe4a18cb80880b252559b9cf4e48a98e73037ab`。仅读明确的绝对 raw 路径；必传 sealed SHA、UTC begin/end。只读固定 FD，`O_NOFOLLOW` 拒绝末级符号链接，前后 fstat 检查，并在解析/输出前核 SHA；非空常规文件上限64MiB、单行256KiB、stdout32KiB，无写入/网络/目录发现。显式路径的祖先目录仍由调用方控制，本工具不宣称完整祖先路径防链接沙箱。

采样器白名单精确源44079B，SHA `3d9f096f8d51d2c46994089c437650fb6e710887739abe1d9a1fc81b3bdb44cd`，静态核实：

- `cpu_delta` 为 `(usage_usec_now - before) * 100000 / (monotonic_ns_now - before)`；单核满载=100%，可大于100%，不是整机总核归一化利用率。首样/计数器或时钟重置为 null。
- RSS 是 cgroup 含子 cgroup 的去重 PID 集合中每进程 `/proc/PID/stat` 的 RSS 字段×页大小之和；共享页会重复。任一进程不可读则 RSS=null，`unreadable_process_count` 保留。
- `cgroup_memory_bytes` 取 `memory.current`，含 cache/kernel，独立于进程 RSS 和；两者 maxima 不相加、不互换。
- 缺角色时 source 抛 `ValueError("missing_role")`，拼接 `type(error).__name__ + ":" + str(error)`，精确值 `ValueError:missing_role`；scheduler 缺失保留 null。

按七个真实 role 独立输出 CPU p50/p95/max、RSS max、cgroup max；CPU 分位数采用样本等权 nearest-rank，不是按采样时长加权的整窗利用率。缺值与非法值计数独立；无有效样本时指标 null。资源行选择为 `begin <= resource_sample.utc <= end`，CPU 值仍对应前一个 cgroup CPU 读取间隔，可能越过窗口起点，采样点 maxima 不是连续真实峰值。

输出同时列出采样错误行、missing_reason、首尾时间/距窗口头尾、窗口前后最近采样、单调时钟间隔与已知 pair 数、sequence 已知样本/pair/内部缺口/倒序。已知 pair 为0时缺口和倒序均 null，不能把未知填0；内部 sequence 缺口不能量化窗口外缺失。输出头/尾完整布尔值仅描述记录布局，不颁发业务或验收结论。

供协调岗部署后执行：

```sh
python3 /EXPLICIT/DEPLOYED/resource_window.py \
  --raw /root/t44-r9/resource-mirror-r28p7-01/app-raw.jsonl \
  --sha256 2662a505f4034f63ae50f836d0c239cff1f2e018431cf2869af4a496ecbdd283 \
  --begin 2026-10-28T06:33:02.088909+00:00 \
  --end 2026-10-28T06:33:23.979649+00:00
```

## 实际验证与限制

手算合成 CLI 检查最终4个 unittest 方法通过，覆盖已知 CPU 50/150/200/400 的 p50=150、P95=400，独立 RSS88/cgroup999 maxima、窗口边界/缺口/错误行、缺sequence保留null、scheduler全null、错误SHA/末级符号链接/无换行截尾/零时窗拒绝，以及原文件字节/mtime不变。用例不读取或复用采样器实现，不构成生产负载或独立验收。

首次 `python3 -m ruff` 因无模块失败；后以仓库锁定的 `uvx --from ruff==0.17.2` 执行，初次 lint 6 条失败（import顺序、未用sys、三处zip strict、lambda赋值）已修正，最终 check 与 format check 均通过。原失败摘录与最终原始命令输出均保留在本目录。本岗没有重跑产品全套CI、MySQL、云负载、正式验收，也没有推定CPU或DB是延迟根因。

首次主工作树 `rg --files` 因未排除未跟踪tmp意外显示了792私有文件的路径名称，未打开或读取其内容；后续查找仅用独立工作树的Git受控清单、责任目录与明确白名单。没有访问云UI、独立测试工作日志/用例/讨论，未向独立岗发送开发信息。

真实 P16 结果与资源窗口尚待总协调发布。当前脚本和 P7 读数可以独立审阅/执行，不隐含未来轮次授权。
