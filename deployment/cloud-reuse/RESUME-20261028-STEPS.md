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

## 新代际待补

旧generator和resource-stream绝对21Z已经过期，不能原样使用。新派生profile将显式pin最终完整Git源、新≤12小时UTC窗口、真实文件数量及builder→generator→resource-stream摘要链；依赖/DDL/REST/前端等同字节保护继续保留。输出必须用新目录/新namespace，不改旧935/f4绑定。此项目前仍在本地实现，不表示可以启动新SUT。
