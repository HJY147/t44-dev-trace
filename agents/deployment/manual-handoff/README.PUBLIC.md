ManualV4 传输与执行可行性（仅本地准备，云端未执行）

保持两台节省停机。先把命令和上传材料准备好；若用户决定验证传输，仅先开原LOAD16核的短验证窗口，确认后再由用户决定开APP64核。任何开机、上传、SSH、INSTALL或QA均由用户执行。本交付没有连接云端。

首选：用户在 ECS 实例详情“上传/下载文件”中一次上传原 `MANUAL_TOOL_V4.PUBLIC.tar.gz` 到LOAD新stage目录；这是OOS临时OSS通道，单文件≤500MB，86KB可整包上传，不依赖GitHub，也不要求公网IP或SSH。现场CUA的checkbox/choosefile跨域点击失败只是自动化UI阻点，不能说用户手动整包上传不支持。官方说明：https://help.aliyun.com/zh/ecs/user-guide/upload-and-download-files-on-the-instance-details-page 。

收到实际bootstrap后，在本地生成收件命令（不连接云）：

```sh
python3 agents/deployment/manual-handoff/build_user_transport.py --package /Users/yang/Desktop/nothing/软件开发大作业/tmp/753_fresh_acceptance_90b/PUBLIC/MANUAL_TOOL_V4.PUBLIC.tar.gz --bootstrap ACTUAL_LOAD_BOOTSTRAP.PUBLIC.json --output NEW_LOCAL_DELIVERY_DIR --remote-parts /root/t44-final-20261029/manual-v4-stage-UNIQUE --workspace /root/t44-final-20261029/QA753MANUAL_UNIQUE
```

上传原整包后，用户只需在LOAD云助手执行生成的 `USER_LOAD_RECEIVE_WHOLE.PUBLIC.sh`（≤16KiB）。该命令内嵌原bootstrap字节和SHA，所以无需再上传bootstrap；核整包原SHA→逐PUBLIC manifest SHA→新W安全解包，保存原tar.gz/原bootstrap/receipt。只stage，不运行INSTALL/790/QA，不开密封capsule。若bootstrap超过16KB生成器如实拒绝单条粘贴，改用户上传bootstrap+接收工具原CLI，不能截断。

整包86788B，SHA `0b3d4d6ba68dc1fa27930963b9442b0bf8e2c2ae61d2860233e1754f4dbb61a9`；delivery manifest SHA `676458385bfd64abcba3e4c6c80f4bb773545d28c46061c113670c411df4a27b`。原包13个PUBLIC文件逐SHA验证，tar中的空__pycache__目录不执行。新W已存在拒绝覆盖。

备用：CloudAssistant SendFile API/旧“发送文件”是另一个接口，base64内容≤32KiB（原始文件≤24KiB），不能把这条限制套在上述500MB功能。生成器也准备4个part：24576/24576/24576/13060B，用户上传4份后执行 `USER_LOAD_RECEIVE.PUBLIC.sh` 合并；全包/分片两种收件方式二选一。官方接口限制：https://www.alibabacloud.com/help/en/ecs/developer-reference/api-ecs-2014-05-26-sendfile 。不建议退回多轮大段手工base64粘贴。

SSH可选（目前未证实连通）：旧授权key期限 `20261029190000Z` 已过，必须由用户安装新的有效临时pubkey。之前banner timeout发生在SSH认证前，不是“key过期已导致banner失败”的证据。现场Mac到旧47.99.42.52走utun5/gateway198.18.0.1，系统SOCKS127.0.0.1:7890；它们是父任务提供的已见事实，本任务没有再查网络，也不能保证新开机IP仍相同。ssh不因声明ProxyCommand=none就绕过系统TUN路由。

用户先读取本次LOAD实际公网IP、核主机指纹，并指定已安装且未过期的key路径；可用短命令测试：

```sh
ssh -T -o RequestTTY=no -o ForwardAgent=no -o ClearAllForwardings=yes -o BatchMode=yes -o ConnectTimeout=10 -o ConnectionAttempts=1 -o StrictHostKeyChecking=yes -i "$NEW_KEY_PATH" "root@$ACTUAL_LOAD_IP" 'printf "SSH_AUTHENTICATED_LOAD\n"'
```

该命令只有收到远端输出才能证明完成认证；不能把TCP成功/banner超时/本地key存在称为SSH/SCP连通。known_hosts需事先按真实指纹准备，不能关闭主机校验。SSH/SCP实际通过后可以scp原整包到新stage再运行同一whole收件脚本；未通过就用用户手动OOS整包上传，先不要开APP等待。

执行衔接有明确边界：原ManualV4 README要求opened目录的五件原packet，bootstrap本身不是五件packet。若LOAD原盘已有经过原790恢复的extracted目录，用户可按原README对新W INSTALL和manual prepare（无SUT请求），再提交独立QA新defaultfalse grant，仅独立批准后manual execute一次；本交付不替代该批准。若LOAD没有extracted，只搬bootstrap还不够：旧P05 LOAD driver把旧timeplan.cost_stop传给policy790/five_files，原policy_790.py要求deadline在未来且≤3600秒，five_files也拒过期。不能直接将旧C改新或冒称原790一定可运行。此缝需中性运输责任岗/独立QA发布适用manual的明确方案，本交付不修改90b、QA包或旧时钟。

本地真实验证：`python3 -B tmp/748_manual_transport/test_public_transport.py`。实际将原包切片/base64编解码/逐SHA/解包；在临时目录执行生成的whole和parts收件Python，13件原字节相同；变更part/bootstrap、覆盖W、路径穿越/绝对路径/符号链接负例均拒绝。未执行SSH/SCP、云助手、INSTALL、790或QA，不能声称已远程演练成功。

新增CMS/SCP可选运输见 `CMS-SCP.PUBLIC.md`：以原LOADkey的一日PUBLIC接收cert作标准CMS AES256GCM，原五件从APP密封后仅cipher经过Mac；LOAD本机解封到新opened/inputs五件，不参与旧790/C。已做本地合成完整往返，云端未验证；仍保留原独立QA批准。
