# 保留实例恢复：先提取原观察汇总

本地准备，不是云执行回执。原935/f4 controller和绑定不修改；旧Persistent timer到期可能在开机后触发保卷停旧project，先只读核其状态及receipt，不直接重开旧工作负载。

## APP开机后的最少操作

1. Root核官方实例与云盘、释放时间仍“-”、预算和用户恢复授权。只需先启动原APP，LOAD等新的本地产品验证/部署准备好再开；不释放重买。
2. 在APP官方云助手创建新执行，将 `agents/deployment/resume-20261028/install-and-emit-first.sh` 原文粘贴。3679字节脚本先把压缩helper独占写到新路径，核SHA后输出index0；不改原summary。helper原文7225字节/SHA256 `ce7ed1e96b97eea2f32db2d429c4d60d0e39b2c1b61c428c5041dfa6d4dd5ec0`。
3. index0的JSON给出真实chunks总数。后续每次一个小任务：`python3 /root/t44-r9/observer-summary-export-20261028.py emit --index 1`，依次到chunks-1。每次约≤13KB；不要把所有块拼到一次可能被UI截断的输出里。任何hash/size失败停止并保存原错误；不得改批准SHA去迁就文件。
4. Root在本机私有0700新目录保存每个返回JSON为chunk-0.json等，精确原对象，无删节。执行：

```sh
python3 deployment/cloud-reuse/observer-summary-export.py assemble \
  --chunk /ABSOLUTE_PRIVATE_DIR/chunk-0.json \
  --chunk /ABSOLUTE_PRIVATE_DIR/chunk-1.json \
  --output /ABSOLUTE_PRIVATE_DIR/observer-summary-935.received.json
```

按真实chunks重复`--chunk`。少块/重块/范围/元数据/块SHA/压缩SHA/原文SHA不符、符号链接或输出已存在均拒绝。新文件0600、O_EXCL|O_NOFOLLOW固定FD并fsync；原云summary不写入。原文66110字节/SHA d554caf63e38238ab1b3e75abc2823b670b078d60c84a9097b031c03044e3053。

12项本地guard已通过：真实多块回收、缺块/重块/篡改/offset/manifest拒绝、源SHA/长度、真实symlink拒绝、固定FD不覆盖。首轮2失败来自本岗临时夹具使用macOS非canonical `/var`路径，改为项目内tmp夹具后绿；原失败XML保留。没有更改生产读取/独占保护以通过测试。

原汇总是源935开发诊断观察，不是当前新源、完整600秒性能或根因证明。提取后由总协调/后端按真实阶段和重叠跨度解释，不能相加重复归因。

## 新源和新截止的独立派生profile

旧generator和resource-stream绝对21Z已经过期，不能原样使用。新增`derive-resume-profile.py`只读精确审核的四个旧模板SHA，构造全新派生件；原935/f4不改变。root先明确最终完整源commit和真实未来30分钟至12小时的UTC截止，再在本机运行：

```sh
python3 deployment/cloud-reuse/derive-resume-profile.py derive \
  --repository /Users/yang/Desktop/nothing/软件开发大作业 \
  --source ROOT_FINAL_COMPLETE_40_HEX_COMMIT \
  --stop-utc ROOT_NEW_ABSOLUTE_UTC_Z \
  --output /ABSOLUTE_NEW_PARENT/profile-01
```

输出新builder、generation、resource-stream和五文件receiver以及profile.json/SHA；builder→generator→resource-stream/receiver摘要链、真实Git源文件数量和等字节集合摘要都记录。依赖/REST/DDL/schema.py/前端/支持文件仍与935完整比较，不同就拒绝；不能为了复用镜像删检查。如果本轮改到这些，先交总协调另行设计并重建必要镜像。

本机生成小源制品（纯Git/stdlib，不Docker/不业务导入）：

```sh
python3 deployment/cloud-reuse/derive-resume-profile.py package \
  --repository /Users/yang/Desktop/nothing/软件开发大作业 \
  --profile /ABSOLUTE_NEW_PARENT/profile-01/profile.json \
  --profile-sha256 ACTUAL_PROFILE_SHA \
  --output /ABSOLUTE_NEW_PARENT/package-01
```

只在新目录产出source/原件和source-artifact.zip五文件（完整source.gz/manifest/frozen-equality/Dockerfile/新builder），回执给实际ZIP/manifest/builder摘要。派生receiver仍检查原ZIP全SHA/CRC、五文件allowlist、TAR及新builder SHA；不能拿旧5200 receiver接收新builder，也不能改新builder套旧manifest。

运输方式由root选定并另有实际完整字节核验；本岗未上传/发CI。root把新profile脚本、source小包交APP后，依原BACKEND-UPGRADE和GENERATION步骤，使用**新**receiver→新builder build→新generation prepare/arm/infra/migrate，分别pin真实manifest、derived image binding、phase binding和新截止。新generation的完整源检查取真实文件数量，不固定假53；原entry/nonroot/networknone/TLS CA+IP/新namespace/保卷ownedstop保护仍在。

连续资源步骤使用派生resource-stream.py与**该新generation**绑定，采样和finaltail截止≤新profile停止时间；warmup前启动APP collector及LOAD mirror，先确认真实数值，再跑正式阶段。seal→LOAD确认全尾/wholeSHA→两个observer stop→SUT ownedstop；独立验收自行判coverage/性能，不以运输complete替代数值完整。时间过期或工具SHA变化就新建profile，不改旧已冻结运行目录。

16项profile本地检查包括：原模板精确SHA/前像次数、新窗口拒绝过期/无界/非Z、动态49文件完整检查、nonroot/环境/模式/缺文件拒绝、真实22f Git源53项五文件ZIP及receiver校验、拒覆盖和错误profile SHA。22f只是本岗本地工具验证源，不是本轮最终产品选择。没有新云build/新generation或跨VM采样结果。

## 只读核旧定时器示例

```sh
systemctl list-timers --all --no-pager 't44-cloud-*'
```

随后只对实际列出的旧timer用`systemctl show EXACT_OLD_TIMER --property=Id,ActiveState,SubState,Result,LastTriggerUSec,NextElapseUSecRealtime`及旧phase/status/receipt只读核验。不要disable/delete旧锚或强杀unknown；旧到期任务完成后保留它的实际回执，用新的run-id/namespace建新代际。
