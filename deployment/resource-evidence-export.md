# 18:10后资源证据回收（root执行，本岗未云操作）

先等app v3/load host采样任务真实结束，记录安全完成摘要的file/SHA/bytes/样本/失败/UTC；完成SHA不能用当前活动文件临时hash替代。root中性首样本转述：app resource-aa5399ea993f426b82b678f5812c530f.ndjson始于09:11:13.775549Z；load host-resource-0a687bf0312940979b8097f1800a2850.ndjson始于09:17:47.204093Z。最终SHA/计数尚待18:10，本岗未读raw。helper可先预上传并核源码SHA，不提前执行。

两台分别执行，变量由root从各自**完成摘要**填入；不扫描目录、不下载整个relay852。所有命令均不改C/服务/权限/网络。

```sh
# app：18:10后，APP_COMPLETION_SHA256须为完成摘要64hex
python3 /run/t44-delivery/resource-evidence-export.py --host app \
  --source /run/t44-delivery/resource-aa5399ea993f426b82b678f5812c530f.ndjson "$APP_COMPLETION_SHA256"
```

```sh
# load：18:10后，LOAD_COMPLETION_SHA256须为完成摘要64hex
python3 /run/t44-relay852/resource-evidence-export.py --host load \
  --source /run/t44-relay852/host-resource-0a687bf0312940979b8097f1800a2850.ndjson "$LOAD_COMPLETION_SHA256"
```

若需保留早期本岗v1文件，只能从其既有安全完成摘要逐项再加--source PATH SHA，不能glob找文件。v1四/proc原始口径不追改；按当前五源证据要求缺TCP会标NOT_PROVEN，raw仍原样归档。每机max8文件、单64MiB/总256MiB、压缩128MiB、单JSON行2MiB、执行预算60秒。仅10:10Z后、10:28Z前准入；root-owned0700父目录，输入root-owned0600/regular/nlink1/nofollow、前后元数据稳定+完成SHA匹配；输出新UUID.tar.gz排他0600，不改已有文件，不读852私有/Env/token/key或应用日志。

包只含raw/受控UUID.ndjson与manifest.json；原字节/hash/大小保持。manifest的UTC范围来自可解析完整样本，若有坏行/缺项计数null/NOT_PROVEN，不能当完整范围保证；原raw仍保存。app服务精确7且各stats精确7非空str，app/load proc精确5非空str；errors空不等于数据完整。压缩写入同时算包hash，不回读任何其他文件；失败partial_archive保留，completed=false不得当成功包。

18:10–18:20目标流程（计划不是完成保证）：
1. 两机分别取completed=true的包路径/hash/bytes，使用用户已授权的官方单文件下载功能只下载该包，不能选择整个目录。49,520B旧密文下载/hash一致是root既有通道事实，不保证新大包已下载或大小限制。
2. 本地核包完整SHA256与bytes等于服务器摘要；再用tarfile只读manifest和白名单raw成员，逐项核原SHA/bytes，不extract整个目录、不读取任何私有验收包。下面是本地新中性资源包核验例（先替换三参数）：

```sh
python3 -I - 'LOCAL_RESOURCE_PACKAGE.tar.gz' 'SERVER_ARCHIVE_SHA256' 'SERVER_ARCHIVE_BYTES' <<'CHECK'
import hashlib, json, re, sys, tarfile
from pathlib import Path
p = Path(sys.argv[1]); data = p.read_bytes()
if len(data) != int(sys.argv[3]) or hashlib.sha256(data).hexdigest() != sys.argv[2]:
    raise SystemExit('ARCHIVE_INTEGRITY_FAILED')
with tarfile.open(p, 'r:gz') as archive:
    members = archive.getmembers(); names = [m.name for m in members]
    if len(names) != len(set(names)) or not all(m.isfile() for m in members):
        raise SystemExit('ARCHIVE_MEMBERS_FAILED')
    manifest = json.load(archive.extractfile('manifest.json'))
    if set(names) != {'manifest.json', *(x['member'] for x in manifest['sources'])}:
        raise SystemExit('ARCHIVE_ALLOWLIST_FAILED')
    for source in manifest['sources']:
        if not re.fullmatch(r'raw/(?:host-)?resource-[0-9a-f]{32}\.ndjson', source['member']):
            raise SystemExit('RAW_NAME_FAILED')
        raw = archive.extractfile(source['member']).read(64 * 1024 * 1024 + 1)
        if len(raw) != source['bytes'] or hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise SystemExit('RAW_INTEGRITY_FAILED')
print(json.dumps({'archive_and_all_raw_hashes_verified': True, 'sources': len(manifest['sources'])}))
CHECK
```

3. 保存原下载包、服务器安全摘要、manifest及本地完整核验回执，按app/load分开。资源证据完整性不等于容量/正式压测通过；失败样本/NOT_PROVEN原样报告。
4. 最迟18:25前处理官方通道失败并报告真实缺证，18:30释放前必须实际下载到本地并核hash，不能只保留云路径。不能自动延长负载/租期或启用新外部发布通道。100元为授权预算上限，非实际花100；既定18:10硬停/18:30释放保持。

本地26纯合成guard/内存gzip-tar roundtrip与Ruff/compile通过。初版仅number/time/errors会错误OBSERVED缺proc，root审查指出后已补结构检查，原682c80…反例red保存；本次没有真实资源读取、云执行、浏览器下载、独立私密材料或新test文件。
