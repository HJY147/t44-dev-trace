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
