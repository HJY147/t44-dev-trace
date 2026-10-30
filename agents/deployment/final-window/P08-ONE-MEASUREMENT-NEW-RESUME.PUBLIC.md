# P08：本次恢复，仅一轮正式性能测量

状态：本地准备，未执行云动作。用户最后100元授权由root核实充值、欠费和余额后使用；新campaign内部仍取cap50，不沿用昨晚40/45/50的费用起点或旧deadline。任务只收尾准确90b源码的一轮严格P测量与必要原始证据，不追加F全验收、Word、重构或大备份。失败也输出真实结果，不自动开继任轮。

**费用文件**：从`P08-NEW-RESUME-COST.TEMPLATE.PUBLIC.json`另建实际批准原件，不覆盖旧件。`historical_APP_first_boot_utc`保留历史，只用于审计；计价起点是本次`resume_observed_utc`，两`actual_*_resume_boot_utc`填本次现场kernel boot，`absolute_cost_cutoff_utc`填本次平台保护边界。四项均为实际新UTC，不能填旧时间或预测boot；root完成实际核验才置`root_approved=true`并取rawSHA。cap50工具按`(outer−本次observed)×15.5765/小时≤47`验预算，另留3元；旧单价须重新核对，不符就不启动。首次freeze必须距新outer至少35分钟。平台侧定时经济停机/保盘保护先建立并回查，再恢复；guest shutdown不代表计算停费。

**开机前能完成的先做**：源码90b、六件工件与source346 profile、同源18生产件、QA公开准入/原ENTRY和S+1脚本SHA、single-attempt授权流程、本地结果接收目录。恢复后立即核真实双机boot/时钟/网络池/资源/Python身份、QA安装与旧actor单位状态；这些PUBLIC元数据提前收齐。P08固定保留S=T0+10、E+23、G+25、C+30、13分钟总测量、400客户端、60秒预热、600秒稳态及全部原门禁。

**APP最小命令**（下列均由root在上述条件成立后派发；本岗未运行）：

```sh
python3 -B P08-FRESH-PREPARE-v2.PUBLIC.py --p07-launcher-sha256 ACTUAL_VALID_P07_COPYFIX_SHA --approved-budget-cny 50
systemd-run --unit=t44-final-p08-continuous --property=Type=exec --property=UMask=0077 --property=RuntimeMaxSec=2400 --collect python3 -B /root/t44-final-20261029/ops01/deployment/cloud-reuse/P08-CONTINUOUS-fast10-cap50.PUBLIC.py --load-ready NEW_FRESH_LOAD_READY --load-ready-sha256 RAW_SHA --cost-approval NEW_CURRENT_RESUME_COST --cost-approval-sha256 RAW_SHA
```

旧P07 actor unit须先由root确切停止；新launcher还会拒活动`t44-final-p07*`服务并核旧P07所属容器停止。原P07文件/旧晚门拒绝保留。若P08目录已存在，停止自动方案，先核实际状态，不能删目录重跑。

**避开晚启动**：idle立即传新binding/CA/import；S−290附近生成fresh packet后马上原790传输→原ENTRY `prepare`→独立QA审新target/新grant。不得等到S前最后20秒才收身份元数据。fresh LOAD准入仍≤120秒；HTTP准备须在原packet cutoff=S−150之前完成，packet执行年龄仍≤300秒。S−30前必须完成所有准入与root审定，否则不arm、不晚启动。

```sh
python3 -B P08-SPLUS1-EXEC.PUBLIC.py describe --entry ORIGINAL_ENTRY --entry-sha256 SHA --workspace QA_WORKSPACE --grant-file NEW_ALLOW_TRUE_GRANT --grant-sha256 SHA --run-id r30finalp08
systemd-run --unit=qa753-p08-start-once --on-calendar="ACTUAL_S_PLUS_1_UTC" --timer-property=AccuracySec=1s --timer-property=RandomizedDelaySec=0 --property=Type=exec --collect python3 -B P08-SPLUS1-EXEC.PUBLIC.py execute --entry ORIGINAL_ENTRY --entry-sha256 SHA --workspace QA_WORKSPACE --grant-file NEW_ALLOW_TRUE_GRANT --grant-sha256 SHA --run-id r30finalp08
```

`describe`不arm、不发请求；`execute`只在真实S+1≤now<S+20调用原ENTRY，不重试/不retime。定时器、权限与完整云链尚未实际演练通过。结束立即取独立QA原结果/退出状态/请求和资源证据，区分运行完成与达标；不要由exit0推断400并发、600秒、270ms或1000次/分钟通过。root按已验证的平台保护收尾计算资源，公开实际收费与停止状态。
