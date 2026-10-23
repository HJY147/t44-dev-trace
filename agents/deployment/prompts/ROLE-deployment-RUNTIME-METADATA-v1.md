# ROLE-deployment-RUNTIME-METADATA-v1

本岗为本条实际派工设定归档ID，不称用户修订版本。

## 实际总协调派工原文

恢复原deployment中性托管环境职责，另隔离worktree/分支 codex/deployment-runtime-metadata，从root最新9fb24f1（git rev-parse确认完整）开始；不触deployment-native worktree/application.py。独立岗请求只读同次runner/容器资源元数据给正式性能报告。root已先写specs/changes/neutral-resource-metadata-rfc.md（9fb24f1），请读后实施快速中性能力。新增control.py runtime-metadata：只读当前Compose白名单六服务与runner，单JSON，缺必需观察非零/结构化incomplete，不猜默认。记录host CPU/总可见内存/cgroup limit、各实际docker HostConfig CPUquota/period/NanoCpus/memory/swap/cpuset/pidslimit，0/null不等于无限硬件；实际API supervisor配置workers+spawn_main进程计数（仅数量不输出argv）；固定SELECT @@max_connections（可用audit()返回TSV）；Nginx -T只投影实际worker_processes/worker_connections/upstreamkeepalive/proxyconnect/read/sendtimeout，不保存整个config；Docker daemon transport是否本地unix，明确发压进程在runner、服务同daemon容器（无法确认别推定物理同机）。禁止读Config.Env/完整dockerinspect/私密业务行/任意命令/任意SQL；先从compose ps -q service取得64hexID，inspect用字段白名单模板并核对project/service标签。固定背景scheduler60s/consumer/healthprobe活动如实说明，无持续抓包不能说无其他流量。可独立metadata.py模块，run.py context只宣告新只读control能力，不自动collect以免拖/打断旧harness，未改原7命令/产品/SUT/资源/性能阈值。既有953增加少量真实边界合成核验（ID/project拒绝、字段投影无secret、失败unknown非0），不新建tmp编号；CI configRuff针对变更。无需实际Docker本地没有，不在未知数据上模拟实际runner结论。要尽快给独立岗精确实现commit，供原正式入口前后调用，当前3组正式尚未跑。
并注意rootcf685d7已修compose stderr/stdout分离和严格init-userIDJSON（63合成green），不要丢此改动。MySQL --batch成功零行允许全空stdout已root常量SELECT实际验证并README补充9fb，独立driver自行适配不需你写业务case。
记录真实prompt/日志/模块报告/handoff、工具测试原件、commit push/Issue7真实具体交流读回。封档后结束释放。不要读取任何tmp/independent或私密报告引用。小问题自主解决，不等人确认。

## 对应产物

仅deployment/acceptance/metadata.py、control只读命令/context声明、README与既有953能力边界及本岗记录。无产品/native/门禁/资源/性能阈值修改，无独立材料读取或通信。
