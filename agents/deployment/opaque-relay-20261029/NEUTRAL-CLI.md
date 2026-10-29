# 中性材料单文件私网TLS交接

部署AI准备，尚未云上运行。新工具源5979字节/69行，安装器4318字节；根实际密文size/hash及原seal public_record_sha256必须从真实complete PUBLIC原件取得，不能拿模板当结果。原18447短诊断relay和原13件都不改。

两侧执行 `install-neutral-opaque.PUBLIC.sh`，仅排他安装 `/root/t44-r9/neutral-opaque-r29-01.py`。APP在实际中性seal完成后由有界systemd异步运行：

```sh
python3 -I -B /root/t44-r9/neutral-opaque-r29-01.py serve --bytes ACTUAL_BYTES --sha256 ACTUAL_SHA --binding-sha256 ACTUAL_PHASE_BINDING_SHA --cost-stop-utc 2026-10-29T04:56:19.801Z
```

监听公开LISTENING行/PID后，LOAD单次运行：

```sh
python3 -I -B /root/t44-r9/neutral-opaque-r29-01.py fetch --bytes ACTUAL_BYTES --sha256 ACTUAL_SHA --ca-sha256 ACTUAL_CA_SHA --public-record-sha256 ACTUAL_SEAL_PUBLIC_RECORD_SHA --cost-stop-utc 2026-10-29T04:56:19.801Z
```

APP只读固定 `/root/t44-r9/neutral-fixture-r29-01/output/sealed-neutral/transfer.public.jsonl`，O_NOFOLLOW/稳定关闭的单链接常规文件/≤4MiB/精确size/SHA，整包冻结内存；原phase绑定和原叶证书SHA必须符合，私钥仅原leaf用于TLS。固定APP172.21.182.245:18448，TLS握手前精确检查LOAD172.21.182.244，唯一GET /opaque，仅一次完整传送尝试，绝对成本窗口后退出，无新nonce/credential/SG/IAM变更。

LOAD只以原CA/IP严格验证请求一次；精确response headers、body cap/size/SHA后在新 `neutral-opaque-load-r29-01/transfer.OPAQUE.jsonl` 排他写密文。核固定新29原transfer helper SHA，调用原open和本机现有LOAD私钥，输出到 `neutral-opaque-load-r29-01/opened-neutral`。stdout仅完成标志、原public receipt SHA及路径；工具不读解密结果，后续仅测试岗读取。没有SUT HTTP或正式压力授权。失败保留prefix，不重试、不新造会话。

本地仅Python3.10语法解析、shell语法、3个file guard真实检查（排他覆盖/尺寸/软链接拒绝），未新跑TLS/原open/云。加载模块没有执行main。实际传输/解密和截止/保盘停机必须由根记录；原receipt成功不代表性能达标。
