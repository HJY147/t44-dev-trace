# 最小原版import helper（离线已verify，尚未APP import）

三个Python文件逐字来自构建ref `e523bf082a95f3af70697bcf4d3a00a4cfddde8e`，约61.6KB，仅标准库。`final-image-bundle.py`的verify/import/prove-loaded只需要同目录image-bundle.py及image-proof.py；后两者SHA已由原适配器内嵌校验。无factory/v4/GEN/定时关机依赖。SHA256SUMS及MANIFEST.PUBLIC.json给原bytes/SHA。

原final文件内保留历史build/derive等函数以保持原字节，**本包入口只准verify、import、prove-loaded**，不得调用build/derive/verify-cache或image-bundle.py的build/load/其它入口；未复制derive依赖，更不能临时补齐或设置stop_utc。搬运此完整ops目录，不必搬整棵旧工具树。

## APP手工入口（尚未执行，先由root核现场）

PACKAGE为已下载候选包的APP完整绝对路径，NEW_IMPORT_RECEIPT为本轮全新/root/...路径且文件不存在。先核本目录SHA并核现场七角色资源/原数据卷/无发压/排他，当前root准入不能用此README替代。不能把本机private目录名当APP已存在路径。

```sh
cd "$OPS"
sha256sum -c SHA256SUMS
python3 -B final-image-bundle.py verify --package "$PACKAGE" --manifest-sha256 414e3069bddc03adedea3671cb5de7c9382f46f9f44bb77799c5cc7112856bd7
python3 -B final-image-bundle.py import --package "$PACKAGE" --manifest-sha256 414e3069bddc03adedea3671cb5de7c9382f46f9f44bb77799c5cc7112856bd7 --receipt "$NEW_IMPORT_RECEIPT"
```

import要求APP root、Linux amd64、全新输出receipt、新镜像alias；它load两镜像、核原save archive层/config证明及实际非root完整runtime文件，不启动业务服务/不碰数据卷。已有alias时原入口拒绝，不能强制覆盖。若此前已实际load但缺本轮观测，root先确认现场事实再用prove-loaded生成**另一个全新**receipt（同参数，将import改为prove-loaded）；它不load，仅验证已加载内容，不得把旧receipt重命名充当新导入。

producer同时写`$NEW_IMPORT_RECEIPT.observation.PUBLIC.json`，原receipt必须uid0/mode0600。后续backend/maintenance必传该原始sidecar，auth loaded_ref.original_path用APP真实canonical receipt路径，observed_at采用producer真实值；不填模板成功、不以本机复制路径替代。生成receipt不等于应用已替换/发压准入，应用overlay更新仍按独立已审replacement plan执行，config/env/overlay漂移须重plan。

## 本地证据

同一最小目录运行verify exit0，输出VERIFIED_NOT_LOADED；完整125MB镜像包和source/runtime文件仍在原private构建目录，本ops不重复归档。未运行Docker/import/prove-loaded，也未访问云或设置任何VMstop。部署observer7项自测与独立测试工具22+8项分开，不互算。
