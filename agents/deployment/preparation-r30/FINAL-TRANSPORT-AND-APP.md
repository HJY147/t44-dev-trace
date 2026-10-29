# R30window01官方SAS交付与APP准备

仅交付与本地验证；本岗没有ECS/VM、Docker、SQL、SUT或会话签发操作。root冻结T0=10:00Z、S10:20、D780、E10:33、G10:35、C10:40、最终核10:45，packet cutoff10:17:30Z（18:17:30 CST），不晚于用户19:00 CST目标。安装不是运行授权。

## 直接执行接口

- 免费标准Actions [40853915121](https://github.com/HJY147/t44-dev-trace/actions/runs/40853915121) 实际success；工具提交`3bc139e167e578eca5a2f800bbecb06cf3d195a7`。
- artifact ID **12888875391**，ZIP **211243B**，官方API及完整本地回收SHA均为`c9bb834877ac22dbb7e6307c0ca3cc1f222c3439657848cd6d21cac55757e7fc`，16普通唯一成员逐bytes/SHA与transport manifest一致。
- root用官方302 endpoint取SAS，SAS仅其私有保存，本文件/Git不含链接或凭据。endpoint为 `https://api.github.com/repos/HJY147/t44-dev-trace/actions/artifacts/12888875391/zip`。
- root严格核ZIP后解到APP/LOAD各自`ROOT=/root/t44-r30/r30window01/transport`；APP原已核94MB backend包仍在`/root/t44-r30/r30window01/package`。本交付不替它重新下载或解包。

```bash
python3 /root/t44-r30/r30window01/transport/install-from-local-public-ops.py \
  /root/t44-r30/r30window01/transport/public-ops.tar.gz
```

仅独占`/root/t44-r30/r30window01/ops`，不独占或覆盖已存在ROOT/package；精确核gzip/tar/每项bytes/hash后排他写29成员。APP/LOAD可同条命令，各只执行一次，不自动重试/覆盖旧prefix。

APP随后把artifact内 `launch-APP-prepare.PUBLIC.txt` **完整单条**提交执行，raw1572B、整base64+256=2352；它校验APP runner/profile原SHA，再启动`systemd-run --unit=t44-r30-r30window01-prepare`，RuntimeMaxSec按实际host clock界到G10:35，User=root/UMask0077，外部timeout30。只在T0至packet cutoff内允许启动。

APP runner固定顺序：verify-bundle→import-backend→六角色原cache复核→GEN prepare→**仅P** arm/config/infra/probe-budget/migrate/idle。原公开cache proof只认`/root/t44-r9/proof-v2-01/proof.jsonl`、50297B/SHA30b1ca48f152cae797862319cdda80c0a0b65ed5af32acf4b18ea55d531cc8d0；不符拒绝，不找私件。APP-IP若未明确提供，只读kernel IPv4默认路由prefsrc并要求RFC1918，不发网络包。

不seed、不init、不签会话、不启动scheduler、不启动F。原stdout/stderr全部流式保存到ROOT/run/commands/*.private，0600；每条另保存bytes/SHA与returncode。完成摘要ROOT/run/preparation.PUBLIC.json最多22000B，包含原import receipt/P binding/原probe路径与SHA及实际资源。失败保所有prefix并在已arm时尝试原GEN owned stop；guest G停止timer与root C节省停机分别负责，runner不声称云费停止。

## 精确包与路径

`public-ops.tar.gz`：78319B/SHA`894b4b50b957bde282eda8d7f10bf7d48c68dba28ed56ececcf0195d30c0c2cf`。解压tar327680B/SHA`712d238423105059eb5032c594c74934d77c21dffeba0e179cc7df6d5fff4574`。29成员=7件profile代码+原profile JSON、17件producer payload+原code manifest、wrapper/APP runner、新transport manifest。

- profile JSON：`6d4b7bc4c4f77515da429df9cbf82554a3a0f5d379ef4fd3a638bf04eaf94584`；GEN `ed0493b73a9d9b352ead6713209fcc74ce493048664bb65b3defea436d4e2c58`；resource `311d9d4d380ca62ee04368416901685db0020a2fb307d260fc72c67a07167648`；预算9e、r30-window7ef不改。
- producer最终`3be27131398a049f1a509918e5308f1bda7c8cec`，原manifest `66ab164258803a8a62edfc3dbc713837431ce8b649664ab8de4c5a48a2359606`，全部17件实际Git原blob逐bytes/hash复核，修正cryptographic_transport_proofs后的真实staging/固定argv纯mock smoke通过。
- wrapper：19840B/SHA`8e9d024b7aa38692a633b620a23a27380d155ed7a8725f45c9ee25dac0fe4d9a`；APP runner：SHA`735a33e08a38f9c1a0cae34df170842b83a38738f3349bc4c69cee3122cbcdb6`。
- 安装后路径：`ROOT/ops/profile`、`ROOT/ops/producer`、`ROOT/ops/r30-neutral-admin.py`、`ROOT/ops/r30-app-prepare.py`；profile7与producer17原件未改。
- 官方ZIP另带root已审d4b5ff1e80f17662558779d26e09eddec8ae2ce8的materials.py原16368B/SHA`8db05a89d7805054304900d2a10c05f1f07b906ac8712fc7b8d4561d61421ba6`，以及批准c189b55742e27c1b8c317ae321f4dde73f3854b9的8件qa-opaque原blob。本岗只复制/核SHA，不解释或解密opaque、不读取PRIVATE。

## 真实检查与首次失败

- 最新3be17件实际manifest的wrapper staging/固定argv smoke通过；3个APP runner外部命令seam检查首次通过（十步顺序/全部0600原prefix/≤22KB、idle失败原prefix+owned-stop、错误固定proof不找替代文件）。没有Linux/Docker/SQL/HTTP实际准备结论。
- 官方ZIP完整本地211243B回收及16件manifest核验通过。其原安装器仅映射目标到项目tmp后实际执行，28payload逐hash一致、既有package marker未改；原launcher只替换systemd执行边界，实捕获RuntimeMaxSec=2095/G界参数，没有创建unit。
- 本机匿名GitHub API curl首试SSL connect timeout(28)/0B响应原prefix保留；叫停前单次IPv4检查已返回本地真实下载及29件核验成功，仍不称云网络通过。root选择官方Actions/Azure SAS；之后不再做匿名路线研究。JSON/raw兼容、坏字节拒绝、重复拒覆盖也只本地检查。正式操作使用SAS ZIP内本地文件安装器，不依赖云GitHub通达。
- root实际生成profile首次因相对output报`NEW_CANONICAL_ABSOLUTE_OUTPUT_REQUIRED`，据root回执未写任何件；改绝对后实际生成当前6d4b原件，本岗逐字核7件SHA。此为root报告，不冒本岗亲自执行该失败。
- push自动附带product run40853915084已申请取消；docker-application40853922144首次取消API TLS timeout，后续明确已completed不可取消，不冒主动全产品CI/验收。旧准确0b native CI不改。

## 同一40项目service供scheduler（root显式选择）

GEN不强制另发scheduler独立会话。root/后端核真实40 projectIDs、escalation:write和TTL后，将service阶段产的原CLI `original-service.json`原bytes排他复制到P phase/scheduler-secrets/scheduler-token.json，UID10001/0600，父目录GEN已建UID10001/0700。必须原`access_token/expires_at/session_id`格式，不能用service.json外层/session.token替代；不改原件，不额外签token。

```bash
python3 "$OPS/profile/generation.py" scheduler-start \
  --phase-dir "$PHASE" --binding-sha256 "$BIND_SHA" \
  --budget-receipt "$ORIGINAL_GEN_PROBE" --budget-receipt-sha256 "$PROBE_SHA"
```

它仍要求真实9e admit/timer及至少600秒余量，token canonical regular/UID10001/0600、expires_at带timezone且>now+60。实际scheduler读取access_token32..512字符；scope/40IDs/覆盖E的TTL应由原service readback证明。启动后以真实status/资源证据判断第7角色，不把文件复制当运行成功。

## 原resource-stream现场契约（仅本地核，未运行）

root回报实际P binding `0c50f2d775b4aa9c724ff3cd287fd4cf6b86c88b1806098ac8d668ee091a89e8`、APP准备/原probe实际max384/P64pool5已成。root后要sample G10:35/serve C10:40；原311d helper的validate_deadlines及binding二次检查同时规定serve<=HARDSTOP G且serve>=sample+30s，因此该组合必拒。本岗45秒内如实报root，不擅改311或窗口。原合法CLI可sample10:34:30/serve10:35，仍覆盖S10:20/E10:33，须root选择：

```bash
python3 "$OPS/profile/resource-stream.py" prepare-app \
  --phase-dir /root/t44-r30/r30window01/run/campaign/p \
  --phase-binding-sha256 0c50f2d775b4aa9c724ff3cd287fd4cf6b86c88b1806098ac8d668ee091a89e8 \
  --app-ip "$ACTUAL_APP_IP" --load-ip "$ACTUAL_LOAD_IP" \
  --run-id r30res01 --port 18449 --interval 1 \
  --sample-until 2026-10-29T10:34:30Z --serve-until 2026-10-29T10:35:00Z \
  --output /root/t44-r30/resource-r30window01
python3 "$OPS/profile/resource-stream.py" start \
  --directory /root/t44-r30/resource-r30window01 --binding-sha256 "$ACTUAL_NEW_RESOURCE_BINDING_SHA"
```

原helper prepare-app必须root、cgroupv2、APP IP等原binding且LOAD为不同RFC1918，parent目录owned0700、output全新。required-start/end只prepare-mirror使用，prepare-app不写入此二字段；不能假称S/E已因传flag绑定。start用其真实返回resource binding SHA，动态PID/nonce不预填。此只连续7roles/DB原观察，不创建新业务授权、封装或依赖；sample第一delta null按原语义保留。若root坚持C服务期，须另明确审计新observer horizon，不能直接改当前冻结原件。
