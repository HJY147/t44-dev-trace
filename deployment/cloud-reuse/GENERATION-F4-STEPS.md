# 新f4正式入口generation：root执行步骤

工具 generation-f4.py 27109B/SHA9c1abe24da6fc775976505af84dd5172c0e6484d890f77179c5e9bc7df886cf4。14本地guard0.03s/Ruff绿；首个guard误写client_temp_path，已按nginx真实client_body_temp_path修正，首失败XML保留。尚无新generation云运行。

不改旧770d/56d78/546e、env/controller/timer或VM。root填真实新image binding/manifest SHA：

```sh
python3 /root/t44-r9/generation-f4.py prepare \
  --factory /root/t44-r9/campaign-935/p/controller.py \
  --upgrade-binding /root/t44-r9/upgrade-f4-v2-build-01/upgrade-binding.json \
  --upgrade-binding-sha256 ACTUAL_DERIVED_BINDING_SHA \
  --source-package /root/t44-r9/upgrade-f4-v2-source-01 \
  --source-manifest-sha256 ACTUAL_LINUX_SOURCE_MANIFEST_SHA \
  --original-proof /root/t44-r9/proof-v2-01/proof.jsonl \
  --image-proof /root/t44-r9/image-proof.py \
  --output /root/t44-r9/campaign-f4-01 --run-id r10f4gen01 \
  --app-ip ROOT_PRIVATE_APP_IP \
  --f-tls-port 19443 --f-http-port 18180 --p-tls-port 19445 --p-http-port 18181 \
  --p-workers 7 --stop-utc 2026-10-25T21:00:00Z
```

先完整OCI证明及临时readonly/nonroot/networknone容器实际全53项核（含lock/pyproject），后才生成新F/P namespace/账号/CA；没有业务模块import、migrate或seed。原web935以原标签及同字节前端来源记录。4个新端口占用则拒，不碰旧13306。原entry t44.api:app，F4/P7无810。每phase输出独立bindingSHA/CApath/hash/project/database/端口。复制自己的controller+固定daaf factory，双代码SHA随binding冻结；timer ExecStart带bindingSHA。所有工作负载≤21Z，启动留至少600秒。内存limits非预留，同时新旧phase存在时不得宣称cap总和小于物理内存，root按实际阶段控制并采样。

每phase依次执行（F换独立路径/SHA）：

```sh
python3 /root/t44-r9/campaign-f4-01/p/controller.py arm --phase-dir /root/t44-r9/campaign-f4-01/p --binding-sha256 NEW_P_BINDING_SHA
python3 /root/t44-r9/campaign-f4-01/p/controller.py config --phase-dir /root/t44-r9/campaign-f4-01/p --binding-sha256 NEW_P_BINDING_SHA
python3 /root/t44-r9/campaign-f4-01/p/controller.py infra --phase-dir /root/t44-r9/campaign-f4-01/p --binding-sha256 NEW_P_BINDING_SHA
python3 /root/t44-r9/campaign-f4-01/p/controller.py migrate --phase-dir /root/t44-r9/campaign-f4-01/p --binding-sha256 NEW_P_BINDING_SHA --database t44c_r10f4gen01_p
```

root分开运行原admin CLI账户/fixture/seed阶段，不预造ID/session。新P admin模板：

```sh
docker --context default compose --env-file /root/t44-r9/campaign-f4-01/p/application.env \
  --file /root/t44-r9/campaign-f4-01/p/compose.json --project-name t44-cloud-r10f4gen01-p \
  --profile operations run --rm --no-deps -T admin ORIGINAL_CLI_ARGS
```

凭据走原CLI私有文件机制，不写命令/公开日志。root确认数据后：

```sh
python3 /root/t44-r9/campaign-f4-01/p/controller.py idle --phase-dir /root/t44-r9/campaign-f4-01/p --binding-sha256 NEW_P_BINDING_SHA
python3 /root/t44-r9/campaign-f4-01/p/controller.py scheduler-token --phase-dir /root/t44-r9/campaign-f4-01/p --binding-sha256 NEW_P_BINDING_SHA --project-id ACTUAL_POSITIVE_PROJECT_ID
python3 /root/t44-r9/campaign-f4-01/p/controller.py scheduler-start --phase-dir /root/t44-r9/campaign-f4-01/p --binding-sha256 NEW_P_BINDING_SHA
```

idle起API/consumer/web、同权限实际nginx-t、TLS后host严格原CA+IP GET/api/v1/projects=401，无Token；五类temp均/tmp。初次启动role缺失/不Running/RestartCount非0，先存真实状态再失败，不能重贴success。scheduler凭据用原credential-admin/service-token真实CLI、实际正ID、原TTL3600s，无通配；start核10001/0600/regularfile/有效期。scheduler-rotate先停已核scheduler再原CLI --rotate，随后另scheduler-start；失败回执保留，不延长租约。scheduler-stop只停精确本role/image。

status/stop同controller，必须显式phase_dir与bindingSHA。status只报告真实角色/重启，不是业务可用性批准；stop只认本project/service＋已证明actual/configID，保卷/库/退出与OOM原件，不猜forcedfalse，不影响旧935或VM。资源collector/mirror另独立seal/收尾/ownedstop，不能在此stop后冒全部资源已回收。
