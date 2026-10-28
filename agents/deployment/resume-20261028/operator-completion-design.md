# 限定resource ready-race的operator completion

root转交真实APP新resource-r28p16-02的EXACT_OWNED_SYSTEMD_PROCESS_REQUIRED拒绝；原1030 helper/binding和失败原件不改。仅允许该APP目录和未来LOAD resource-mirror-r28p16-02，root唯一云操作者。本岗不读792/private或修改产品，不启动/重启/停止服务。

输入必须为明确目录、binding完整SHA及该目录内failure-hex.json。APP additionally pin root提供的f76269ff…及failure-23c53697…；LOAD允许root后续明确pin新binding/实际failure。只接受ValueError、reason恰为上述ready-race、partial_state_preserved且start-result不存在，其他拒绝。

预检原e5b0324e…controller、binding内固定文件集合SHA、start-plan的unit/path/SHA与严格预期argv；unit必须为对应resource/mirror前缀、/etc/systemd/system字面路径、root/0644且原模板保护/ExecStart完整相同（RuntimeMaxSec保原已冻正整数）。不重算旧timer或修改RuntimeMaxSec。

最多5秒仅等argv匹配：systemctl真实MainPID/active/running/ControlGroup、/proc PID目录owner与Uid四值0、/proc/stat starttick、argv、cgroupv2所属组与cgroup.procs成员均核。首次PID/starttick为锚，任何切换/失踪/非root/错误cgroup立即拒，不能只信active。匹配后两次稳定快照、重新核所有输入未变，再O_EXCL|NOFOLLOW/fsync写原控制器所需start-result，额外明确late=true、not_original_start_success=true及原拒绝/操作者/证明摘要。

随后调用原已核controller status并复核实际PID/starttick/cgroup；失败保留已写late回执，不谎称成功或删除前缀。无法与内核重启完全原子化，故末次原status和再探测是额外门禁，任何晚到变化报告失败。helper只补这一个缺回执，不重新start、不接其他目录或其他错误。

本地5组守卫用公开原controller和真实私有fixture文件/O_EXCL，systemd/proc观察为明确模拟（Mac没有目标Linux服务），覆盖限定正例、其他错误/已有回执、PID切换、UID/argv/cgroup拒绝及拒覆盖。此范围不冒充实际云成功；root实际operator/status回执另列。
