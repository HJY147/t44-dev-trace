Agent-Role: deployment
Prompt-Ref: ROLE-deployment-RUNTIME-METADATA-v1

已按中性资源RFC实现并push `b3ee0ac2f261b5f453af4a8c0fb5516ba06645d0`，分支 `codex/deployment-runtime-metadata`，精确基点 `9fb24f1f0e173ef37d0cee8b14b080f190ca6d58`。cf685d7的Compose stdout/stderr分离、严格init-user user_id JSON和audit成功零行语义均保留；未改原七命令、native/application.py、产品源、资源或性能阈值。

新增 `control.py runtime-metadata`，无额外参数；使用原context的python/control_cli/control_state，stdout单JSON，`observation_complete=false`非零/缺项null，不猜默认。run.py只宣告 `runtime_metadata` 能力，不自动collect。协议在deployment/acceptance/README.md“同次运行的只读资源快照”。

六服务先Compose ps-q取得唯一64hex ID，再核对project/service标签，仅inspect资源/Running/探针interval白名单，不读Config.Env或完整inspect。观察runner CPU/可见内存/cgroup v2祖先限制、实际HostConfig、API supervisor/配置workers/spawn_main数量（无argv/PID）、固定SELECT @@max_connections、Nginx-T内存字段投影（完整config/stderr不落盘）与daemon transport；不输出endpoint地址。0/null不当无限硬件，unix socket不当物理同机，scheduler60秒基线/consumer/health probes可能有背景活动，不声明无其他流量。

供协调岗核对的调用边界：Linux cgroup v2必需controller不可见则incomplete，不以默认补齐；Nginx-T验证当前配置文件，不单独证明最近reload内存相同；输出只供调用方私密审阅/显式发布。请保留原JSON与真实非零返回，勿将不完整采集改成性能通过或用预估硬件代替观察。

既有953扩充必要ID/project拒绝、字段无secret、固定SQL、缺项unknown非零与只读投影合成守卫，75 passed/0.10s；CI配置Ruff针对改动通过。工具原件在agents/deployment/runtime-metadata-validation，仅开发能力证据，不传独立岗。首次UP022诊断与更正后原件均保留。未运行Docker/GHA或真实runner资源采集，没有性能/独立验收结论；不读取任何独立用例/私密报告，也不与独立岗通信。
