# Source935 新 P 的两步开发诊断

这不是正式验收。作者/执行者：AI 后端岗位；本岗未执行云端、读取实际口令或连接实际
MySQL。代码 C `f811c5c1cc4573ab57db1be35fa1e9ade379d7cf`；产品仍源935零改。

1. 根/部署岗先启动 810 观测 API。该模块只需要原 Settings/engine 与 `T44_DIAG_*`，
   **不读 sessionpacket、账号或任务 ID**。保持原7worker、原TLS、原后台组件与
   21:00 UTC hardstop；只有观测 entry 覆盖。模块 SHA8f0dbec…、网络 SHA dd776e…
   与 b767 既有封包不变。root 已另收到部署岗位的精确 overlay 接口。
2. 根把本次两份 PUBLIC 工具装入新目录，在 app 容器调用准备器（需原 DB 环境和
   本次显式准入），再只将生成的 private session 文件安全交给 load 侧短窗驱动。

PUBLIC 投递：`delivery.f811c5c1.json` 12643字符；`install.f811c5c1.py` 13724字符。
根设置 `T44_DIAG801_INSTALL_DIR` 为**全新绝对目录**并执行 installer，只解压验证
两个已知公源，不启动应用或读取数据库。详见 `delivery-receipt.json` 的长度及 SHA。
不得把目录里的 checks、accounts、session 或私密 runtime 文件塞进公包。

准备器在 app 容器的原 source935 Python3.12 环境执行，两个公源必须同目录。
以下占位符由根在实际容器中填入，不是本岗已执行命令：

```sh
python /opt/diag801/801_prepare.py \
  --accounts <root显式提供的0600三角色JSON> \
  --output-dir <本容器全新绝对输出目录> \
  --url https://172.21.182.245:18445 --ca <容器内原CA只读路径> \
  --host mysql --port 3306 --user <与原DSN逐字相同的非root用户> --slots 400
```

准备器额外环境只有 `T44_DIAG_ALLOW=source935-development-only`、
`T44_DIAG_PRODUCT_SHA=935ab5b93bea788672c2b4a088c79cfeed848954` 与原产品
`DATABASE_URL`、`T44_DATABASE=t44c_r9diag935_p`。不重建 DSN，不改变 TTL/事务/
鉴权/锁。其严格3306、精确新库/host/user检查在 engine 构造前执行；两个产品源
文件指纹是子集验证，完整镜像证明仍由根提供。

账号输入契约（根私下适配现有文件，不把实际内容发给本岗）：顶层只有 manager、
developer、reviewer；每项只有 username、password、user_id。原 CLI 已实际建出的
三身份必须是 seed 使用的同一批，ID从输入和真实 users/members 交叉核对，程序不
猜数字。私密文件必须当前执行 UID 所有、普通文件、无 group/other 权限、末级非
symlink。根的 server 文件若未挂到容器，需根自行安全只读传递；代码不搜索凭据。

准备器只读实际 seed marker/40 projects/members/任务/依赖/产能以选择输入，跨40
项目轮转400个原DEVELOPING且其前驱真实已交付的 developer 所有任务；另选400
个不相交且15分钟内窗口级别稳定的提醒任务。原 CLI 对**实际项目ID全集**发服务
令牌；三次真实TLS登录核身份；每slot真实 GET、实际创建提醒、新幂等键验证去重、
实际 contract 校验。输出每20slot的匿名进度，不打印响应正文/密码/令牌/DSN。
全部准备请求不混入后续短窗性能统计。partial failure保留已提交新事件，不删数据。
假如 scheduler 或其他操作者已抢先创建该选中事件，准备器明确失败，由根保留现场
决定重新准备；不能把 `created=false` 冒成新建成功。

输出新目录含 `service.private.json`、`session.private.json`、`status.public.jsonl`。
session只保留实际会话/TTL/版本/路径所需字段，不复制密码或DB凭据。公状态终态
应为 `prepared-not-acceptance`、`diagnostic_valid=true`，且exit0。中途异常只打印
异常类，公状态标记 `partial_business_commits_may_exist`；空/缺失文件不能当成功。

