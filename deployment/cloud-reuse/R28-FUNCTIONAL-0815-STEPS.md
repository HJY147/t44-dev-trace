# 新functional窗口08:15Z（只本地交付，root执行）

原P7/P16诊断07:30Z不变。新源仍a12e9e70b963bacafda3242bb6d82e53ee912ff1，原两VM，不重买、不改IAM、不删旧数据。新run-id `r28funcgen01`合法，共12字符；新F项目`t44-cloud-r28funcgen01-f`、数据库`t44c_r28funcgen01_f`。P只prepare不启动，后续只F4worker空库和真实五身份，由root按独立中性准入执行。

## 公共运输

在APP新任务粘贴 `agents/deployment/resume-20261028/functional-install-once.sh` 原文，31595字节，小于32KiB。脚本只含公开代码/元数据，先核整个transport和每个压缩/原文字节SHA、source/08:15/53文件及代码可解析，再独占创建 `/root/t44-r9/functional-20261028-01` 并写3件0600文件/fsync。不改旧目录，目录已存在拒绝，不直接覆盖重试。

| 文件 | 字节 | SHA256 |
| --- | ---: | --- |
| profile.json | 1495 | b940549052f149f616ae5e943cd6f6571d74142c497df8afb9b99f4513e85270 |
| generation.py | 27199 | 2dbdbbb4bcfc6cd4cbecc4c766e05692554439d2b53e8305f47ba82a36e17c33 |
| resource-stream.py | 44079 | 587ec55fcb00a40ea490edc8bc501a7be6559d2b5e6571533b2164ec93215dbd |

transport PUBLIC JSON28111字节/SHA `91e362ad00aafe4ac2b9a681851fdea459599105f7083667cf9926d355e84469`。新profile全套5件本地原件留在functional-profile-0815；此次运输仅profile和两运行helper。builder仍原同源a12的23566字节/SHA `ebc91ce54ee73a418b9df11c3878ae75e348198b64c25060aeff8462de3949d1`，直接只读引用已核sourcechecked包即可，不用重建镜像/替换旧builder或receiver。

## 新环境prepare

root先核真实余窗：至少600秒，建议剩余≥1800秒以留功能准备/后置检查；08:05Z后新controller非stop/status操作将拒绝。旧daemon/07:30锚不改，新namespace与原诊断互不覆盖。APP运行：

```sh
python3 /root/t44-r9/functional-20261028-01/generation.py prepare \
  --factory /root/t44-r9/campaign-935/p/controller.py \
  --upgrade-binding /root/t44-r9/resume-20261028-01/build-01/upgrade-binding.json \
  --upgrade-binding-sha256 31fc1c8a9cd2162656c8cfc9a42e830e228494d1e644f143921bbb718834cbd8 \
  --source-package /root/t44-r9/resume-20261028-01/source-checked-01 \
  --source-manifest-sha256 68f9db715b4a9d33d1cc70c5f7d08a50fcd51c97dfd4276dceba71e93d9ade00 \
  --original-proof /root/t44-r9/proof-v2-01/proof.jsonl --image-proof /root/t44-r9/image-proof.py \
  --output /root/t44-r9/campaign-r28functional-01 --run-id r28funcgen01 \
  --app-ip ROOT_ACTUAL_APP_PRIVATE_IP \
  --f-tls-port 22443 --f-http-port 18480 --p-tls-port 22445 --p-http-port 18481 \
  --p-workers 7 --stop-utc 2026-10-28T08:15:00Z
```

四端口仅本地计划，真实bind-free由原helper检查；冲突保留错误，不杀unknown。prepare本身不启任何F/P。取**f**回执的真实bindingSHA，依次执行该新f/controller.py arm→config→infra→migrate（`--database t44c_r28funcgen01_f`）。每步均显式`--phase-dir /root/t44-r9/campaign-r28functional-01/f --binding-sha256 ROOT_ACTUAL_F_BINDING_SHA`；后续只在真实空库用原CLI建五个不同身份。不要运行790 P7/P16 bootstrap或seed40，也不要把其私包用于F。

root完成身份/独立准入后才idle，原F固定4worker、t44.api:app、无profiling。scheduler真实scope/令牌、资源采集和独立执行分别按中性契约安排，不预填角色已齐、测试通过或CPU/RSS。resource需使用此**08:15派生**helper绑定此新F；不能用07:30版本或旧fd7d controller给新F采集。

收尾resource seal→mirror收全tail/wholeSHA→stop observers→新F controller owned stop，保卷/库/原始记录；原P不启。stop/status过期后仍可按原身份执行，不能给cleanup加未来窗口限制。ECS生命周期和100元预算由root单独控制，本岗不执行。

11项本地保护检查通过：source/窗口/完整SHA链、runid/CLI解析前拦截、三件运输/大小、篡改/错source/错截止/路径穿越/重复/超限拒绝、真实本地独占安装/不覆盖。没有云操作或独立功能执行结论。
