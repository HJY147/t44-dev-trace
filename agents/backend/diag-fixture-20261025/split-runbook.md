# S1/S2：新 P 实际准备流程

仅开发诊断。C `0edb4ceeff2f7afbe42a62d8eef983a33fd1f44f`；旧 f811、实际失败与原
prepare/http不改。根读凭据/执行云命令，本岗只交工具。原API、DB、770d网络、
7workers、采样all/每worker10000、TLS18445及21:00 UTC hardstop保持。

根公布的真实 t-hz07144bus7oge8：候选观察40projects/6000tasks/9000deps、变更600、
不交提醒2080、requested400/sufficienttrue；普通prepare14:34:44Z OSError，可能已
提交服务账户/审计，未重跑覆盖。这个OSError根因没有本岗实证：admin只有data
internal网络是一条可证环境限制，CA文件/客户端构造/连接均需分阶段实际核对。

两个PUBLIC包分别安装到**全新**绝对目录：设置 `T44_DIAG801_INSTALL_DIR`，执行
`split-s1-install.py`（17600字符）和 `split-s2-install.py`（11756字符）。只展开
列出的公源，逐文件SHA验证；两包本地owned安装逐字核对，不启动应用或读私包。
S1三源=801_stage1+原801_prepare+原801_http；S2两源=801_stage2+原801_http。
完整hash见split-delivery-receipt.json，不能把整个tmp目录/测试/private复制进云。

根在原app host私下把已有三role accounts另导出 identity-only 0600文件，格式：
manager/developer/reviewer各只有username/user_id，没有password；S1不需要密码。
S2仍使用根已正确适配的三role密码文件，各只有username/password/user_id。文件及
输出当前UID所有、0600、父0700，私包不公开、不打印值，不猜原JSON层级或ID。

S1仍是原data-only admin，没有HTTP、URL或CA参数。下面路径为本轮新建布局示例，
不是本岗读到的既有私件；根创建父目录并装入只读公源后，以原DBenv运行：

```sh
docker --context default compose \
  --env-file /root/t44-r9/campaign-935/p/application.env \
  --file /root/t44-r9/campaign-935/p/compose.json \
  --project-name t44-cloud-r9diag935-p --profile operations \
  run --rm --no-deps -T --user 0:0 --entrypoint python \
  --volume /root/t44-r9/diag801-s1-code:/opt/diag801:ro \
  --volume /root/t44-r9/diag801-split-private/identities.private.json:/run/diag801/identities.private.json:ro \
  --volume /root/t44-r9/diag801-split-private/s1-output-parent:/diag-output:rw \
  --env T44_DIAG_ALLOW=source935-development-only \
  --env T44_DIAG_PRODUCT_SHA=935ab5b93bea788672c2b4a088c79cfeed848954 \
  admin -B /opt/diag801/801_stage1.py \
  --identities /run/diag801/identities.private.json \
  --output-dir /diag-output/candidate-01 \
  --host mysql --port 3306 --user <根由原DSN读取的非root用户名> --slots 400
```

S1先严格源/新schema/host/port/user guard、真实候选/角色/产能/依赖检查。选中800
任务必须无旧escalation事件，全部旧事件行快照做canonical hash（日期原wire，
bytes明确bytes_hex），CLI前后数量和内容hash均一致才成功；只代表这两个观测点，
不称无限时间全局无并发写。若发现原失败已有选中事件，CLI前拒，保留现场交根。
原CLI为实际40IDs发令牌，再读实际session比对摘要/有效期/actor2/scopes/projectIds。
输出candidate.private.json含800完整task_model快照、真实40ids、ruleVersion、三
role身份、完整原service回执并绑定已核scopes/ids、provenance。没有DSN或password。
公终态 `stage1-complete-not-acceptance` /validtrue/exit0给candidate_sha256；任何
部分服务账户/审计可能存在都要保留，失败时不自动重发或覆盖。

S2运行在app host的独立edge-only source-free Python3.12客户端容器。部署岗确认
已有官方alias：
`t44-official-python:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70`，
对应原固定python:3.12-slim-bookworm digest，根已有image proof，不需pull。
edge名从Compose配置推导为`t44-cloud-r9diag935-p_edge`，部署岗未读云daemon；根
必须先只读核实际网络Name及com.docker.compose.project/network标签，不能冒已核：

```sh
docker --context default network inspect t44-cloud-r9diag935-p_edge \
  --format '{{.Name}} {{index .Labels "com.docker.compose.project"}} {{index .Labels "com.docker.compose.network"}}'
```

CA路径来自原prepare实际stdout phases.p.ca_path：
`/root/t44-r9/campaign-935/p/tls/ca.pem`，冻结binding.tls只有ca_sha256等，没有ca_path。
根核公CA SHA等于binding.tls.ca_sha256，绝不挂整个TLS目录或CA私钥。
S2只挂单个候选、单个accounts、单个公CA、两公源和新输出父目录；不挂产品源码、
原envfile、DB凭据、后端镜像或data网络，不跨机传密码。原host父进程DOCKER_/
COMPOSE_/T44_/MYSQL_/RABBITMQ_继承仍由根过滤，保留原PATH/HOME，不打印env。

```sh
docker --context default run --rm --name t44-diag801-s2-01 \
  --network t44-cloud-r9diag935-p_edge --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 0:0 \
  --volume /root/t44-r9/diag801-s2-code:/opt/diag801:ro \
  --volume /root/t44-r9/diag801-split-private/accounts.role-map.private.json:/run/diag801/accounts.private.json:ro \
  --volume /root/t44-r9/diag801-split-private/s1-output-parent/candidate-01/candidate.private.json:/run/diag801/candidate.private.json:ro \
  --volume /root/t44-r9/campaign-935/p/tls/ca.pem:/run/diag801/ca.pem:ro \
  --volume /root/t44-r9/diag801-split-private/s2-output-parent:/diag-output:rw \
  t44-official-python:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 \
  python -B /opt/diag801/801_stage2.py \
  --accounts /run/diag801/accounts.private.json --candidate /run/diag801/candidate.private.json \
  --candidate-sha256 <S1公终态给出的完整SHA> \
  --ca /run/diag801/ca.pem --ca-sha256 <原binding.tls.ca_sha256> \
  --url https://172.21.182.245:18445 --output-dir /diag-output/session-01
```

S2只stdlib，不读DB环境/源码。验证候选SHA、source/schema、15分钟内、原服务TTL、
40ids/scopes、800slot不交及角色，再记录public_ca_verification /
first_tls_client_configuration /tls_client_configuration_ready /three_real_tls_logins /
snapshot/contract/create/dedup阶段。失败公记录仅phase、异常类、errno、可能提交，
不输出异常正文、body、password、token。真实CA读取/SSLContext/HTTPSConnection
构造已有owned回归，实际网络仍根执行证明；ENETUNREACH不是预定实际结果。
实际三登录，GET与S1**完整**快照逐字数据相等，合法contract，create须新事件及
version+1，新keydedup须false/同event/版本不变。每20slot匿名进度。

成功S2输出session.private.json是原801_http驱动格式，只有它移load；candidate/
accounts/service私包仍留app host。失败空/缺失session绝不使用，已创建事件不回滚/
不重试，根先核真实状态与请求终态。原driver的续包/不确定提交禁续跑机制不变。
候选过15分钟需根按现场状态新准备，不能用改时钟/篡改时间绕过。
这里的S2是顺序准备器，不是400压力；原正式400/600/270、0错误与hardstop不变。
