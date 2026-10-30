恢复既有P09七容器（用户执行；本地spy通过，未连云）

同目录放 `resume_existing_p09.py` 与 `P09-existing-containers.PUBLIC.json`。expected文件来自root指定的P09实际PUBLIC observation，绑定原七个完整容器ID、project、role、actual image ID、user和全部已观察资源值；不使用旧controller/GEN，不重放任何过期时钟。Docker start原ID复用原容器配置/卷，不能变更worker数、CPU池或image；工具没有recreate/build/pull/seed操作。

1. 用户开机并具备实际SSH后，在APP恢复原基础服务：

```sh
python3 /root/t44-final-20261029/manual-handoff/resume_existing_p09.py infra
```

只start原mysql/rabbitmq，等待它们原Docker healthcheck healthy；然后start原api并等原health，再start原web/tls-gateway。等待是相对实际健康检查、默认最多180秒，不设S或人工固定启动时间。web/TLS无service token依赖。若consumer/scheduler意外已运行，或旧P09 launcher仍active/未知，先拒绝并交root处理，不擅自stop/restart。七ID不齐/多出同owner容器/owner、image或资源不同均在任何start前拒绝。其他project不被start或停止。

2. 在基础服务实际ready后，root串接后端作者提供的【真实service重签+四会话刷新+原scheduler-secrets目录中token文件刷新】helper；必须按其真实CLI成功退出和PUBLIC证据核对。该步骤不由本工具猜测、实现或读取token。本工具无旧service/generation重放。consumer本身依赖DB/MQ，不依赖scheduler service token；为保持中性准备顺序，此时同样暂不启动。
3. 后端helper真实成功、原token文件已更新后，用户再执行：

```sh
python3 /root/t44-final-20261029/manual-handoff/resume_existing_p09.py workers --service-and-scheduler-token-refreshed
```

仅start原consumer/scheduler并等原health。该flag只是操作者对前置步骤完成的明确确认，不是本工具证明凭证有效，不替代后端helper PUBLIC回执或独立QA批准；root须串接真实helper后再给此命令。全七已运行时不restart任何容器。可用同工具 `observe` 输出只读当前身份/资源/健康，不读Env/Cmd/密钥、不查询业务SQL。

输入原观察SHA在expected文件内；后端三角色实际容器image ID为 `sha256:8e7fed199fb103a9946a14149a7f248efac0fb8655c4ed30b9167b8455ef26a3`，应与实际container Image字段比，不能拿source90b的config digest `47c338...`替代这个历史观测值。原卷使用由原容器ID的既有配置保持，本观察原件没有volume baselines，本工具不冒称已核盘上volume内容。

`python3 -B tmp/748_manual_transport/test_resume_existing_p09.py` 已执行真实函数配CLI spy：mysql→rabbitmq→api→web→TLS→consumer→scheduler顺序、无refresh确认拒worker、错owner/image/id/resources均零start、重复操作不restart。没有实际Docker/systemd/SSH/云/PRIVATE读。远程旧容器、健康、真实token与完整资源仍需用户现场核对，不能据spy声称已恢复或压测通过。

service真重签后的实际token轮换CLI已补齐（APP root本机）：

```sh
python3 /root/t44-final-20261029/manual-handoff/rotate_scheduler_token.py --material /实际/新backend-output/material.PUBLIC.json --backup-dir /root/t44-final-20261029/manual-UNIQUE-scheduler-backup
```

先核backend成功status及 `material_process_exit_proof.process_exit_proven=true`；核其同目录 `service-cli.original.private.json` 原SHA。只inspect精确原scheduler的身份和Mounts，确认原 `P09/campaign/p/scheduler-secrets` 是目录只读bind到 `/run/t44-secrets`（不是单文件bind，没有覆盖子mount）。旧token备份至新root-owned0700目录/0600文件；新原CLI字节写同一挂载目录临时0600文件、保留旧token UID/GID，文件fsync、原子replace、目录fsync并读回SHA。不会重启scanner、不会制造业务事件，不修改backend原material的 `scheduler_token_refreshed=false`；新增rotation receipt单列真实完成范围。全部私有字节和备份只留APP，不复制到Mac/stdout。

该命令成功后才给用户上面的workers确认命令。worker起来后，仍应由后端原中性观测核实际持久scanner的HTTP结果/错误与新会话主体；SHA相同、Docker running/healthy只能证明文件或进程状态，不能证明实际扫描HTTP成功。不要为“验证”手动创建升级事件、另开scanner或重放一次业务写入。读取失败应保留本机备份和中性错误并交责任岗，不伪造新expiry或自动重启。

轮换本地验证：`python3 -B tmp/748_manual_transport/test_rotate_scheduler_token.py`。真实临时文件写入/fsync/原子replace/读回、0600、旧字节备份及无临时残留通过；4个负例（exit proof false、原CLI SHA错误、scheduler owner错误、单文件bind）都在替换/备份创建前拒绝。macOS的root UID/chown和Docker inspect用spy，不能冒充APP真实权限、mount或scanner已验证。