load侧持有同两份公源、原CA与根安全传输的 private session 后，可依次执行：

```sh
python /opt/diag801/801_http.py --packet <最新session私包> --ca <原CA> \
  --output <全新匿名结果JSONL> --updated-packet <全新下一份私包> \
  --clients 1 --cycles 20 --seconds 45
```

后续按根的准入逐次改 clients 为20、40、400；cycles1..20，seconds1..120。每次
必须串行使用前一次 `updated-packet`；旧文件禁止覆盖。先1client取得四路径阶段
基线，再20/40、最后400短窗，不等同400持续600秒，也不改变270ms正式门槛。
同一slot每轮 GET→contract→BLOCK/UNBLOCK→existing-event escalation。变更版本
来自上次真实响应；新幂等key不命中请求重放；existing-event要 `created=false`、
同event且不增task_version，不用JSONstub跳过SQL。

每客户端一个严格CA/主机检查的 HTTPSConnection，复用原连接，server close才下次
重建；reset不重试。`connections_established` 与 `tcp_tls_connect_ns`只记成功的
显式connect调用，失败握手可能未计入该成功计数，不能当全部TLS尝试数。该阶段
transport stub核实现，真实TLS由根首次实际执行证明。与正式冻结发压器连接语义
可能不同，短窗量化不能替代正式结果。样本wall含首连；caller threadCPU非server
CPU；Server-Timing仍有原排除边界；残差不能直接叫网络时间。

结果首行记录clients、UTC barrier、每路径经验分位（含失败样本，不丢失败）、原
status/UUID/response字节、失败类与deadline客户端；次行记录结果writer时长，随后
两文件fsync。所有结果在结束时写出，非实时证据写盘压力复刻；已知会话不确定时
`resumable=false`/exit1，下轮拒此包。已有真实提交但响应断连的测试已证明该保护；
必须由根在所有线程停止后另核真实HTTP状态，不能盲重试、猜version或沿旧包续跑。
deadline只阻止发起后续请求；每个已发请求最多原15秒timeout，根必须保留独立
容器/服务hardstop。短窗没有总通过/资源释放保证；真实退出、文件、stage final、
资源窗口和账单/释放仍归根核对。

本地13目标仅owned transport stub与SQLite原CLI/API。原红为测试错误猜提醒201，
冻结接口实际202，已保留原log/XML并改精确202；不是产品修复或放宽业务断言。


根追加的实际候选核对：第一次加 `--inspect-only --slots 400`，它仍严格验证源/新库/
三身份映射，读取真实数据库后先写 `actual-readonly-candidate-profile`：实际project、
task、dependency数量，合格transition与不交escalation候选数、requested_slots、
sufficient_observed。随后 `readonly-inspection-complete`，不CLI、不登录、不发token、
不做业务写，也不建session文件。普通prepare不足也先写counts再退出且
partial_business_commits_may_exist=false；不足不是业务bug，不修改guards。
可按实际数另建全新输出目录用slots1或40先诊断，不等400。

原seed算法静态给150task/project，前60已交付，其余90按六态循环，所以每项目15个
DEVELOPING共600；依赖算法前驱=min(local,60)-distance，均<60，因而算法生成的
这些前驱已交付。这只是源935算法性质，本岗没有读取实际6000/9000云库；本次
真实400可用性目前NOT_PROVEN，必须以根这次只读profile为准。本地缩样400tasks
只有40个DEVELOPING，测试明确证实inspect400显示不足但不写业务，非声称云库400。

根已通报810实际上云up（仅引用根中性事实，非本岗实跑）：任务t-hz07143a01sddkw，
CID e30c189b34b9ab2155deadef8b5e02779b9457d0f34d8db12c8779a3798b18c2，
host profile /root/t44-r9/diag-profile-935-01，output UID10001；容器输出为
/var/lib/t44-diagnostic，all模式每worker10000，原7worker/原TLS18445/source935。
本岗没有读取该路径或容器/private文件，也不将启动成功叫业务性能通过。

部署岗已直接核对的 host-side 原 admin 接口（仅中性路径，不读env内容）：
phase `/root/t44-r9/campaign-935/p`，base `compose.json`，原 `application.env`，
project `t44-cloud-r9diag935-p`，admin profile `operations`，原 entrypoint
`python -m t44.cli`。运行准备器须显式覆盖 entrypoint 为 `python`；不能把脚本路径
误传给原 CLI，也不需要给admin套API的810 overlay。

CA来源纠正：冻结 binding.json 的 tls **没有 ca_path**，只含 ca_sha256、
server_certificate_sha256、CA_private_key_mounted。部署 prepare 的实际 stdout
receipt `phases.p.ca_path` 给出的公CA路径是
`/root/t44-r9/campaign-935/p/tls/ca.pem`。根应先只读该公CA并验证 SHA256 等于冻结
`binding.tls.ca_sha256`；可另存新外置CA receipt，不修改原binding，不杜撰tls.ca_path。
不得挂载整个tls目录或CA私钥。

账号适配只由根私下执行：先确定原
`/root/t44-r9/campaign-935/p/fixture-bootstrap-01/accounts.private.json` 的真实层级，
将各身份的实际 username/password/已确认user_id复制到本工具上述三role形状的新
0600文件；顶层或叶键必须精确，不在聊天/控制台打印值，不猜源JSON键。
示例新文件名 `/root/t44-r9/diag801-private-01/accounts.role-map.private.json` 是根将
创建的路径，不是本岗观察到的既有文件。owner为执行admin的root，父目录0700。

根先公源installer生成全新 `/root/t44-r9/diag801-code-f811`，再创建全新输出父目录
`/root/t44-r9/diag801-private-01/outputs`（0700）。下面是精确原base admin命令布局；
仅 `<原DSN的非root username>` 由根私下从原 Settings/DSN读出，不猜、不打印凭据。
shell执行前应清除**继承的** `DOCKER_`/`COMPOSE_`/`T44_`/`MYSQL_`/`RABBITMQ_`
前缀环境，保留原 PATH/HOME，显式命令旗标和容器的原env-file配置仍保留。可以在
根的外层Python使用过滤后的env调用subprocess，不打印env；不得清除或重写原env文件。

```sh
docker --context default compose \
  --env-file /root/t44-r9/campaign-935/p/application.env \
  --file /root/t44-r9/campaign-935/p/compose.json \
  --project-name t44-cloud-r9diag935-p --profile operations \
  run --rm --no-deps -T --user 0:0 --entrypoint python \
  --volume /root/t44-r9/diag801-code-f811:/opt/diag801:ro \
  --volume /root/t44-r9/diag801-private-01/accounts.role-map.private.json:/run/diag801/accounts.private.json:ro \
  --volume /root/t44-r9/campaign-935/p/tls/ca.pem:/run/diag801/ca.pem:ro \
  --volume /root/t44-r9/diag801-private-01/outputs:/diag-output:rw \
  --env T44_DIAG_ALLOW=source935-development-only \
  --env T44_DIAG_PRODUCT_SHA=935ab5b93bea788672c2b4a088c79cfeed848954 \
  admin /opt/diag801/801_prepare.py \
  --accounts /run/diag801/accounts.private.json \
  --output-dir /diag-output/inspect-01 \
  --url https://172.21.182.245:18445 --ca /run/diag801/ca.pem \
  --host mysql --port 3306 --user <原DSN的非root username> \
  --slots 400 --inspect-only
```

这是根后续实际执行的模板，不是本岗已执行命令或声称网络已通。公profile实际数
满足后，普通prepare使用同布局但**移除inspect-only且换全新output-dir**，slots先
1或40以快速首诊；只有根实际profile证400足够后再400。根需要复制host的
`outputs/<prepared>/session.private.json` 至load的0600新文件，或只挂这一个新文件。
driver无需DB/原accounts密码，不能把整个private输出目录或service token推到公开Git。
